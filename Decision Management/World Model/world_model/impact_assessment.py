"""
Impact Assessment generator -- the "alert" artifact for this World Model.

IMPORTANT FRAMING: this module produces a disclosure document, not an
enforcement action. It does not contact anyone, does not assert that a
decision should be opposed, and has no channel to real institutional
leaders. It generates a structured, numbered, assumption-disclosing
report -- projected domestic and cross-border effects of a HYPOTHETICAL
decision, with confidence/uncertainty attached and the dominant modeled
causal path shown for each material effect -- that a human user can
read, challenge, and choose to share through their own channels if they
judge it useful. That is the "Impact-assessment artifact" scope the user
selected over any form of automated alerting.

Every number in here inherits the illustrative/hypothesis status of its
inputs (registry.py baselines, causal_graph.py mechanism coefficients,
decisions.py scenarios). The report says so, prominently and repeatedly,
rather than letting its tables read as findings.
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Dict, List, Optional

import numpy as np

from .decisions import Decision
from .ontology import STATE_VAR_BY_KEY
from .propagation import HopContribution, NodeImpact, PropagationResult
from .registry import actor_label

MATERIALITY_BANDS = [  # (min |mean_normalized_moves|, tier label) -- illustrative cut points
    (0.75, "high"),
    (0.25, "moderate"),
    (0.05, "low"),
    (0.0, "negligible"),
]


def materiality_tier(mean_normalized_moves: float) -> str:
    v = abs(mean_normalized_moves)
    for threshold, label in MATERIALITY_BANDS:
        if v >= threshold:
            return label
    return "negligible"


def sign_consistency_pct(impact: NodeImpact) -> float:
    """Share of Monte Carlo draws whose sign agrees with the mean's sign --
    a rough, cheap confidence proxy: a high-magnitude mean built from
    draws that disagree on direction is a weaker claim than the same mean
    built from draws that agree."""
    s = impact.samples_native
    if impact.mean == 0 or len(s) == 0:
        return 0.0
    agree = np.sum(np.sign(s) == np.sign(impact.mean))
    return float(100.0 * agree / len(s))


def dominant_path(result: PropagationResult, actor: str, var: str) -> List[HopContribution]:
    """Walk backward from (actor, var) one hop at a time, at each step picking
    the single largest-|contribution| edge that fed this node at that hop, to
    surface ONE representative explanatory chain back to the decision's
    origin shock. Real influence is usually the sum of several edges and
    paths; this is "the biggest reason," not "the only reason." """
    impact = result.impacts.get((actor, var))
    if impact is None or impact.first_hop_reached == 0:
        return []
    path: List[HopContribution] = []
    cur_actor, cur_var, cur_hop = actor, var, impact.first_hop_reached
    seen = set()
    while cur_hop >= 1:
        candidates = [c for c in result.contribution_log
                      if c.hop == cur_hop and c.target_actor == cur_actor and c.target_var == cur_var]
        if not candidates:
            break
        best = max(candidates, key=lambda c: abs(c.mean_contribution_normalized))
        key = (best.hop, best.edge_id)
        if key in seen:
            break
        seen.add(key)
        path.append(best)
        cur_actor, cur_var, cur_hop = best.source_actor, best.source_var, cur_hop - 1
    path.reverse()
    return path


def _path_to_text(path: List[HopContribution]) -> str:
    if not path:
        return "direct origin effect of the decision (no intermediate causal hop)."
    steps = []
    for c in path:
        steps.append(f"{actor_label(c.source_actor)}'s {STATE_VAR_BY_KEY[c.source_var].label} "
                      f"→ {actor_label(c.target_actor)}'s {STATE_VAR_BY_KEY[c.target_var].label} "
                      f"(hop {c.hop}, modeled lag {c.lag}: {c.rationale})")
    return "  then  ".join(steps)


def _impact_entry(result: PropagationResult, impact: NodeImpact) -> Dict:
    path = dominant_path(result, impact.actor, impact.var)
    return {
        **impact.to_dict(),
        "actor_label": actor_label(impact.actor),
        "materiality_tier": materiality_tier(impact.mean_normalized),
        "sign_consistency_pct": round(sign_consistency_pct(impact), 1),
        "dominant_path": [c.to_dict() for c in path],
        "dominant_path_text": _path_to_text(path),
    }


@dataclass
class ImpactAssessment:
    decision: Decision
    result: PropagationResult
    generated_at: str
    domestic_impacts: List[Dict]
    cross_border_impacts: List[Dict]
    assumptions_and_limitations: List[str]
    executive_summary: List[str]
    unmodeled_note: Optional[str]

    def to_dict(self) -> Dict:
        return {
            "status": "HYPOTHETICAL — ILLUSTRATIVE MODEL OUTPUT, NOT A REAL-WORLD FORECAST",
            "decision": self.decision.to_dict(),
            "generated_at": self.generated_at,
            "executive_summary": self.executive_summary,
            "assumptions_and_limitations": self.assumptions_and_limitations,
            "domestic_impacts": self.domestic_impacts,
            "cross_border_impacts": self.cross_border_impacts,
            "unmodeled_note": self.unmodeled_note,
            "simulation": {"n_simulations": self.result.n_simulations, "seed": self.result.seed,
                            "n_nodes_reached": len(self.result.impacts),
                            "n_edge_firings": len(self.result.contribution_log)},
        }


def _standard_assumptions(decision: Decision) -> List[str]:
    items = [
        "This decision is HYPOTHETICAL/fictional, authored to exercise the model -- it is not a real "
        "announced policy or corporate action.",
        "All actor baseline values (registry.py) are illustrative placeholders, not sourced or current "
        "real-world statistics.",
        "All causal edges are expert-elicited hypotheses with an explicit uncertainty band (a Bayesian "
        "NormalBelief), not statistically fitted or empirically validated causal effects.",
        "Cross-border spillover is generated only from the illustrative bilateral trade-dependency links "
        "in registry.TRADE_LINKS -- real trade/financial/diplomatic spillover channels are far richer than "
        "the energy/agriculture/industrial links modeled here.",
        "Propagation is bounded to a small number of hops and each hop's newly produced effect is damped "
        "(factor 0.65) before continuing -- a modeling convenience to keep the walk finite given the graph's "
        "cycles, not an empirical decay rate.",
        "A variable with no further outgoing modeled edges is not asserted to have no further real-world "
        "effects -- it means the hand-authored mechanism library (causal_graph.SECTOR_MECHANISMS) does not "
        "yet encode one; this is a known gap for expert review to fill, not a finding.",
    ]
    if decision.proxy_route:
        items.append(
            f"This decision's actor ({actor_label(decision.actor)}) is a company, which has no direct "
            f"edges in the causal graph; its shock is additionally injected into "
            f"{actor_label(decision.proxy_route.home_country)} at an illustrative scope of "
            f"{decision.proxy_route.scope:.0%} ({decision.proxy_route.rationale})."
        )
    return items


def generate_impact_assessment(decision: Decision, result: PropagationResult, top_n: int = 6) -> ImpactAssessment:
    ranked = result.ranked_impacts(exclude_origin=True)
    origin_actors = {s.actor for s in decision.origin_shocks}
    if decision.proxy_route:
        origin_actors.add(decision.proxy_route.home_country)

    domestic = [i for i in ranked if i.actor in origin_actors]
    cross_border = [i for i in ranked if i.actor not in origin_actors]

    domestic_entries = [_impact_entry(result, i) for i in domestic[:top_n]]
    cross_border_entries = [_impact_entry(result, i) for i in cross_border[:top_n]]

    summary = [
        f"HYPOTHETICAL decision: {decision.name}.",
        f"Actor: {actor_label(decision.actor)} ({decision.actor_kind}). Status: {decision.status}.",
        f"Modeled via an Assembly of {len(decision.assembly.primitives())} action primitive(s), "
        f"Assembly Index {decision.assembly.assembly_index}, illustrative total cost "
        f"{decision.assembly.total_cost:,.1f}.",
    ]
    if domestic_entries:
        top_d = domestic_entries[0]
        summary.append(
            f"Largest modeled domestic effect: {top_d['var_label']} in {top_d['actor_label']} shifts by "
            f"~{top_d['mean']:+.2f} ({top_d['p5']:+.2f} to {top_d['p95']:+.2f} across simulated draws), "
            f"materiality tier '{top_d['materiality_tier']}', direction consistent in "
            f"{top_d['sign_consistency_pct']:.0f}% of draws."
        )
    if cross_border_entries:
        top_c = cross_border_entries[0]
        summary.append(
            f"Largest modeled cross-border effect: {top_c['var_label']} in {top_c['actor_label']} shifts by "
            f"~{top_c['mean']:+.2f} ({top_c['p5']:+.2f} to {top_c['p95']:+.2f}), materiality tier "
            f"'{top_c['materiality_tier']}', reaching that actor via: {top_c['dominant_path_text']}"
        )
    else:
        summary.append("No materially-reached cross-border effects were produced by the current mechanism "
                        "library and trade-link set for this decision.")

    unmodeled = None
    leaf_vars = {i.var for i in ranked if i.first_hop_reached > 0}
    if leaf_vars:
        unmodeled = ("Several reached variables currently have no further outgoing modeled mechanism "
                      "(e.g. " + ", ".join(sorted({STATE_VAR_BY_KEY[v].label for v in list(leaf_vars)[:3]}))
                      + "), so this report's cascade stops there -- not because the real-world effect "
                      "necessarily stops there.")

    return ImpactAssessment(
        decision=decision, result=result,
        generated_at=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        domestic_impacts=domestic_entries, cross_border_impacts=cross_border_entries,
        assumptions_and_limitations=_standard_assumptions(decision),
        executive_summary=summary, unmodeled_note=unmodeled,
    )
