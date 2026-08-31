"""
Component 5: State Transition & Impact Transfer.

This module holds only the generic, domain-agnostic mechanics every domain
reuses (discounting a cash-flow trajectory to NPV). The actual state
equation S[t+1] = f(S[t], A[t], shock[t]) is necessarily domain-specific
(it's the "physics" of enterprise cash, supply-chain inventory, or breach
loss) — each domains/*.py module supplies its own state_transition_fn with
this exact signature so the MonteCarloEngine can call it polymorphically:

    def state_transition_fn(assembly, shocks, failure_draws, n) -> (npv, trajectories)
"""
from __future__ import annotations

import numpy as np


def npv_of(cashflows: np.ndarray, periodic_rate: float) -> np.ndarray:
    """
    Vectorized NPV. cashflows: shape (n_sims, n_periods). Returns shape (n_sims,).
    """
    periods = np.arange(1, cashflows.shape[-1] + 1)
    discount = (1.0 + periodic_rate) ** periods
    return np.sum(cashflows / discount, axis=-1)
