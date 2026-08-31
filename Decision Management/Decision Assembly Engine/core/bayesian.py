"""
Component 3: Bayesian Belief Node — the epistemic-uncertainty layer.

Wraps a parametric belief (Beta or Normal, the two conjugate families used
across all three demo domains) and updates it from evidence. Every update
is written to the AuditTrail with the prior, the evidence, and the exact
posterior — so any downstream number can be traced back to "what we believed
and why it changed."
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional, Sequence

import numpy as np

from .audit import AuditTrail


@dataclass
class BetaBelief:
    """Belief over a probability (failure rate, breach rate, disruption rate, ...)."""
    name: str
    alpha: float
    beta: float
    audit: Optional[AuditTrail] = None

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    def update(self, observed_failures: int, observed_successes: int) -> "BetaBelief":
        prior = (self.alpha, self.beta)
        post = BetaBelief(self.name, self.alpha + observed_failures,
                           self.beta + observed_successes, self.audit)
        if self.audit:
            self.audit.log(
                "BayesianBeliefNode", "beta_binomial_update",
                inputs={"name": self.name, "prior_alpha": prior[0], "prior_beta": prior[1],
                        "observed_failures": observed_failures, "observed_successes": observed_successes},
                outputs={"posterior_alpha": post.alpha, "posterior_beta": post.beta,
                         "prior_mean": prior[0] / sum(prior), "posterior_mean": post.mean},
            )
        return post

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return rng.beta(self.alpha, self.beta, size=n)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "alpha": self.alpha, "beta": self.beta, "mean": round(self.mean, 4)}


@dataclass
class NormalBelief:
    """Belief over a continuous latent quantity (demand, throughput, ...)."""
    name: str
    mu: float
    sigma: float
    audit: Optional[AuditTrail] = None

    def update(self, data: Sequence[float], obs_sigma: float) -> "NormalBelief":
        data = np.asarray(data, dtype=float)
        n = len(data)
        var0, varv = self.sigma ** 2, obs_sigma ** 2
        post_var = 1.0 / (1.0 / var0 + n / varv)
        post_mu = post_var * (self.mu / var0 + data.sum() / varv)
        post = NormalBelief(self.name, post_mu, float(np.sqrt(post_var)), self.audit)
        if self.audit:
            self.audit.log(
                "BayesianBeliefNode", "normal_normal_update",
                inputs={"name": self.name, "prior_mu": self.mu, "prior_sigma": self.sigma,
                        "obs_sigma": obs_sigma, "data": data.tolist()},
                outputs={"posterior_mu": post.mu, "posterior_sigma": post.sigma},
            )
        return post

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return rng.normal(self.mu, self.sigma, size=n)

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "mu": round(self.mu, 4), "sigma": round(self.sigma, 4)}
