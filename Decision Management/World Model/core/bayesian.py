"""
Component: BayesianBeliefNode — conjugate Bayesian beliefs for the
epistemic-uncertainty layer. BetaBelief (Beta-Binomial) represents a
bounded rate/probability (a hazard rate, or here, a causal edge's
believed strength as a fraction); NormalBelief (Normal-Normal)
represents an unbounded continuous quantity. Both expose closed-form
posterior updates and a .sample() method the Monte Carlo layer draws from.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Optional

import numpy as np

from .audit import AuditTrail


@dataclass
class BetaBelief:
    name: str
    alpha: float
    beta: float
    audit: Optional[AuditTrail] = None

    @property
    def mean(self) -> float:
        return self.alpha / (self.alpha + self.beta)

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return rng.beta(self.alpha, self.beta, size=n)

    def update(self, successes: float, failures: float) -> "BetaBelief":
        new = BetaBelief(self.name, self.alpha + successes, self.beta + failures, self.audit)
        if self.audit:
            self.audit.log("BayesianBeliefNode", "beta_update",
                            inputs={"name": self.name, "prior_alpha": self.alpha, "prior_beta": self.beta,
                                    "successes": successes, "failures": failures},
                            outputs={"posterior_alpha": new.alpha, "posterior_beta": new.beta,
                                     "posterior_mean": new.mean})
        return new

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "alpha": round(self.alpha, 4), "beta": round(self.beta, 4),
                "mean": round(self.mean, 4)}


@dataclass
class NormalBelief:
    name: str
    mu: float
    sigma: float
    audit: Optional[AuditTrail] = None

    def sample(self, n: int, rng: np.random.Generator) -> np.ndarray:
        return rng.normal(self.mu, self.sigma, size=n)

    def update(self, observed_mean: float, observed_sigma: float, n_obs: int) -> "NormalBelief":
        prior_precision = 1.0 / (self.sigma ** 2)
        obs_precision = n_obs / (observed_sigma ** 2)
        post_precision = prior_precision + obs_precision
        post_mu = (self.mu * prior_precision + observed_mean * obs_precision) / post_precision
        post_sigma = (1.0 / post_precision) ** 0.5
        new = NormalBelief(self.name, post_mu, post_sigma, self.audit)
        if self.audit:
            self.audit.log("BayesianBeliefNode", "normal_update",
                            inputs={"name": self.name, "prior_mu": self.mu, "prior_sigma": self.sigma,
                                    "observed_mean": observed_mean, "observed_sigma": observed_sigma, "n_obs": n_obs},
                            outputs={"posterior_mu": new.mu, "posterior_sigma": new.sigma})
        return new

    def to_dict(self) -> Dict[str, Any]:
        return {"name": self.name, "mu": round(self.mu, 4), "sigma": round(self.sigma, 4)}
