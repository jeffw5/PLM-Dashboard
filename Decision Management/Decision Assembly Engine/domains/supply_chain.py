"""
Domain 2 — Critical Component Sourcing & Supply-Chain Resilience.

A manufacturer must decide how to source a critical component over a
2.5-year (10-quarter) horizon:
  A. Low-Cost Single Source     (one supplier contract, no redundancy)
  B. Resilient Dual-Source       (second supplier + regional hub + buffer stock)
  C. Vertical Integration        (build an in-house plant)

This module reuses every core/ class UNCHANGED from domains/rd_portfolio.py
(same Primitive, Assembly, BetaBelief/NormalBelief, MonteCarloEngine,
RiskEvaluator, Explainer, and all four patterns) — only the primitive
library, assemblies, beliefs, scenarios and state_transition_fn differ.

It additionally exercises Pattern 1 (AssemblyPipeline) explicitly: the full
combinatorial candidate set is auto-generated from the primitive library and
pruned by budget/lead-time/complexity, rather than hand-specified, to show
the generator half of the engine (the R&D domain hand-specifies its three
strategies; this domain shows the alternative, automated path).
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core.audit import AuditTrail
from core.bayesian import BetaBelief, NormalBelief
from core.evaluator import RiskEvaluator
from core.explain import Explainer
from core.montecarlo import MonteCarloEngine, ScenarioSampler, VarSpec, sample_execution_trace
from core.patterns import AssemblyConstrainedStressTester, AssemblyPipeline, DualLoopAssemblyOptimizer
from core.primitives import Assembly, JoinOp, Primitive, leaf, parallel
from core.state import npv_of

DOMAIN = "supply_chain"
QUARTERS = 10
DISCOUNT_RATE_ANNUAL = 0.10


def build_primitive_library() -> Dict[str, Primitive]:
    # prior_alpha/prior_beta parameterize a PER-QUARTER disruption hazard rate
    # (Beta belief over a Bernoulli-per-quarter process), not a whole-horizon
    # probability — risk compounds over the 10-quarter horizon in the state
    # transition, which is what makes single-sourcing materially riskier over
    # a multi-year window even though its per-quarter hazard looks modest.
    return {
        "Q1": Primitive("Q1", "Single-Source Supply Contract", cost=2.0, lead_time=1,
                         prior_alpha=0.8, prior_beta=9.2),
        "Q2": Primitive("Q2", "Dual-Source Qualification", cost=6.0, lead_time=3,
                         prior_alpha=0.2, prior_beta=9.8),
        "Q3": Primitive("Q3", "Regional Distribution Hub", cost=5.0, lead_time=2,
                         prior_alpha=0.15, prior_beta=9.85),
        "Q4": Primitive("Q4", "Vertical Integration Plant Build", cost=22.0, lead_time=6,
                         prior_alpha=0.3, prior_beta=9.7),
        "Q5": Primitive("Q5", "Safety Stock Buffer (60-day)", cost=3.0, lead_time=1,
                         prior_alpha=0.1, prior_beta=9.9),
    }


def build_strategies(lib: Dict[str, Primitive], audit: AuditTrail) -> Dict[str, Assembly]:
    a = Assembly("Strategy A: Low-Cost Single Source", leaf(lib["Q1"]), audit,
                 meta={"mitigation_factor": 0.0, "recovery_quarters": 3,
                       "margin_fraction_pre": 0.22, "margin_fraction_post": 0.22,
                       "holding_cost_per_q": 0.0, "disruption_fixed_cost": 11.0})
    b = Assembly("Strategy B: Resilient Dual-Source",
                 parallel(leaf(lib["Q2"]), leaf(lib["Q3"]), leaf(lib["Q5"])), audit,
                 meta={"mitigation_factor": 0.65, "recovery_quarters": 1,
                       "margin_fraction_pre": 0.19, "margin_fraction_post": 0.19,
                       "holding_cost_per_q": 0.3, "disruption_fixed_cost": 1.5})
    c = Assembly("Strategy C: Vertical Integration", leaf(lib["Q4"]), audit,
                 meta={"mitigation_factor": 0.5, "recovery_quarters": 2,
                       "margin_fraction_pre": 0.14, "margin_fraction_post": 0.27,
                       "holding_cost_per_q": 0.0, "disruption_fixed_cost": 5.0})
    return {"A": a, "B": b, "C": c}


def build_beliefs(lib: Dict[str, Primitive], audit: AuditTrail) -> Dict[str, BetaBelief]:
    return {pid: BetaBelief(f"{pid}_disruption_rate", p.prior_alpha, p.prior_beta, audit)
            for pid, p in lib.items()}


def build_demand_belief(audit: AuditTrail) -> NormalBelief:
    prior = NormalBelief("addressable_revenue_per_quarter_musd", mu=14.0, sigma=2.0, audit=audit)
    return prior.update(data=[15.2, 13.8, 14.6], obs_sigma=1.5)


def build_scenarios(demand_belief: NormalBelief, audit: AuditTrail) -> Dict[str, ScenarioSampler]:
    corr = np.array([[1.0, -0.3, 0.2],
                      [-0.3, 1.0, -0.1],
                      [0.2, -0.1, 1.0]])

    def sampler(demand_mu, demand_sigma, sev_low, sev_mode, sev_high,
                margin_low, margin_mode, margin_high):
        specs = [
            VarSpec("demand", "normal", {"mu": demand_mu, "sigma": demand_sigma}),
            VarSpec("disruption_severity", "triangular", {"low": sev_low, "mode": sev_mode, "high": sev_high}),
            VarSpec("margin_shock", "triangular", {"low": margin_low, "mode": margin_mode, "high": margin_high}),
        ]
        return ScenarioSampler(specs, correlation=corr, audit=audit)

    mu, sigma = demand_belief.mu, demand_belief.sigma
    return {
        "baseline": sampler(mu, sigma, 0.10, 0.30, 0.60, 0.85, 1.00, 1.15),
        "supplier_disruption_wave": sampler(mu, sigma, 0.30, 0.60, 0.95, 0.85, 1.00, 1.15),
        "tariff_margin_shock": sampler(mu, sigma, 0.10, 0.30, 0.60, 0.60, 0.80, 0.95),
        "demand_surge": sampler(mu * 1.3, sigma * 1.1, 0.15, 0.35, 0.65, 0.85, 1.00, 1.15),
    }


def state_transition_fn(assembly: Assembly, shocks: Dict[str, np.ndarray],
                         failure_draws: Dict[str, np.ndarray], rng: np.random.Generator,
                         n: int, trace_rows: Optional[List[int]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    demand = shocks["demand"]
    severity_raw = shocks["disruption_severity"]
    margin_shock = shocks["margin_shock"]

    total_capex = assembly.total_cost()
    base_lead = assembly.critical_path_lead_time()
    m = assembly.meta
    mitigation = m.get("mitigation_factor", 0.0)
    recovery_q = int(m.get("recovery_quarters", 1))
    margin_pre = m.get("margin_fraction_pre", 0.2)
    margin_post = m.get("margin_fraction_post", 0.2)
    holding_cost_q = m.get("holding_cost_per_q", 0.0)
    fixed_cost = m.get("disruption_fixed_cost", 0.0)

    lead_mult = np.clip(1.0 + 0.15 * rng.standard_normal(n), 0.5, 2.0)  # schedule slippage
    build_q = np.clip(np.ceil(max(base_lead, 1) * lead_mult), 1, QUARTERS).astype(int)
    severity_eff = np.clip(severity_raw * (1.0 - mitigation), 0.0, 0.95)  # (n,)

    # Per-quarter Bernoulli disruption trials, one hazard-rate draw per
    # primitive per simulation (epistemic) applied independently each quarter
    # (aleatoric) — risk compounds over the 10-quarter horizon.
    event_matrix = np.zeros((n, QUARTERS), dtype=bool)
    per_primitive_any = {}
    per_primitive_matrix = {}
    for pid, prob in failure_draws.items():
        pm = rng.random((n, QUARTERS)) < prob[:, None]
        per_primitive_any[pid] = pm.any(axis=1)
        per_primitive_matrix[pid] = pm
        event_matrix |= pm

    cash = np.zeros((n, QUARTERS))
    coverage = np.ones((n, QUARTERS))
    recovery_counter = np.zeros(n)
    for t in range(QUARTERS):
        fires_now = event_matrix[:, t]
        recovery_counter = np.where(fires_now, recovery_q, recovery_counter)
        impaired = recovery_counter > 0
        coverage[:, t] = np.where(impaired, 1.0 - severity_eff, 1.0)
        cash[:, t] -= fixed_cost * fires_now
        recovery_counter = np.maximum(recovery_counter - 1, 0)

    col = np.arange(QUARTERS)[None, :]
    build_mask = col < build_q[:, None]
    capex_per_q = total_capex / build_q
    cash -= build_mask.astype(float) * capex_per_q[:, None]

    margin_frac = np.where(build_mask, margin_pre, margin_post)
    revenue = demand[:, None] * coverage * margin_frac * margin_shock[:, None]
    holding = holding_cost_q * (~build_mask).astype(float)
    cash = cash + revenue - holding

    npv = npv_of(cash, DISCOUNT_RATE_ANNUAL / 4.0)
    trajectories = {"events": per_primitive_any, "has_failed": event_matrix.any(axis=1),
                     "build_quarters": build_q}

    if trace_rows:
        discount = (1.0 + DISCOUNT_RATE_ANNUAL / 4.0) ** np.arange(1, QUARTERS + 1)
        trace = {}
        for i in trace_rows:
            quarters = []
            cum = 0.0
            for t in range(QUARTERS):
                phase = "build" if build_mask[i, t] else "operate"
                c = float(cash[i, t])
                cum += c / discount[t]
                fired = [pid for pid, pm in per_primitive_matrix.items() if pm[i, t]]
                quarters.append({"t": t, "phase": phase, "cash": round(c, 3),
                                  "cumulative_npv": round(float(cum), 3),
                                  "health": round(float(coverage[i, t]), 3), "events": fired})
            trace[int(i)] = {"quarters": quarters}
        trajectories["trace"] = trace

    return npv, trajectories


def liquidity_decision_rule(liquidity_available: float):
    def rule(results):
        baseline = [r for r in results if r.scenario_name == "baseline"]
        affordable = [r for r in baseline if r.cvar95 >= -liquidity_available]
        if affordable:
            best = max(affordable, key=lambda r: r.utility)
            return best.strategy_name, (
                f"Working capital (${liquidity_available:.0f}M) can absorb {best.strategy_name}'s "
                f"CVaR95 tail loss (${best.cvar95:.1f}M); it has the highest regularized utility "
                f"among affordable options (${best.utility:.1f}M).")
        best = max(baseline, key=lambda r: r.cvar95)
        return best.strategy_name, (
            f"No strategy's tail loss fits within ${liquidity_available:.0f}M of working capital; "
            f"{best.strategy_name} has the least-bad downside (${best.cvar95:.1f}M).")
    return rule


def run(audit: AuditTrail, n_simulations: int = 10_000, liquidity_available: float = 8.0) -> Dict[str, Any]:
    lib = build_primitive_library()
    strategies = build_strategies(lib, audit)
    beliefs = build_beliefs(lib, audit)
    demand_post = build_demand_belief(audit)
    scenarios = build_scenarios(demand_post, audit)

    evaluator = RiskEvaluator(lambda_risk=0.5, lambda_assembly=1.5, audit=audit)
    explainer = Explainer(audit=audit)

    # Pattern 1: combinatorial generation + pruning, exercised explicitly here.
    from math import comb
    pipeline = AssemblyPipeline(audit=audit)
    max_k = 3
    n_generated = sum(comb(len(lib), k) for k in range(1, max_k + 1))
    generated = pipeline.generate(list(lib.values()), max_k=max_k, join=JoinOp.PARALLEL,
                                   budget=16.0, max_lead_time=6.0, max_assembly_index=3)

    tester = AssemblyConstrainedStressTester(evaluator, explainer, n_simulations, seed=7, audit=audit)
    results, explanations = tester.run(list(strategies.values()), beliefs, state_transition_fn, scenarios)

    optimizer = DualLoopAssemblyOptimizer(audit=audit)
    baseline_results = [r for r in results if r.scenario_name == "baseline"]
    selection = optimizer.optimize(baseline_results, decision_rule=liquidity_decision_rule(liquidity_available))

    execution_traces = {}
    for assembly in strategies.values():
        execution_traces[assembly.name] = {}
        for scen_name, sampler in scenarios.items():
            prior_audit, sampler.audit = sampler.audit, None
            engine = MonteCarloEngine(sampler, n_simulations, seed=7, audit=None)
            execution_traces[assembly.name][scen_name] = sample_execution_trace(
                engine, assembly, beliefs, state_transition_fn, scen_name)
            sampler.audit = prior_audit

    return {
        "domain": DOMAIN,
        "title": "Critical Component Sourcing & Supply-Chain Resilience",
        "primitives": {pid: p.to_dict() for pid, p in lib.items()},
        "strategies": {k: a.to_dict() for k, a in strategies.items()},
        "generated_candidates": {
            "n_generated": n_generated,
            "n_survived": len(generated),
            "survivors": [a.to_dict() for a in generated],
        },
        "beliefs": {"addressable_revenue": demand_post.to_dict(),
                    **{pid: b.to_dict() for pid, b in beliefs.items()}},
        "scenario_names": list(scenarios.keys()),
        "results": [r.to_dict() for r in results],
        "explanations": explanations,
        "selection": selection,
        "liquidity_available": liquidity_available,
        "execution_traces": execution_traces,
    }
