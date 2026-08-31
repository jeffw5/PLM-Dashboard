"""
Component 4: Stochastic Scenario Generator / Monte Carlo Engine — the
aleatory-uncertainty layer.

ScenarioSampler draws N correlated joint realizations of the domain's
exogenous shock variables using a Gaussian copula (so e.g. "demand surge"
and "input-cost spike" can be made to co-move realistically), then maps
each marginal through its target distribution (normal / lognormal /
triangular / Beta-posterior). MonteCarloEngine then propagates each draw,
plus independently-sampled primitive failure/event indicators drawn from
their Bayesian posteriors, through a domain-supplied state_transition_fn.

Nothing here is domain-specific: the same class runs the R&D-portfolio,
supply-chain, and cyber-defense engines unchanged.
"""
from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

import numpy as np
from scipy.stats import norm, lognorm, triang

from .audit import AuditTrail
from .bayesian import BetaBelief
from .primitives import Assembly


@dataclass
class VarSpec:
    """One exogenous shock variable's marginal distribution."""
    name: str
    kind: str                     # "normal" | "lognormal" | "triangular"
    params: Dict[str, float]      # distribution parameters

    def ppf(self, u: np.ndarray) -> np.ndarray:
        if self.kind == "normal":
            return norm.ppf(u, loc=self.params["mu"], scale=self.params["sigma"])
        if self.kind == "lognormal":
            return lognorm.ppf(u, s=self.params["sigma"], scale=np.exp(self.params["mu"]))
        if self.kind == "triangular":
            lo, mode, hi = self.params["low"], self.params["mode"], self.params["high"]
            c = (mode - lo) / (hi - lo)
            return triang.ppf(u, c, loc=lo, scale=(hi - lo))
        raise ValueError(f"unknown distribution kind: {self.kind}")


class ScenarioSampler:
    """Gaussian-copula joint sampler over a set of named VarSpecs."""

    def __init__(self, specs: List[VarSpec], correlation: Optional[np.ndarray] = None,
                 audit: Optional[AuditTrail] = None):
        self.specs = specs
        k = len(specs)
        self.correlation = correlation if correlation is not None else np.eye(k)
        self.audit = audit

    def sample(self, n: int, rng: np.random.Generator, scenario_name: str = "baseline") -> Dict[str, np.ndarray]:
        k = len(self.specs)
        z = rng.multivariate_normal(mean=np.zeros(k), cov=self.correlation, size=n)
        u = norm.cdf(z)  # to uniform marginals, preserving copula correlation
        out = {spec.name: spec.ppf(u[:, i]) for i, spec in enumerate(self.specs)}
        if self.audit:
            self.audit.log(
                "ScenarioSampler", "joint_draw",
                inputs={"scenario": scenario_name, "n": n,
                        "variables": [s.name for s in self.specs],
                        "correlation": self.correlation.round(3).tolist()},
                outputs={k_: {"mean": float(np.mean(v)), "std": float(np.std(v))} for k_, v in out.items()},
            )
        return out


@dataclass
class MCResult:
    strategy_name: str
    scenario_name: str
    npv: np.ndarray
    trajectories: Dict[str, np.ndarray] = field(default_factory=dict)
    failure_draws: Dict[str, np.ndarray] = field(default_factory=dict)


class MonteCarloEngine:
    """
    Component 4 (orchestrator): draws shocks + primitive failure indicators,
    hands each realization to a domain-supplied state_transition_fn, and
    collects the resulting NPV (and any auxiliary trajectories) distribution.
    """

    def __init__(self, sampler: ScenarioSampler, n_simulations: int = 10_000,
                 seed: int = 42, audit: Optional[AuditTrail] = None):
        self.sampler = sampler
        self.n = n_simulations
        self.seed = seed
        self.audit = audit

    def _derived_seed(self, assembly: Assembly, scenario_name: str) -> int:
        # A stable (cross-process) hash, unlike Python's randomized str hash() —
        # so re-running this program later reproduces bit-identical draws, which
        # both the audit chain-hash and the execution-trace replay depend on.
        h = hashlib.sha256(f"{assembly.name}|{scenario_name}".encode("utf-8")).hexdigest()
        return (self.seed + int(h[:8], 16) % 10_000) % (2 ** 31 - 1)

    def run(self, assembly: Assembly, beliefs: Dict[str, BetaBelief],
            state_transition_fn: Callable[[Assembly, Dict[str, np.ndarray], Dict[str, np.ndarray], np.random.Generator, int], Any],
            scenario_name: str = "baseline", trace_rows: Optional[List[int]] = None) -> MCResult:
        # Seed derived from (assembly, scenario) so every strategy/scenario pair
        # is independently reproducible yet the whole sweep is deterministic —
        # calling run() twice with the same assembly/scenario (e.g. once to find
        # percentile draws, once with trace_rows set to inspect them) replays
        # bit-identical random draws.
        derived_seed = self._derived_seed(assembly, scenario_name)
        rng = np.random.default_rng(derived_seed)
        with (self.audit.span("MonteCarloEngine", "strategy_run",
                               inputs={"strategy": assembly.name, "scenario": scenario_name,
                                       "n": self.n, "seed": derived_seed})
              if self.audit else _nullctx()):
            shocks = self.sampler.sample(self.n, rng, scenario_name)
            failure_draws = {
                pid: belief.sample(self.n, rng) for pid, belief in beliefs.items()
                if pid in [p.id for p in assembly.primitives()]
            }
            npv, trajectories = state_transition_fn(assembly, shocks, failure_draws, rng, self.n,
                                                      trace_rows=trace_rows)
            if self.audit:
                self.audit.log(
                    "MonteCarloEngine", "propagation_complete",
                    inputs={"strategy": assembly.name, "scenario": scenario_name},
                    outputs={"npv_mean": float(np.mean(npv)), "npv_std": float(np.std(npv)),
                             "npv_p5": float(np.percentile(npv, 5)), "npv_p95": float(np.percentile(npv, 95))},
                )
        return MCResult(assembly.name, scenario_name, npv, trajectories, failure_draws)


def sample_execution_trace(engine: "MonteCarloEngine", assembly: Assembly,
                            beliefs: Dict[str, BetaBelief], state_transition_fn: Callable,
                            scenario_name: str = "baseline",
                            percentiles: Optional[List[tuple]] = None) -> List[Dict[str, Any]]:
    """
    Replay a handful of individual Monte Carlo draws quarter-by-quarter, so a
    UI can step through "how the decision actually plays out" instead of only
    seeing the aggregate distribution. Two-pass by construction: pass 1 finds
    which draw index sits at each requested percentile of the NPV outcome;
    pass 2 re-runs with the SAME derived seed (so the draws are bit-identical)
    asking state_transition_fn to also emit full per-quarter detail for just
    those rows. Domain-agnostic — works for any state_transition_fn that
    honors the `trace_rows` kwarg (see domains/*.py for the convention).
    """
    percentiles = percentiles or [(10, "Downside"), (50, "Typical"), (90, "Upside")]
    pass1 = engine.run(assembly, beliefs, state_transition_fn, scenario_name)
    order = np.argsort(pass1.npv)
    n = len(order)
    row_for_label = {}
    for p, label in percentiles:
        pos = int(round(p / 100 * (n - 1)))
        row_for_label[label] = int(order[pos])
    trace_rows = sorted(set(row_for_label.values()))
    pass2 = engine.run(assembly, beliefs, state_transition_fn, scenario_name, trace_rows=trace_rows)
    trace_by_row = pass2.trajectories.get("trace", {})
    out = []
    for p, label in percentiles:
        row = row_for_label[label]
        detail = trace_by_row.get(row) or trace_by_row.get(str(row))
        if not detail:
            continue
        out.append({
            "label": label, "percentile": p, "row": row,
            "final_npv": float(pass1.npv[row]),
            "quarters": detail["quarters"],
        })
    return out


class _nullctx:
    def __enter__(self): return None
    def __exit__(self, *a): return False
