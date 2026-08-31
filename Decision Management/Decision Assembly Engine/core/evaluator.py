"""
Component 6: Risk-Adjusted Evaluator.

Aggregates a Monte Carlo NPV distribution plus an Assembly's structural
complexity into a single regularized utility score, and provides a
non-dominated (Pareto) frontier across strategies on three axes:
Assembly Index (simplicity), Expected NPV (value), and CVaR95 (downside risk).
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from .audit import AuditTrail
from .montecarlo import MCResult


@dataclass
class EvalResult:
    strategy_name: str
    scenario_name: str
    capital: float
    assembly_index: int
    mean_npv: float
    median_npv: float
    std_npv: float
    var95: float
    cvar95: float
    prob_loss: float
    assembly_penalty: float
    utility: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            "strategy": self.strategy_name, "scenario": self.scenario_name,
            "capital": round(self.capital, 2), "assembly_index": self.assembly_index,
            "mean_npv": round(self.mean_npv, 2), "median_npv": round(self.median_npv, 2),
            "std_npv": round(self.std_npv, 2), "var95": round(self.var95, 2),
            "cvar95": round(self.cvar95, 2), "prob_loss": round(self.prob_loss, 4),
            "assembly_penalty": round(self.assembly_penalty, 2), "utility": round(self.utility, 2),
        }


class RiskEvaluator:
    def __init__(self, lambda_risk: float = 0.5, lambda_assembly: float = 3.0,
                 audit: Optional[AuditTrail] = None):
        self.lambda_risk = lambda_risk
        self.lambda_assembly = lambda_assembly
        self.audit = audit

    def evaluate(self, mc: MCResult, capital: float, assembly_index: int) -> EvalResult:
        npv = mc.npv
        mean_npv = float(np.mean(npv))
        var95 = float(np.percentile(npv, 5))
        tail = npv[npv <= var95]
        cvar95 = float(np.mean(tail)) if len(tail) else var95
        penalty = self.lambda_assembly * assembly_index
        utility = mean_npv + self.lambda_risk * cvar95 - penalty
        res = EvalResult(
            strategy_name=mc.strategy_name, scenario_name=mc.scenario_name,
            capital=capital, assembly_index=assembly_index,
            mean_npv=mean_npv, median_npv=float(np.median(npv)), std_npv=float(np.std(npv)),
            var95=var95, cvar95=cvar95, prob_loss=float(np.mean(npv < 0)),
            assembly_penalty=penalty, utility=utility,
        )
        if self.audit:
            self.audit.log(
                "RiskEvaluator", "utility_computed",
                inputs={"strategy": mc.strategy_name, "scenario": mc.scenario_name,
                        "assembly_index": assembly_index, "lambda_risk": self.lambda_risk,
                        "lambda_assembly": self.lambda_assembly},
                outputs=res.to_dict(),
            )
        return res


def pareto_frontier(results: List[EvalResult]) -> List[str]:
    """
    Non-dominated set across (maximize utility, maximize mean_npv, minimize
    assembly_index, maximize cvar95 i.e. minimize downside). Returns strategy names.
    """
    names = []
    for r in results:
        dominated = False
        for o in results:
            if o.strategy_name == r.strategy_name:
                continue
            better_or_eq = (o.mean_npv >= r.mean_npv and o.cvar95 >= r.cvar95
                             and o.assembly_index <= r.assembly_index)
            strictly_better = (o.mean_npv > r.mean_npv or o.cvar95 > r.cvar95
                                or o.assembly_index < r.assembly_index)
            if better_or_eq and strictly_better:
                dominated = True
                break
        if not dominated:
            names.append(r.strategy_name)
    return names
