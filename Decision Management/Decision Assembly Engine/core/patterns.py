"""
Four reusable orchestration patterns, built ONLY from the six core
components (primitives/assembly, bayesian, montecarlo, state, evaluator,
explain). Every domains/*.py module imports these classes UNCHANGED — only
the primitives, assemblies, state_transition_fn and scenarios differ. That
is the concrete evidence that "decision functors" generalize across domains.

  1. AssemblyPipeline               — combinatorial option generator + pruning
  2. ActiveEpistemicGraph            — sequential Bayesian learning / value of information
  3. AssemblyConstrainedStressTester — multi-scenario risk & fragility sweep
  4. DualLoopAssemblyOptimizer       — Pareto frontier + rule-based final selection
"""
from __future__ import annotations

from dataclasses import dataclass
from itertools import combinations
from typing import Any, Callable, Dict, List, Optional, Tuple

import numpy as np

from .audit import AuditTrail
from .bayesian import BetaBelief
from .evaluator import EvalResult, RiskEvaluator, pareto_frontier
from .explain import Explainer
from .montecarlo import MonteCarloEngine, ScenarioSampler
from .primitives import Assembly, AssemblyNode, JoinOp, Primitive, leaf


# ---------------------------------------------------------------------------
# Pattern 1: Assembly Pipeline (Combinatorial Option Generator)
# ---------------------------------------------------------------------------
class AssemblyPipeline:
    """Generates candidate Assemblies from a primitive library and prunes
    infeasible ones (budget / lead-time / max complexity) before they ever
    reach Monte Carlo — the combinatorial search-space stage of the engine."""

    def __init__(self, audit: Optional[AuditTrail] = None):
        self.audit = audit

    def generate(self, library: List[Primitive], max_k: int = 3,
                 join: JoinOp = JoinOp.PARALLEL, budget: Optional[float] = None,
                 max_lead_time: Optional[float] = None,
                 max_assembly_index: Optional[int] = None) -> List[Assembly]:
        raw: List[Assembly] = []
        for k in range(1, max_k + 1):
            for combo in combinations(library, k):
                if k == 1:
                    node = leaf(combo[0])
                else:
                    node = AssemblyNode(label=f"combo[{','.join(p.id for p in combo)}]",
                                         children=[leaf(p) for p in combo], join=join)
                name = "+".join(p.id for p in combo)
                raw.append(Assembly(name, node, audit=self.audit))

        survivors = []
        pruned = []
        for a in raw:
            ax = a.assembly_index()
            reasons = []
            if budget is not None and a.total_cost() > budget:
                reasons.append(f"cost {a.total_cost():.1f} > budget {budget:.1f}")
            if max_lead_time is not None and a.critical_path_lead_time() > max_lead_time:
                reasons.append(f"lead_time {a.critical_path_lead_time():.1f} > max {max_lead_time:.1f}")
            if max_assembly_index is not None and ax > max_assembly_index:
                reasons.append(f"Ax {ax} > max {max_assembly_index}")
            if reasons:
                pruned.append((a.name, reasons))
            else:
                survivors.append(a)

        if self.audit:
            self.audit.log(
                "AssemblyPipeline", "generate_and_prune",
                inputs={"library": [p.id for p in library], "max_k": max_k,
                        "budget": budget, "max_lead_time": max_lead_time,
                        "max_assembly_index": max_assembly_index},
                outputs={"n_generated": len(raw), "n_survived": len(survivors),
                         "n_pruned": len(pruned), "pruned": pruned[:25]},
            )
        return survivors


# ---------------------------------------------------------------------------
# Pattern 2: Active Epistemic Graph (Sequential Bayesian Assembly)
# ---------------------------------------------------------------------------
@dataclass
class VOIResult:
    strategy_name: str
    pre_utility: float
    post_utility: float
    value_of_information: float
    posterior_belief: Dict[str, Any]


class ActiveEpistemicGraph:
    """Runs a strategy pre-milestone (on the prior), simulates an interim
    milestone observation, updates the Bayesian belief, and re-runs the
    strategy post-milestone — quantifying Value of Information (VOI) as the
    utility delta a stage-gate purchases before committing full capital."""

    def __init__(self, sampler: ScenarioSampler, evaluator: RiskEvaluator,
                 n_simulations: int = 10_000, seed: int = 42, audit: Optional[AuditTrail] = None):
        self.sampler = sampler
        self.evaluator = evaluator
        self.n = n_simulations
        self.seed = seed
        self.audit = audit

    def run(self, assembly: Assembly, beliefs: Dict[str, BetaBelief], watch_primitive: str,
             milestone_failures: int, milestone_trials: int,
             state_transition_fn: Callable, scenario_name: str = "baseline") -> VOIResult:
        with (self.audit.span("ActiveEpistemicGraph", "sequential_run",
                               inputs={"strategy": assembly.name, "watch_primitive": watch_primitive})
              if self.audit else _null()):
            engine = MonteCarloEngine(self.sampler, self.n, self.seed, self.audit)

            pre_mc = engine.run(assembly, beliefs, state_transition_fn, scenario_name + "/pre-milestone")
            pre_eval = self.evaluator.evaluate(pre_mc, assembly.total_cost(), assembly.assembly_index())

            updated = dict(beliefs)
            updated[watch_primitive] = beliefs[watch_primitive].update(
                milestone_failures, milestone_trials - milestone_failures)

            post_mc = engine.run(assembly, updated, state_transition_fn, scenario_name + "/post-milestone")
            post_eval = self.evaluator.evaluate(post_mc, assembly.total_cost(), assembly.assembly_index())

            voi = post_eval.utility - pre_eval.utility
            result = VOIResult(assembly.name, pre_eval.utility, post_eval.utility, voi,
                                updated[watch_primitive].to_dict())
            if self.audit:
                self.audit.log(
                    "ActiveEpistemicGraph", "value_of_information",
                    inputs={"strategy": assembly.name, "watch_primitive": watch_primitive,
                            "milestone_failures": milestone_failures, "milestone_trials": milestone_trials},
                    outputs={"pre_utility": pre_eval.utility, "post_utility": post_eval.utility,
                             "voi": voi, "posterior": updated[watch_primitive].to_dict()},
                )
        return result


# ---------------------------------------------------------------------------
# Pattern 3: Assembly-Constrained Stress-Tester (Scenario & Risk Optimization)
# ---------------------------------------------------------------------------
class AssemblyConstrainedStressTester:
    """Sweeps every strategy across every named stress scenario, producing a
    strategy x scenario impact matrix plus a fragility flag for primitives
    that are structural bottlenecks (shared across the strategies with the
    worst downside in a given scenario)."""

    def __init__(self, evaluator: RiskEvaluator, explainer: Explainer,
                 n_simulations: int = 10_000, seed: int = 42, audit: Optional[AuditTrail] = None):
        self.evaluator = evaluator
        self.explainer = explainer
        self.n = n_simulations
        self.seed = seed
        self.audit = audit

    def run(self, assemblies: List[Assembly], beliefs: Dict[str, BetaBelief],
            state_transition_fn: Callable,
            scenarios: Dict[str, ScenarioSampler]) -> Tuple[List[EvalResult], List[Dict[str, Any]]]:
        results: List[EvalResult] = []
        explanations: List[Dict[str, Any]] = []
        for scen_name, sampler in scenarios.items():
            engine = MonteCarloEngine(sampler, self.n, self.seed, self.audit)
            for a in assemblies:
                mc = engine.run(a, beliefs, state_transition_fn, scen_name)
                ev = self.evaluator.evaluate(mc, a.total_cost(), a.assembly_index())
                results.append(ev)
                explanations.append(self.explainer.explain(ev, mc).to_dict())
        if self.audit:
            worst = sorted(results, key=lambda r: r.cvar95)[:3]
            self.audit.log(
                "AssemblyConstrainedStressTester", "sweep_complete",
                inputs={"n_strategies": len(assemblies), "n_scenarios": len(scenarios)},
                outputs={"n_runs": len(results),
                         "worst_3_by_cvar95": [(r.strategy_name, r.scenario_name, round(r.cvar95, 2)) for r in worst]},
            )
        return results, explanations


# ---------------------------------------------------------------------------
# Pattern 4: Dual-Loop Assembly Optimizer (Objective & Utility Tuning)
# ---------------------------------------------------------------------------
class DualLoopAssemblyOptimizer:
    """Loop 1 (structure): compute the Pareto frontier over Ax / E[NPV] /
    CVaR95. Loop 2 (preference): apply a domain-supplied decision rule
    (e.g. a liquidity or risk-appetite constraint) to pick the single
    recommended strategy from the frontier, with the reasoning recorded."""

    def __init__(self, audit: Optional[AuditTrail] = None):
        self.audit = audit

    def optimize(self, results: List[EvalResult],
                 decision_rule: Optional[Callable[[List[EvalResult]], Tuple[str, str]]] = None
                 ) -> Dict[str, Any]:
        frontier = pareto_frontier(results)
        by_utility = sorted(results, key=lambda r: r.utility, reverse=True)
        recommended, rationale = (by_utility[0].strategy_name, "highest regularized utility")
        if decision_rule is not None:
            recommended, rationale = decision_rule(results)
        out = {
            "pareto_frontier": frontier,
            "ranked_by_utility": [(r.strategy_name, round(r.utility, 2)) for r in by_utility],
            "recommended": recommended,
            "rationale": rationale,
        }
        if self.audit:
            self.audit.log(
                "DualLoopAssemblyOptimizer", "final_selection",
                inputs={"n_candidates": len(results)},
                outputs=out,
            )
        return out


class _null:
    def __enter__(self): return None
    def __exit__(self, *a): return False
