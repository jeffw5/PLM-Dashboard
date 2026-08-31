"""
Domain 1 — Enterprise AI Infrastructure R&D Portfolio Allocation.

$50M / 3-year capital allocation across three next-gen platform strategies:
  A. Monolithic Custom Silicon   (In-House ASIC + Compiler)
  B. Modular Hybrid System       (COTS GPUs + Optical Interconnect + Compiler)
  C. Pure Cloud API Orchestration

Everything domain-specific lives in this file: the primitive library, the
three candidate Assemblies, the Bayesian priors, the scenario shock specs,
and the state_transition_fn (quarterly cash-flow physics). Every component
class it calls (Assembly, BetaBelief, NormalBelief, MonteCarloEngine,
RiskEvaluator, Explainer, and all four patterns) is imported unchanged from
core/.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core.audit import AuditTrail
from core.bayesian import BetaBelief, NormalBelief
from core.evaluator import RiskEvaluator
from core.explain import Explainer
from core.montecarlo import MonteCarloEngine, ScenarioSampler, VarSpec, sample_execution_trace
from core.patterns import (ActiveEpistemicGraph, AssemblyConstrainedStressTester,
                            DualLoopAssemblyOptimizer)
from core.primitives import Assembly, AssemblyNode, JoinOp, Primitive, leaf, parallel, serial
from core.state import npv_of

DOMAIN = "rd_portfolio"
QUARTERS = 12
DISCOUNT_RATE_ANNUAL = 0.08


def build_primitive_library() -> Dict[str, Primitive]:
    return {
        "P1": Primitive("P1", "In-House Silicon Tape-Out", cost=30.0, lead_time=6,
                         prior_alpha=2.0, prior_beta=8.0),
        "P2": Primitive("P2", "Custom Optical Interconnect", cost=12.0, lead_time=4,
                         prior_alpha=3.0, prior_beta=7.0),
        "P3": Primitive("P3", "Custom ML Compiler Stack", cost=8.0, lead_time=3,
                         prior_alpha=1.0, prior_beta=9.0),
        "P4": Primitive("P4", "COTS GPU Cluster Procurement", cost=15.0, lead_time=2,
                         prior_alpha=0.5, prior_beta=9.5),
        "P5": Primitive("P5", "Cloud API Wrapper & Middleware", cost=5.0, lead_time=1,
                         prior_alpha=0.2, prior_beta=9.8),
    }


def build_strategies(lib: Dict[str, Primitive], audit: AuditTrail) -> Dict[str, Assembly]:
    # P1 (silicon) and P3 (compiler) are developed concurrently and integrated
    # at the end, so the critical path is max(lead times), not their sum.
    a = Assembly("Strategy A: Monolithic In-House",
                 parallel(leaf(lib["P1"]), leaf(lib["P3"])), audit,
                 meta={"base_unit_capacity": 1.3, "margin_multiplier": 1.55})
    b = Assembly("Strategy B: Modular Hybrid",
                 serial(parallel(leaf(lib["P4"]), leaf(lib["P2"])), leaf(lib["P3"])), audit,
                 meta={"base_unit_capacity": 1.0, "margin_multiplier": 1.05})
    c = Assembly("Strategy C: Pure Cloud API",
                 leaf(lib["P5"]), audit,
                 meta={"base_unit_capacity": 0.7, "margin_multiplier": 0.38})
    return {"A": a, "B": b, "C": c}


def build_beliefs(lib: Dict[str, Primitive], audit: AuditTrail) -> Dict[str, BetaBelief]:
    return {pid: BetaBelief(f"{pid}_failure_rate", p.prior_alpha, p.prior_beta, audit)
            for pid, p in lib.items()}


def build_demand_belief(audit: AuditTrail) -> NormalBelief:
    prior = NormalBelief("enterprise_compute_demand_pflops", mu=100.0, sigma=5.0, audit=audit)
    return prior.update(data=[112.0, 108.0, 115.0], obs_sigma=4.0)


def build_scenarios(demand_belief: NormalBelief, audit: AuditTrail) -> Dict[str, ScenarioSampler]:
    corr = np.array([[1.0, 0.4, -0.2],
                      [0.4, 1.0, -0.1],
                      [-0.2, -0.1, 1.0]])

    def sampler(demand_mu, demand_sigma, lead_sigma, margin_low, margin_mode, margin_high):
        specs = [
            VarSpec("demand", "normal", {"mu": demand_mu, "sigma": demand_sigma}),
            VarSpec("base_margin", "triangular", {"low": margin_low, "mode": margin_mode, "high": margin_high}),
            VarSpec("lead_time_multiplier", "lognormal", {"mu": 0.0, "sigma": lead_sigma}),
        ]
        return ScenarioSampler(specs, correlation=corr, audit=audit)

    mu, sigma = demand_belief.mu, demand_belief.sigma
    return {
        "baseline": sampler(mu, sigma, 0.15, 0.35, 0.50, 0.65),
        "demand_surge": sampler(mu * 1.25, sigma * 1.1, 0.15, 0.40, 0.55, 0.70),
        "hardware_supply_shock": sampler(mu, sigma, 0.45, 0.30, 0.45, 0.60),
        "margin_compression": sampler(mu * 0.9, sigma, 0.20, 0.20, 0.32, 0.45),
    }


def state_transition_fn(assembly: Assembly, shocks: Dict[str, np.ndarray],
                         failure_draws: Dict[str, np.ndarray], rng: np.random.Generator,
                         n: int, trace_rows: Optional[List[int]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    demand = shocks["demand"]
    margin = shocks["base_margin"]
    lead_mult = shocks["lead_time_multiplier"]

    total_capex = assembly.total_cost()
    base_lead = assembly.critical_path_lead_time()
    base_capacity = assembly.meta["base_unit_capacity"]
    margin_multiplier = assembly.meta["margin_multiplier"]

    build_q = np.clip(np.ceil(base_lead * lead_mult), 1, QUARTERS).astype(int)

    events = {pid: (rng.random(n) < prob) for pid, prob in failure_draws.items()}
    has_failed = np.zeros(n, dtype=bool)
    for flags in events.values():
        has_failed |= flags

    col = np.arange(QUARTERS)[None, :]
    build_mask = (col < build_q[:, None]).astype(float)
    capex_per_q = total_capex / build_q
    cash = -build_mask * capex_per_q[:, None]

    rework_col = np.minimum(build_q, QUARTERS - 1)
    cash[np.arange(n)[has_failed], rework_col[has_failed]] -= 12.0

    op_start = np.where(has_failed, np.minimum(build_q + 2, QUARTERS), build_q)
    effective_capacity = base_capacity * np.where(has_failed, 0.6, 1.0)
    unit_margin = margin * margin_multiplier
    quarterly_revenue = effective_capacity * demand * unit_margin / 4.0
    rev_mask = (col >= op_start[:, None]).astype(float)
    cash = cash + rev_mask * quarterly_revenue[:, None]

    npv = npv_of(cash, DISCOUNT_RATE_ANNUAL / 4.0)
    trajectories = {"events": events, "has_failed": has_failed, "build_quarters": build_q}

    if trace_rows:
        discount = (1.0 + DISCOUNT_RATE_ANNUAL / 4.0) ** np.arange(1, QUARTERS + 1)
        trace = {}
        for i in trace_rows:
            quarters = []
            cum = 0.0
            for t in range(QUARTERS):
                phase = "build" if t < build_q[i] else ("rework" if has_failed[i] and t < op_start[i] else "operate")
                c = float(cash[i, t])
                cum += c / discount[t]
                if phase == "build":
                    health = 0.0
                elif phase == "rework":
                    health = 0.0
                else:
                    health = float(effective_capacity[i] / base_capacity)
                fired = [pid for pid, flags in events.items() if flags[i] and t == rework_col[i]]
                quarters.append({"t": t, "phase": phase, "cash": round(c, 3),
                                  "cumulative_npv": round(float(cum), 3), "health": round(health, 3),
                                  "events": fired})
            trace[int(i)] = {"quarters": quarters}
        trajectories["trace"] = trace

    return npv, trajectories


def liquidity_decision_rule(liquidity_available: float):
    """Loop 2 of the Dual-Loop Optimizer: among baseline-scenario candidates
    whose CVaR95 tail loss the available liquidity can actually absorb, pick
    the highest-utility one; if none are affordable, fall back to whichever
    has the least-bad tail loss (capital preservation)."""
    def rule(results):
        baseline = [r for r in results if r.scenario_name == "baseline"]
        affordable = [r for r in baseline if r.cvar95 >= -liquidity_available]
        if affordable:
            best = max(affordable, key=lambda r: r.utility)
            return best.strategy_name, (
                f"Liquidity (${liquidity_available:.0f}M) can absorb {best.strategy_name}'s CVaR95 "
                f"tail loss (${best.cvar95:.1f}M); among the strategies that fit within this constraint "
                f"it has the highest regularized utility (${best.utility:.1f}M).")
        best = max(baseline, key=lambda r: r.cvar95)
        return best.strategy_name, (
            f"No strategy's CVaR95 tail loss fits within ${liquidity_available:.0f}M of available liquidity; "
            f"{best.strategy_name} has the least-bad downside (${best.cvar95:.1f}M) and is recommended "
            f"for capital preservation.")
    return rule


def run(audit: AuditTrail, n_simulations: int = 10_000, liquidity_available: float = 25.0) -> Dict[str, Any]:
    lib = build_primitive_library()
    strategies = build_strategies(lib, audit)
    beliefs = build_beliefs(lib, audit)
    demand_post = build_demand_belief(audit)
    scenarios = build_scenarios(demand_post, audit)

    evaluator = RiskEvaluator(lambda_risk=0.5, lambda_assembly=4.0, audit=audit)
    explainer = Explainer(audit=audit)

    tester = AssemblyConstrainedStressTester(evaluator, explainer, n_simulations, seed=42, audit=audit)
    results, explanations = tester.run(list(strategies.values()), beliefs, state_transition_fn, scenarios)

    optimizer = DualLoopAssemblyOptimizer(audit=audit)
    baseline_results = [r for r in results if r.scenario_name == "baseline"]
    selection = optimizer.optimize(baseline_results, decision_rule=liquidity_decision_rule(liquidity_available))

    voi = ActiveEpistemicGraph(scenarios["baseline"], evaluator, n_simulations, seed=42, audit=audit).run(
        strategies["A"], beliefs, watch_primitive="P1",
        milestone_failures=1, milestone_trials=10,
        state_transition_fn=state_transition_fn, scenario_name="baseline")

    # Step-through execution traces (a few representative Monte Carlo draws,
    # replayed quarter-by-quarter) for the "Simulate" view — kept off the main
    # audit trail since these are UI inspection replays, not decision inputs.
    execution_traces = {}
    for assembly in strategies.values():
        execution_traces[assembly.name] = {}
        for scen_name, sampler in scenarios.items():
            # Trace replays are UI inspection, not new decision inputs — quiet
            # the sampler's own audit reference for these calls so the trail
            # doesn't fill with duplicate joint_draw entries.
            prior_audit, sampler.audit = sampler.audit, None
            engine = MonteCarloEngine(sampler, n_simulations, seed=42, audit=None)
            execution_traces[assembly.name][scen_name] = sample_execution_trace(
                engine, assembly, beliefs, state_transition_fn, scen_name)
            sampler.audit = prior_audit

    return {
        "domain": DOMAIN,
        "title": "Enterprise AI Infrastructure R&D Portfolio Allocation",
        "primitives": {pid: p.to_dict() for pid, p in lib.items()},
        "strategies": {k: a.to_dict() for k, a in strategies.items()},
        "beliefs": {"demand_pflops": demand_post.to_dict(),
                    **{pid: b.to_dict() for pid, b in beliefs.items()}},
        "scenario_names": list(scenarios.keys()),
        "results": [r.to_dict() for r in results],
        "explanations": explanations,
        "selection": selection,
        "value_of_information": {
            "strategy": voi.strategy_name, "pre_utility": round(voi.pre_utility, 2),
            "post_utility": round(voi.post_utility, 2), "voi": round(voi.value_of_information, 2),
            "posterior_belief": voi.posterior_belief,
            "narrative": (f"A P1 tape-out lab pilot (1 failure in 10 test wafers) shifts the failure-rate "
                          f"posterior from {beliefs['P1'].to_dict()['mean']*100:.1f}% to "
                          f"{voi.posterior_belief['mean']*100:.1f}%, changing Strategy A's baseline "
                          f"utility from ${voi.pre_utility:.1f}M to ${voi.post_utility:.1f}M "
                          f"(Value of Information: ${voi.value_of_information:.1f}M) before the "
                          f"full $30M tape-out commitment is made."),
        },
        "liquidity_available": liquidity_available,
        "execution_traces": execution_traces,
    }
