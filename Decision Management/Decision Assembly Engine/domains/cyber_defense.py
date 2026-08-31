"""
Domain 3 — Cybersecurity Control Investment.

A mid-market enterprise must decide how to invest in security controls to
protect ~$18M/quarter of digital operations over a 3-year (12-quarter)
horizon:
  A. Patch & Train          (vulnerability patch automation + security training)
  B. Zero-Trust Build-out    (zero-trust network rollout + patching + cyber insurance)
  C. Outsourced SOC          (managed detection & response + cyber insurance)

As with domains/supply_chain.py, every core/ class is reused UNCHANGED — the
economic "shape" (coverage degrades for a recovery window after an event,
a one-time incident cost fires, capex is spread over a build phase) is also
reused deliberately, to make the point that the same functor composition
generalizes to a domain (breach risk) that looks nothing like capex
portfolio selection or supply-chain sourcing on the surface, by simply
re-parameterizing what "coverage," "event," and "cost" mean.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional, Tuple

import numpy as np

from core.audit import AuditTrail
from core.bayesian import BetaBelief, NormalBelief
from core.evaluator import RiskEvaluator
from core.explain import Explainer
from core.montecarlo import MonteCarloEngine, ScenarioSampler, VarSpec, sample_execution_trace
from core.patterns import AssemblyConstrainedStressTester, DualLoopAssemblyOptimizer
from core.primitives import Assembly, Primitive, leaf, parallel
from core.state import npv_of

DOMAIN = "cyber_defense"
QUARTERS = 12
DISCOUNT_RATE_ANNUAL = 0.09


def build_primitive_library() -> Dict[str, Primitive]:
    # prior_alpha/prior_beta = per-quarter probability that THIS control's own
    # residual gap is the vector a breach gets through (posterior updated as
    # incident/near-miss data accumulates, same conjugate-Beta mechanic used
    # in the other two domains).
    return {
        "S1": Primitive("S1", "Vulnerability Patch Automation", cost=1.5, lead_time=1,
                         prior_alpha=0.4, prior_beta=9.6),
        "S2": Primitive("S2", "Zero-Trust Network Rollout", cost=9.0, lead_time=5,
                         prior_alpha=0.3, prior_beta=9.7),
        "S3": Primitive("S3", "Outsourced SOC Contract (3yr)", cost=4.0, lead_time=2,
                         prior_alpha=0.15, prior_beta=9.85),
        "S4": Primitive("S4", "Employee Security Training", cost=1.0, lead_time=1,
                         prior_alpha=0.5, prior_beta=9.5),
        "S5": Primitive("S5", "Cyber Insurance Policy (3yr)", cost=3.0, lead_time=1,
                         prior_alpha=0.05, prior_beta=9.95),
        # Synthetic reference primitive used only to build the "do nothing"
        # comparator below — not a candidate control, just an unmanaged
        # baseline hazard rate to quantify each strategy's ROI against.
        "D0": Primitive("D0", "No Investment (unmanaged baseline)", cost=0.0, lead_time=0,
                         prior_alpha=1.2, prior_beta=8.8),
    }


def build_strategies(lib: Dict[str, Primitive], audit: AuditTrail) -> Dict[str, Assembly]:
    a = Assembly("Strategy A: Patch & Train",
                 parallel(leaf(lib["S1"]), leaf(lib["S4"])), audit,
                 meta={"mitigation_factor": 0.20, "recovery_quarters": 3,
                       "opex_per_q": 0.10, "fixed_incident_cost": 3.0})
    b = Assembly("Strategy B: Zero-Trust Build-out",
                 parallel(leaf(lib["S2"]), leaf(lib["S1"]), leaf(lib["S5"])), audit,
                 meta={"mitigation_factor": 0.55, "recovery_quarters": 2,
                       "opex_per_q": 0.35, "fixed_incident_cost": 2.0})
    c = Assembly("Strategy C: Outsourced SOC",
                 parallel(leaf(lib["S3"]), leaf(lib["S5"])), audit,
                 meta={"mitigation_factor": 0.70, "recovery_quarters": 1,
                       "opex_per_q": 0.90, "fixed_incident_cost": 1.0})
    do_nothing = Assembly("Baseline: No Investment", leaf(lib["D0"]), audit,
                           meta={"mitigation_factor": 0.0, "recovery_quarters": 4,
                                 "opex_per_q": 0.0, "fixed_incident_cost": 6.0})
    return {"A": a, "B": b, "C": c, "DO_NOTHING": do_nothing}


def build_beliefs(lib: Dict[str, Primitive], audit: AuditTrail) -> Dict[str, BetaBelief]:
    return {pid: BetaBelief(f"{pid}_breach_vector_rate", p.prior_alpha, p.prior_beta, audit)
            for pid, p in lib.items()}


def build_value_belief(audit: AuditTrail) -> NormalBelief:
    prior = NormalBelief("digital_ops_value_per_quarter_musd", mu=18.0, sigma=2.5, audit=audit)
    return prior.update(data=[19.1, 17.4, 18.6], obs_sigma=2.0)


def build_scenarios(value_belief: NormalBelief, audit: AuditTrail) -> Dict[str, ScenarioSampler]:
    corr = np.array([[1.0, -0.2, 0.1, 0.0],
                      [-0.2, 1.0, 0.3, 0.0],
                      [0.1, 0.3, 1.0, 0.2],
                      [0.0, 0.0, 0.2, 1.0]])

    def sampler(value_mu, value_sigma, sev_low, sev_mode, sev_high,
                reg_low, reg_mode, reg_high, opex_low, opex_mode, opex_high):
        specs = [
            VarSpec("digital_ops_value", "normal", {"mu": value_mu, "sigma": value_sigma}),
            VarSpec("breach_severity", "triangular", {"low": sev_low, "mode": sev_mode, "high": sev_high}),
            VarSpec("regulatory_shock", "triangular", {"low": reg_low, "mode": reg_mode, "high": reg_high}),
            VarSpec("opex_multiplier", "triangular", {"low": opex_low, "mode": opex_mode, "high": opex_high}),
        ]
        return ScenarioSampler(specs, correlation=corr, audit=audit)

    mu, sigma = value_belief.mu, value_belief.sigma
    return {
        "baseline": sampler(mu, sigma, 0.15, 0.35, 0.70, 0.85, 1.00, 1.25, 0.90, 1.00, 1.15),
        "ransomware_wave": sampler(mu, sigma, 0.35, 0.60, 0.95, 1.00, 1.30, 1.80, 0.90, 1.00, 1.15),
        "regulatory_tightening": sampler(mu, sigma, 0.15, 0.35, 0.70, 1.20, 1.60, 2.20, 0.90, 1.00, 1.15),
        "security_talent_shortage": sampler(mu, sigma, 0.15, 0.35, 0.70, 0.85, 1.00, 1.25, 1.10, 1.35, 1.70),
    }


def state_transition_fn(assembly: Assembly, shocks: Dict[str, np.ndarray],
                         failure_draws: Dict[str, np.ndarray], rng: np.random.Generator,
                         n: int, trace_rows: Optional[List[int]] = None) -> Tuple[np.ndarray, Dict[str, Any]]:
    value = shocks["digital_ops_value"]
    severity_raw = shocks["breach_severity"]
    reg_shock = shocks["regulatory_shock"]
    opex_mult = shocks["opex_multiplier"]

    total_capex = assembly.total_cost()
    base_lead = assembly.critical_path_lead_time()
    m = assembly.meta
    mitigation = m.get("mitigation_factor", 0.0)
    recovery_q = int(m.get("recovery_quarters", 1))
    opex_per_q = m.get("opex_per_q", 0.0)
    fixed_cost = m.get("fixed_incident_cost", 0.0)

    lead_mult = np.clip(1.0 + 0.15 * rng.standard_normal(n), 0.5, 2.0)
    build_q = np.clip(np.ceil(max(base_lead, 1) * lead_mult), 1, QUARTERS).astype(int)
    severity_eff = np.clip(severity_raw * (1.0 - mitigation), 0.0, 0.95)  # (n,)

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
        cash[:, t] -= fixed_cost * reg_shock * fires_now  # incident response + regulatory fines
        recovery_counter = np.maximum(recovery_counter - 1, 0)

    col = np.arange(QUARTERS)[None, :]
    build_mask = col < build_q[:, None]
    capex_per_q = total_capex / build_q
    cash -= build_mask.astype(float) * capex_per_q[:, None]

    protected_value = value[:, None] * coverage      # digital operations value preserved
    opex = opex_per_q * opex_mult[:, None] * np.ones((n, QUARTERS))
    cash = cash + protected_value - opex

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


def risk_appetite_decision_rule(min_utility_gap_to_justify_complexity: float = 5.0):
    """Loop 2: prefer the simplest (lowest Assembly Index) strategy unless a
    more complex one clears the frontier by more than a materiality
    threshold — an explicit Occam's-razor decision rule distinct from the
    liquidity-constraint rules used in the other two domains."""
    def rule(results):
        baseline = sorted([r for r in results if r.scenario_name == "baseline"],
                           key=lambda r: r.assembly_index)
        best = baseline[0]
        for r in baseline[1:]:
            if r.utility > best.utility + min_utility_gap_to_justify_complexity:
                best = r
        return best.strategy_name, (
            f"{best.strategy_name} is selected under an Occam's-razor rule: a more complex "
            f"strategy is only preferred if it beats the simplest option's utility by more than "
            f"${min_utility_gap_to_justify_complexity:.0f}M; {best.strategy_name} does "
            f"(utility ${best.utility:.1f}M).")
    return rule


def run(audit: AuditTrail, n_simulations: int = 10_000) -> Dict[str, Any]:
    lib = build_primitive_library()
    strategies = build_strategies(lib, audit)
    beliefs = build_beliefs(lib, audit)
    value_post = build_value_belief(audit)
    scenarios = build_scenarios(value_post, audit)

    evaluator = RiskEvaluator(lambda_risk=0.5, lambda_assembly=2.0, audit=audit)
    explainer = Explainer(audit=audit)

    candidates = {k: v for k, v in strategies.items() if k != "DO_NOTHING"}
    tester = AssemblyConstrainedStressTester(evaluator, explainer, n_simulations, seed=99, audit=audit)
    results, explanations = tester.run(list(candidates.values()), beliefs, state_transition_fn, scenarios)

    optimizer = DualLoopAssemblyOptimizer(audit=audit)
    baseline_results = [r for r in results if r.scenario_name == "baseline"]
    selection = optimizer.optimize(baseline_results, decision_rule=risk_appetite_decision_rule(5.0))

    # ROI reference: how much value each strategy protects vs. an unmanaged
    # "do nothing" baseline, evaluated once under the baseline scenario.
    dn_engine = MonteCarloEngine(scenarios["baseline"], n_simulations, seed=99, audit=audit)
    dn_mc = dn_engine.run(strategies["DO_NOTHING"], beliefs, state_transition_fn, "baseline")
    dn_eval = evaluator.evaluate(dn_mc, strategies["DO_NOTHING"].total_cost(),
                                  strategies["DO_NOTHING"].assembly_index())
    incremental_value = {
        r.strategy_name: round(r.mean_npv - dn_eval.mean_npv, 2)
        for r in baseline_results
    }

    execution_traces = {}
    for assembly in candidates.values():
        execution_traces[assembly.name] = {}
        for scen_name, sampler in scenarios.items():
            prior_audit, sampler.audit = sampler.audit, None
            engine = MonteCarloEngine(sampler, n_simulations, seed=99, audit=None)
            execution_traces[assembly.name][scen_name] = sample_execution_trace(
                engine, assembly, beliefs, state_transition_fn, scen_name)
            sampler.audit = prior_audit

    return {
        "domain": DOMAIN,
        "title": "Cybersecurity Control Investment",
        "primitives": {pid: p.to_dict() for pid, p in lib.items() if pid != "D0"},
        "strategies": {k: a.to_dict() for k, a in candidates.items()},
        "beliefs": {"digital_ops_value": value_post.to_dict(),
                    **{pid: b.to_dict() for pid, b in beliefs.items() if pid != "D0"}},
        "scenario_names": list(scenarios.keys()),
        "results": [r.to_dict() for r in results],
        "explanations": explanations,
        "selection": selection,
        "do_nothing_baseline": dn_eval.to_dict(),
        "incremental_value_vs_do_nothing": incremental_value,
        "execution_traces": execution_traces,
    }
