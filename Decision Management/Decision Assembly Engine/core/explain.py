"""
Explainability layer.

Turns the numbers in an EvalResult + MCResult into (a) a utility
decomposition anyone can audit line-by-line, and (b) a plain-language
narrative, and (c) tail-risk attribution: which primitive's adverse event
is most over-represented in the worst-5% outcomes (computed empirically
from the Monte Carlo draws, not asserted).

Domain convention: a state_transition_fn may return, inside its
`trajectories` dict, an `"events"` sub-dict mapping primitive_id -> a
boolean array (len = n_simulations) marking whether that primitive's
adverse event fired on each draw. If present, Explainer uses it for
tail-driver attribution; if absent, attribution is simply omitted.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from .audit import AuditTrail
from .evaluator import EvalResult
from .montecarlo import MCResult


@dataclass
class Explanation:
    strategy_name: str
    scenario_name: str
    decomposition: Dict[str, float]
    tail_drivers: List[Dict[str, Any]]
    narrative: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy_name, "scenario": self.scenario_name,
            "decomposition": self.decomposition, "tail_drivers": self.tail_drivers,
            "narrative": self.narrative,
        }


class Explainer:
    def __init__(self, audit: Optional[AuditTrail] = None):
        self.audit = audit

    def explain(self, eval_result: EvalResult, mc: MCResult) -> Explanation:
        decomposition = {
            "expected_npv": round(eval_result.mean_npv, 2),
            "risk_term (lambda_risk * CVaR95)": round(eval_result.utility - eval_result.mean_npv + eval_result.assembly_penalty, 2),
            "assembly_penalty": round(-eval_result.assembly_penalty, 2),
            "total_utility": round(eval_result.utility, 2),
        }

        tail_drivers = self._tail_attribution(mc)

        narrative = self._narrative(eval_result, tail_drivers)

        exp = Explanation(eval_result.strategy_name, eval_result.scenario_name,
                           decomposition, tail_drivers, narrative)
        if self.audit:
            self.audit.log(
                "Explainer", "explanation_generated",
                inputs={"strategy": eval_result.strategy_name, "scenario": eval_result.scenario_name},
                outputs=exp.to_dict(),
            )
        return exp

    @staticmethod
    def _tail_attribution(mc: MCResult) -> List[Dict[str, Any]]:
        events = mc.trajectories.get("events") if mc.trajectories else None
        if not events:
            return []
        npv = mc.npv
        var95 = np.percentile(npv, 5)
        tail_mask = npv <= var95
        overall_n = len(npv)
        tail_n = max(int(tail_mask.sum()), 1)
        out = []
        for pid, flags in events.items():
            flags = np.asarray(flags, dtype=bool)
            overall_rate = float(flags.mean())
            tail_rate = float(flags[tail_mask].mean()) if tail_mask.any() else 0.0
            lift = (tail_rate / overall_rate) if overall_rate > 0 else float("nan")
            out.append({
                "primitive_id": pid,
                "overall_event_rate": round(overall_rate, 4),
                "tail_event_rate (worst 5% of draws)": round(tail_rate, 4),
                "tail_lift": round(lift, 2) if lift == lift else None,
            })
        out.sort(key=lambda d: (d["tail_lift"] or 0), reverse=True)
        return out

    @staticmethod
    def _narrative(r: EvalResult, tail_drivers: List[Dict[str, Any]]) -> str:
        parts = [
            f"{r.strategy_name} under scenario '{r.scenario_name}' requires ${r.capital:.1f}M of "
            f"capital assembled in {r.assembly_index} join step(s) (Assembly Index).",
            f"Across the Monte Carlo run, expected NPV is ${r.mean_npv:.1f}M "
            f"(median ${r.median_npv:.1f}M, std ${r.std_npv:.1f}M), with a "
            f"{r.prob_loss*100:.1f}% chance of a net loss.",
            f"The worst 5% of outcomes average ${r.cvar95:.1f}M (CVaR95); the assembly complexity "
            f"penalty subtracts ${r.assembly_penalty:.1f}M, giving a regularized utility of ${r.utility:.1f}M.",
        ]
        if tail_drivers:
            top = tail_drivers[0]
            if top["tail_lift"] and top["tail_lift"] > 1.05:
                parts.append(
                    f"Primitive {top['primitive_id']} is over-represented in the worst-case draws "
                    f"({top['tail_event_rate (worst 5% of draws)']*100:.1f}% of tail scenarios vs "
                    f"{top['overall_event_rate']*100:.1f}% overall, a {top['tail_lift']}x lift) — "
                    f"it is the primary structural fragility to monitor or hedge."
                )
        return " ".join(parts)
