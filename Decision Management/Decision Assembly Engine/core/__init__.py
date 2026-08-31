"""
Reusable Decision Engine — core package.

Six canonical, domain-agnostic components (the "decision functors"):
  1. Primitive            — atomic action block
  2. Assembly              — DAG composition of primitives + Assembly Index (Ax)
  3. BayesianBeliefNode     — epistemic uncertainty / posterior updating
  4. MonteCarloEngine       — aleatory scenario sampling + propagation
  5. state_transition (fn)  — domain-supplied physics: (strategy, draw) -> trajectory
  6. RiskEvaluator          — VaR / CVaR / regularized utility / Pareto frontier

Plus two cross-cutting services every component writes through:
  - AuditTrail  — structured, hashed, replayable event log (traceability/auditability)
  - Explainer   — utility decomposition + narrative rationale (explainability)

And four reusable orchestration patterns built ONLY from the six components:
  - AssemblyPipeline
  - ActiveEpistemicGraph
  - AssemblyConstrainedStressTester
  - DualLoopAssemblyOptimizer

Every domain module in domains/ imports these unchanged and supplies only:
  a primitive library, a set of candidate Assemblies, a state_transition_fn,
  and a set of named scenarios. That is the proof of reusability.
"""
