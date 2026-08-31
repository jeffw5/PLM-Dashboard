# Assembly Decision Engine

A working prototype of **reusable decision functors** for building complex
decision models: Assembly Theory (combinatorial structure + a complexity
regularizer), Bayesian inference (epistemic uncertainty / learning), and
Monte Carlo simulation (aleatory uncertainty / risk), composed into six
standard components and four orchestration patterns, then instantiated
**unchanged** across three unrelated domains to prove the reuse claim.

## Quick start

```bash
pip install numpy scipy --break-system-packages   # if not already installed
python3 run_all.py --n 10000
```

This runs all three domains and writes `output/results.json`,
`output/audit_trail.json`, and `output/audit_summary.json`. Open
`dashboard.html` (regenerate it with the snippet at the bottom of this file)
to explore the results interactively.

## Layout

```
core/                  the six reusable components + four patterns (domain-agnostic)
  primitives.py          Component 1+2 — Primitive, Assembly, Assembly Index (Ax)
  bayesian.py             Component 3 — BetaBelief, NormalBelief (conjugate updates)
  montecarlo.py            Component 4 — ScenarioSampler (Gaussian copula), MonteCarloEngine
  state.py                  Component 5 — npv_of() helper; the state equation itself is
                             supplied per-domain as `state_transition_fn`
  evaluator.py               Component 6 — RiskEvaluator (VaR/CVaR/utility), pareto_frontier()
  audit.py                    AuditTrail — hashed, replayable event log (traceability/auditability)
  explain.py                   Explainer — utility decomposition + tail-risk attribution + narrative
  patterns.py                   AssemblyPipeline, ActiveEpistemicGraph,
                                 AssemblyConstrainedStressTester, DualLoopAssemblyOptimizer

domains/               everything DOMAIN-SPECIFIC — imports core/ unchanged
  rd_portfolio.py         Enterprise AI infrastructure R&D portfolio ($50M/3yr capex decision)
  supply_chain.py          Critical-component sourcing & resilience (2.5yr sourcing decision)
  cyber_defense.py           Cybersecurity control investment (3yr security spend decision)

run_all.py              orchestrator — runs all three domains, writes output/*.json
dashboard_template.html  the dashboard shell (data placeholders __RESULTS_JSON__ / __AUDIT_JSON__)
```

## How the reuse actually works

Every `domains/*.py` module supplies exactly four things and nothing else:

1. a primitive library (`build_primitive_library`) — cost/lead-time/hazard-prior tuples
2. one or more `Assembly` objects (strategies) built from those primitives
3. Bayesian priors (`BetaBelief` / `NormalBelief`) for the domain's uncertain quantities
4. a `state_transition_fn(assembly, shocks, failure_draws, rng, n) -> (npv, trajectories)` —
   the domain's own "physics" (quarterly cash-flow mechanics)

Everything else — how Monte Carlo draws are generated and propagated, how
Assembly Index is computed, how Bayesian posteriors update, how CVaR/utility
is scored, how the Pareto frontier and stress-test sweep run, how audit
events are logged, how tail-risk attribution and narrative explanations are
produced — comes from `core/` and is imported **verbatim** by all three
domains. `domains/supply_chain.py` additionally exercises Pattern 1 (the
combinatorial `AssemblyPipeline` generator) instead of hand-specifying its
candidate strategies, to show the alternative entry point.

## Extending to a new domain

Copy the shape of `domains/cyber_defense.py`: define primitives, assemble
2-4 candidate strategies (`core.primitives.serial` / `parallel` / `leaf`),
define one or two `BetaBelief`/`NormalBelief` priors, write a
`state_transition_fn` that turns a strategy + a batch of Monte Carlo shocks
into a quarterly cash-flow array, define a handful of named stress
scenarios (`ScenarioSampler` + `VarSpec`), and write a `run(audit,
n_simulations, ...)` function that wires those into
`AssemblyConstrainedStressTester` and `DualLoopAssemblyOptimizer` (and
optionally `AssemblyPipeline` or `ActiveEpistemicGraph`). Nothing in
`core/` needs to change.

## Regenerating the dashboard

```bash
python3 -c "
import json
results = json.load(open('output/results.json'))
audit = json.load(open('output/audit_trail.json'))
results_json = json.dumps(results, default=str).replace('</script', '<\\/script')
audit_json = json.dumps(audit, default=str).replace('</script', '<\\/script')
tpl = open('dashboard_template.html').read()
tpl = tpl.replace('__RESULTS_JSON__', results_json).replace('__AUDIT_JSON__', audit_json)
open('dashboard.html', 'w').write(tpl)
"
```
