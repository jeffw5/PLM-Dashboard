"""
World Model graph-propagation engine: Monte Carlo impulse-response
simulation over the causal graph (causal_graph.py), given a Decision's
origin shock(s) (decisions.py).

This is NOT the original MonteCarloEngine's quarterly state_transition_fn
pattern reused as-is -- graph propagation is a structurally different
problem (walking an uncertain, partially-cyclic graph an unknown number
of hops) and gets its own, purpose-built engine. It reuses the same
*conventions* as the rest of the Assembly Decision Engine: a derived,
stable seed per (decision, run) for reproducibility; NormalBelief.sample()
for the epistemic layer; and an AuditTrail span around the run.

Mechanics
---------
A decision's origin shock is injected, in NORMALIZED units (native delta
/ typical_move -- see ontology.StateVariable.typical_move), onto its
origin (actor, var) node as "hop 0." At each subsequent hop, every node
active in the previous hop fires its outgoing causal edges: each edge's
NormalBelief is sampled once per Monte Carlo draw (so the coefficient
itself carries uncertainty, not just a point estimate), and
coefficient * source_normalized_delta is added to the target node's
delta for this hop. A DAMPING_FACTOR < 1 is applied to each hop's newly
produced deltas before they become the next hop's frontier -- an explicit
MODELING CHOICE (not an empirical finding), standing in for the real-world
tendency of causal influence to attenuate with distance/time, and needed
because the graph contains cycles (e.g. energy price -> inflation ->
approval -> ... -> energy price): without damping, a signal could in
principle recirculate and grow without bound.

Because only the frontier actually produced by the previous hop is carried
forward (never the cumulative running total), the walk is bounded by
max_hops by construction -- there is no infinite-loop risk even though
the underlying graph has cycles.

The engine returns, per reached (actor, var), the full N-draw sample of
total accumulated effect (native units) plus a hop-by-hop contribution
log for explainability (which edges, in what order, produced how much of
the effect at each downstream node).
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

import numpy as np

from core.audit import AuditTrail

from .causal_graph import CausalEdge
from .decisions import Decision
from .ontology import STATE_VAR_BY_KEY

DAMPING_FACTOR = 0.65       # illustrative per-hop attenuation -- see module docstring
ACTIVATION_EPSILON = 0.01   # prune frontier branches below this |mean normalized delta|
DEFAULT_MAX_HOPS = 4


@dataclass
class HopContribution:
    hop: int
    edge_id: str
    source_actor: str
    source_var: str
    target_actor: str
    target_var: str
    mean_contribution_normalized: float
    lag: int
    rationale: str

    def to_dict(self) -> Dict:
        return {"hop": self.hop, "edge_id": self.edge_id,
                "source": f"{self.source_actor}:{self.source_var}",
                "target": f"{self.target_actor}:{self.target_var}",
                "mean_contribution_normalized": round(self.mean_contribution_normalized, 5),
                "lag": self.lag, "rationale": self.rationale}


@dataclass
class NodeImpact:
    actor: str
    var: str
    samples_native: np.ndarray    # shape (n,): total accumulated effect, native units
    first_hop_reached: int

    @property
    def mean(self) -> float: return float(np.mean(self.samples_native))

    @property
    def std(self) -> float: return float(np.std(self.samples_native))

    def percentile(self, p: float) -> float: return float(np.percentile(self.samples_native, p))

    @property
    def mean_normalized(self) -> float:
        tm = STATE_VAR_BY_KEY[self.var].typical_move
        return self.mean / tm if tm else 0.0

    def to_dict(self) -> Dict:
        var_def = STATE_VAR_BY_KEY[self.var]
        return {
            "actor": self.actor, "var": self.var, "var_label": var_def.label, "unit": var_def.unit,
            "higher_is_better": var_def.higher_is_better,
            "mean": round(self.mean, 4), "std": round(self.std, 4),
            "p5": round(self.percentile(5), 4), "p95": round(self.percentile(95), 4),
            "mean_normalized_moves": round(self.mean_normalized, 4),
            "first_hop_reached": self.first_hop_reached,
        }


@dataclass
class PropagationResult:
    decision_id: str
    n_simulations: int
    seed: int
    impacts: Dict[Tuple[str, str], NodeImpact]
    contribution_log: List[HopContribution]

    def ranked_impacts(self, exclude_origin: bool = True) -> List[NodeImpact]:
        items = list(self.impacts.values())
        if exclude_origin:
            items = [i for i in items if i.first_hop_reached > 0]
        return sorted(items, key=lambda i: abs(i.mean_normalized), reverse=True)

    def to_dict(self) -> Dict:
        return {
            "decision_id": self.decision_id, "n_simulations": self.n_simulations, "seed": self.seed,
            "impacts": [i.to_dict() for _, i in sorted(self.impacts.items())],
            "contribution_log": [c.to_dict() for c in self.contribution_log],
        }


def _derived_seed(decision_id: str, base_seed: int) -> int:
    h = hashlib.sha256(f"worldmodel:{decision_id}".encode("utf-8")).hexdigest()
    return (base_seed + int(h[:8], 16) % 10_000) % (2 ** 31 - 1)


class _NullCtx:
    def __enter__(self): return None
    def __exit__(self, *a): return False


class GraphPropagationEngine:
    """Monte Carlo impulse-response propagation of a Decision's origin
    shock(s) outward through the causal graph."""

    def __init__(self, edges: List[CausalEdge], n_simulations: int = 5_000, seed: int = 42,
                 max_hops: int = DEFAULT_MAX_HOPS, damping: float = DAMPING_FACTOR,
                 audit: Optional[AuditTrail] = None):
        self.edges = edges
        self.n = n_simulations
        self.seed = seed
        self.max_hops = max_hops
        self.damping = damping
        self.audit = audit
        self._by_source: Dict[Tuple[str, str], List[CausalEdge]] = {}
        for e in edges:
            self._by_source.setdefault((e.source_actor, e.source_var), []).append(e)

    def run(self, decision: Decision) -> PropagationResult:
        derived_seed = _derived_seed(decision.id, self.seed)
        rng = np.random.default_rng(derived_seed)
        n = self.n

        ctx = (self.audit.span("GraphPropagationEngine", "propagate",
                                inputs={"decision": decision.id, "n": n, "seed": derived_seed,
                                        "max_hops": self.max_hops, "damping": self.damping})
               if self.audit else _NullCtx())

        with ctx:
            # hop 0: origin shock(s), converted to normalized units. Deterministic
            # magnitude (it's a decision, not a random event) broadcast across all draws.
            frontier: Dict[Tuple[str, str], np.ndarray] = {}
            for shock in decision.origin_shocks:
                tm = STATE_VAR_BY_KEY[shock.var].typical_move
                normalized = (shock.delta / tm) if tm else 0.0
                key = (shock.actor, shock.var)
                frontier[key] = frontier.get(key, np.zeros(n)) + np.full(n, normalized)

            # A company decision additionally routes an attenuated copy of its own
            # shock into its home country's corresponding variable -- see
            # decisions.ProxyRoute docstring for why and how approximate this is.
            if decision.proxy_route:
                for shock in decision.origin_shocks:
                    if shock.actor != decision.actor:
                        continue
                    tm = STATE_VAR_BY_KEY[shock.var].typical_move
                    normalized = (shock.delta / tm) if tm else 0.0
                    key = (decision.proxy_route.home_country, shock.var)
                    frontier[key] = (frontier.get(key, np.zeros(n))
                                      + np.full(n, normalized * decision.proxy_route.scope))

            total_effect: Dict[Tuple[str, str], np.ndarray] = {k: v.copy() for k, v in frontier.items()}
            first_hop_reached: Dict[Tuple[str, str], int] = {k: 0 for k in frontier}
            contribution_log: List[HopContribution] = []

            for hop in range(1, self.max_hops + 1):
                active = {k: v for k, v in frontier.items() if np.mean(np.abs(v)) > ACTIVATION_EPSILON}
                if not active:
                    break
                next_frontier: Dict[Tuple[str, str], np.ndarray] = {}
                for (actor, var), source_delta in active.items():
                    for edge in self._by_source.get((actor, var), []):
                        coef = edge.belief.sample(n, rng)
                        contribution = coef * source_delta
                        tgt = (edge.target_actor, edge.target_var)
                        next_frontier[tgt] = next_frontier.get(tgt, np.zeros(n)) + contribution
                        contribution_log.append(HopContribution(
                            hop=hop, edge_id=edge.id,
                            source_actor=actor, source_var=var,
                            target_actor=edge.target_actor, target_var=edge.target_var,
                            mean_contribution_normalized=float(np.mean(contribution)),
                            lag=edge.lag, rationale=edge.rationale,
                        ))
                next_frontier = {k: v * self.damping for k, v in next_frontier.items()}
                for k, v in next_frontier.items():
                    total_effect[k] = total_effect.get(k, np.zeros(n)) + v
                    if k not in first_hop_reached:
                        first_hop_reached[k] = hop
                frontier = next_frontier

            impacts: Dict[Tuple[str, str], NodeImpact] = {}
            for (actor, var), samples_norm in total_effect.items():
                tm = STATE_VAR_BY_KEY[var].typical_move
                impacts[(actor, var)] = NodeImpact(actor, var, samples_norm * tm, first_hop_reached[(actor, var)])

            if self.audit:
                top = sorted(impacts.values(), key=lambda i: abs(i.mean_normalized), reverse=True)[:5]
                self.audit.log("GraphPropagationEngine", "complete",
                                inputs={"decision": decision.id},
                                outputs={"n_nodes_reached": len(impacts),
                                         "n_edge_firings": len(contribution_log),
                                         "top_impacts": [{"actor": i.actor, "var": i.var,
                                                           "mean_normalized_moves": round(i.mean_normalized, 4)}
                                                          for i in top]})

        return PropagationResult(decision.id, n, derived_seed, impacts, contribution_log)
