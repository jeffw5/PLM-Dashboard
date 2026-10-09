"""
World Model causal graph: an EXPERT-ELICITED, explicitly-uncertain set of
causal mechanisms between state variables — not a statistically-fit or
validated causal structure. Every edge is a sourced hypothesis ("in general,
a rise in X plausibly raises/lowers Y, roughly this much, with this much
lag") represented as a NormalBelief over a standardized coefficient, so it
can be read like a regression-style path coefficient: target's normalized
shock += coefficient * source's normalized shock, where "normalized" means
expressed in units of that variable's `typical_move` (ontology.py).

Two layers:
  - SECTOR_MECHANISMS: within-country, domain-agnostic cause->effect
    hypotheses (the same mechanism is instantiated once per country, each
    instance getting its own independently-updatable belief object).
  - cross-country edges: generated programmatically from registry.TRADE_LINKS
    rather than hand-authored one at a time, so adding a country or a trade
    link automatically produces plausible spillover edges via a documented,
    reviewable rule rather than an ad hoc one-off.

THESE ARE MODELED HYPOTHESES, NOT ESTABLISHED FACTS. Real social, economic
and political causality is contested, context-dependent, and frequently
bidirectional/cyclical in ways a single coefficient cannot capture. Treat
every edge as "a reasonable analyst's starting prior," to be challenged,
sourced properly, and recalibrated against real data before being relied on.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List, Optional

from core.audit import AuditTrail
from core.bayesian import NormalBelief

from .ontology import STATE_VAR_BY_KEY
from .registry import COUNTRIES, TRADE_LINKS


@dataclass
class EdgeSpec:
    source_var: str
    target_var: str
    mean_coef: float
    sigma_coef: float
    lag: int
    rationale: str


# The expert-elicited mechanism library — the thing a domain expert should
# review, challenge, and re-source. Coefficients are standardized (see
# module docstring): roughly, "a one-typical-move change in the source
# produces, on average, mean_coef typical-moves of change in the target,
# ranging plausibly within +/- sigma_coef."
SECTOR_MECHANISMS: List[EdgeSpec] = [
    EdgeSpec("energy.price_index", "economic.inflation_pct", 0.35, 0.12, 1,
             "Energy costs feed directly into consumer price indices."),
    EdgeSpec("energy.price_index", "industrial.industrial_output_growth_pct", -0.25, 0.10, 1,
             "Higher energy costs raise input costs and depress industrial output growth."),
    EdgeSpec("economic.inflation_pct", "political.approval_rating_pct", -0.30, 0.12, 1,
             "Rising prices tend to erode public approval of the sitting executive."),
    EdgeSpec("economic.unemployment_pct", "social.unrest_index", 0.40, 0.15, 1,
             "Rising unemployment is a well-documented driver of civil unrest."),
    EdgeSpec("political.policy_uncertainty_index", "economic.gdp_growth_pct", -0.20, 0.08, 1,
             "Policy uncertainty depresses investment and near-term growth."),
    EdgeSpec("agriculture.output_growth_pct", "economic.trade_balance_pct_gdp", 0.18, 0.08, 0,
             "Agricultural export earnings flow fairly directly into the trade balance."),
    EdgeSpec("healthcare.cost_burden_pct_gdp", "economic.gdp_growth_pct", -0.12, 0.06, 2,
             "A rising health-cost burden can crowd out other productive investment over time."),
    EdgeSpec("education.spending_pct_gdp", "industrial.industrial_output_growth_pct", 0.15, 0.08, 3,
             "Education investment raises workforce skill and productivity, with a multi-year lag."),
    EdgeSpec("transportation.infrastructure_quality_index", "industrial.supply_chain_resilience_index", 0.30, 0.10, 1,
             "Better transport infrastructure reduces logistics fragility."),
    EdgeSpec("industrial.industrial_employment_pct", "social.inequality_gini", -0.20, 0.08, 1,
             "A broader industrial-employment base (vs. high-skill-only growth) tends to compress income inequality."),
    EdgeSpec("energy.renewable_share_pct", "transportation.emissions_index", -0.25, 0.10, 2,
             "A cleaner generation mix lowers transport-sector emissions intensity as electrification spreads."),
    EdgeSpec("social.unrest_index", "political.institutional_stability_index", -0.30, 0.12, 0,
             "Sustained unrest directly strains institutional stability."),
    EdgeSpec("political.institutional_stability_index", "economic.gdp_growth_pct", 0.22, 0.09, 1,
             "Institutional stability supports investment and growth."),
    EdgeSpec("economic.gdp_growth_pct", "political.approval_rating_pct", 0.25, 0.10, 1,
             "Growth tends to support incumbent approval."),
    EdgeSpec("energy.price_index", "agriculture.output_growth_pct", -0.15, 0.07, 1,
             "Energy costs (fertilizer, fuel, irrigation) affect agricultural production costs and output."),
    EdgeSpec("energy.price_index", "transportation.logistics_cost_pct_gdp", 0.30, 0.10, 0,
             "Fuel costs flow fairly directly into logistics/freight costs."),
    EdgeSpec("industrial.supply_chain_resilience_index", "economic.gdp_growth_pct", 0.18, 0.08, 1,
             "Resilient supply chains reduce output volatility and support growth."),
    EdgeSpec("healthcare.outcomes_index", "economic.gdp_growth_pct", 0.12, 0.06, 2,
             "A healthier workforce supports long-run productivity."),
    EdgeSpec("agriculture.food_security_index", "social.unrest_index", -0.28, 0.11, 0,
             "Food insecurity is a well-documented driver of unrest."),
    EdgeSpec("political.corruption_perception_index", "economic.gdp_growth_pct", 0.10, 0.05, 2,
             "Lower perceived corruption tends to support investment climate and growth over time."),
]

_CHANNEL_MECHANISM = {
    "energy": ("energy.price_index", "energy.price_index", 0.80,
               "Price transmission: a shock to the exporter's energy price index passes through to the "
               "importer's own domestic energy price index, scaled by how import-dependent the importer is."),
    "agriculture": ("agriculture.output_growth_pct", "agriculture.food_security_index", 0.60,
                     "An output shock in the exporter's agricultural sector transmits to the importer's food "
                     "security, scaled by how import-dependent the importer is on that exporter."),
    "industrial": ("industrial.industrial_output_growth_pct", "industrial.supply_chain_resilience_index", 0.70,
                    "An output shock in the exporter's industrial sector transmits to the importer's supply-chain "
                    "resilience, scaled by how import-dependent the importer is on that exporter."),
}


@dataclass
class CausalEdge:
    id: str
    kind: str                 # "within_country" | "cross_country"
    source_actor: str
    source_var: str
    target_actor: str
    target_var: str
    belief: NormalBelief      # standardized coefficient belief
    lag: int
    rationale: str

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "kind": self.kind,
            "source_actor": self.source_actor, "source_var": self.source_var,
            "target_actor": self.target_actor, "target_var": self.target_var,
            "belief": self.belief.to_dict(), "lag": self.lag, "rationale": self.rationale,
        }


def build_causal_graph(audit: Optional[AuditTrail] = None) -> List[CausalEdge]:
    edges: List[CausalEdge] = []

    # Within-country: instantiate every mechanism once per country, each
    # getting its own belief object (same prior to start, independently
    # updatable per country as real country-specific evidence arrives).
    for country_id in COUNTRIES:
        for i, spec in enumerate(SECTOR_MECHANISMS):
            belief = NormalBelief(f"{country_id}:{spec.source_var}->{spec.target_var}",
                                   spec.mean_coef, spec.sigma_coef, audit=audit)
            edges.append(CausalEdge(
                id=f"wc:{country_id}:{i}", kind="within_country",
                source_actor=country_id, source_var=spec.source_var,
                target_actor=country_id, target_var=spec.target_var,
                belief=belief, lag=spec.lag, rationale=spec.rationale,
            ))

    # Cross-country: generated from the trade-dependency registry.
    for j, link in enumerate(TRADE_LINKS):
        source_var, target_var, base_coef, rationale = _CHANNEL_MECHANISM[link.channel]
        mean_coef = round(base_coef * link.dependency_share, 4)
        sigma_coef = round(0.05 + 0.20 * link.dependency_share, 4)
        belief = NormalBelief(f"{link.exporter}->{link.importer}:{link.channel}", mean_coef, sigma_coef, audit=audit)
        edges.append(CausalEdge(
            id=f"cc:{j}", kind="cross_country",
            source_actor=link.exporter, source_var=source_var,
            target_actor=link.importer, target_var=target_var,
            belief=belief, lag=1,
            rationale=f"{rationale} (dependency share: {link.dependency_share:.0%} — {link.rationale})",
        ))

    if audit:
        audit.log("CausalGraph", "built",
                   inputs={"n_mechanisms": len(SECTOR_MECHANISMS), "n_countries": len(COUNTRIES),
                           "n_trade_links": len(TRADE_LINKS)},
                   outputs={"n_within_country_edges": len(COUNTRIES) * len(SECTOR_MECHANISMS),
                            "n_cross_country_edges": len(TRADE_LINKS), "n_total_edges": len(edges)})
    return edges


def edges_from(edges: List[CausalEdge], actor: str, var: str) -> List[CausalEdge]:
    return [e for e in edges if e.source_actor == actor and e.source_var == var]


def mechanisms_to_dict() -> List[Dict]:
    """The 20 expert-elicited mechanism templates, for display (not instantiated per-country)."""
    return [
        {"source_var": s.source_var, "target_var": s.target_var, "mean_coef": s.mean_coef,
         "sigma_coef": s.sigma_coef, "lag": s.lag, "rationale": s.rationale,
         "source_label": STATE_VAR_BY_KEY[s.source_var].label, "target_label": STATE_VAR_BY_KEY[s.target_var].label}
        for s in SECTOR_MECHANISMS
    ]
