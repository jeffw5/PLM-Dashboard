"""
World Model ontology: the 9 sectors and their standardized state variables.

This is a DESIGN ARTIFACT, not a scientific claim. Choosing which ~4
variables represent "the state" of a sector is itself a modeling
simplification — a real national-accounts or public-health statistical
system tracks hundreds. These were chosen for breadth and for plausible
cross-sector/cross-country causal interaction, not because they are the
canonical or most important indicators for any sector.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, List


@dataclass(frozen=True)
class StateVariable:
    key: str              # unique across the whole ontology: "<sector>.<var>"
    sector: str
    label: str
    unit: str
    description: str
    higher_is_better: bool  # for display/coloring only — not a causal claim
    typical_move: float = 1.0  # illustrative "one meaningful move" scale in this
    # variable's own units — used only to let causal edges transmit a shock
    # between variables with different units via a normalized (standardized)
    # coefficient, the same convention path-analysis/SEM models use. Not a
    # measured statistic; a modeling convenience, documented as such.


SECTORS: Dict[str, Dict[str, str]] = {
    "social": {"label": "Social", "color": "#c97bb0"},
    "economic": {"label": "Economic", "color": "#e0a458"},
    "political": {"label": "Political", "color": "#6fa8d6"},
    "industrial": {"label": "Industrial", "color": "#5c6c7d"},
    "healthcare": {"label": "Healthcare", "color": "#5cb87a"},
    "education": {"label": "Education", "color": "#a690e0"},
    "transportation": {"label": "Transportation", "color": "#4bb3a3"},
    "agriculture": {"label": "Agriculture", "color": "#9dbf5c"},
    "energy": {"label": "Energy", "color": "#e2685f"},
}

STATE_VARIABLES: List[StateVariable] = [
    # --- Social ---
    StateVariable("social.inequality_gini", "social", "Income inequality (Gini)", "index 0-1",
                   "Standard Gini coefficient of income distribution.", False),
    StateVariable("social.social_trust_index", "social", "Social trust", "index 0-100",
                   "Composite survey-based measure of interpersonal and institutional trust.", True),
    StateVariable("social.migration_net_rate", "social", "Net migration rate", "per 1,000 pop.",
                   "Net migrants per 1,000 population per year (positive = net inflow).", None),
    StateVariable("social.unrest_index", "social", "Civil unrest index", "index 0-100",
                   "Composite frequency/intensity measure of protest and civil disorder events.", False),

    # --- Economic ---
    StateVariable("economic.gdp_growth_pct", "economic", "GDP growth", "% / year",
                   "Real GDP growth rate, year over year.", True),
    StateVariable("economic.inflation_pct", "economic", "Inflation", "% / year",
                   "Headline consumer price inflation, year over year.", False),
    StateVariable("economic.unemployment_pct", "economic", "Unemployment", "% of labor force",
                   "Unemployment rate, standardized definition.", False),
    StateVariable("economic.trade_balance_pct_gdp", "economic", "Trade balance", "% of GDP",
                   "Net exports as a share of GDP (positive = surplus).", True),

    # --- Political ---
    StateVariable("political.institutional_stability_index", "political", "Institutional stability", "index 0-100",
                   "Composite measure of government/institutional continuity and rule-of-law strength.", True),
    StateVariable("political.policy_uncertainty_index", "political", "Policy uncertainty", "index 0-100",
                   "News/market-based measure of uncertainty about future government policy.", False),
    StateVariable("political.corruption_perception_index", "political", "Corruption perception", "index 0-100",
                   "Higher = perceived cleaner (Transparency-International-style scaling).", True),
    StateVariable("political.approval_rating_pct", "political", "Executive approval", "% approving",
                   "Public approval rating of the sitting national executive.", None),

    # --- Industrial ---
    StateVariable("industrial.industrial_output_growth_pct", "industrial", "Industrial output growth", "% / year",
                   "Growth in industrial production index, year over year.", True),
    StateVariable("industrial.capacity_utilization_pct", "industrial", "Capacity utilization", "% of capacity",
                   "Share of installed industrial capacity actually in use.", True),
    StateVariable("industrial.supply_chain_resilience_index", "industrial", "Supply-chain resilience", "index 0-100",
                   "Composite measure of input-source diversification and buffer capacity.", True),
    StateVariable("industrial.industrial_employment_pct", "industrial", "Industrial employment share", "% of labor force",
                   "Share of total employment in industrial/manufacturing sectors.", None),

    # --- Healthcare ---
    StateVariable("healthcare.access_index", "healthcare", "Healthcare access", "index 0-100",
                   "Composite measure of coverage and physical/financial access to care.", True),
    StateVariable("healthcare.outcomes_index", "healthcare", "Health outcomes", "index 0-100",
                   "Composite measure of life expectancy, mortality, and morbidity outcomes.", True),
    StateVariable("healthcare.cost_burden_pct_gdp", "healthcare", "Healthcare cost burden", "% of GDP",
                   "Total health expenditure as a share of GDP.", False),
    StateVariable("healthcare.pandemic_preparedness_index", "healthcare", "Pandemic preparedness", "index 0-100",
                   "Composite surge-capacity and early-warning-system measure.", True),

    # --- Education ---
    StateVariable("education.attainment_index", "education", "Education attainment", "index 0-100",
                   "Composite measure of average educational attainment of the adult population.", True),
    StateVariable("education.stem_graduate_rate", "education", "STEM graduate rate", "per 100k pop./year",
                   "New STEM graduates per 100,000 population per year.", True),
    StateVariable("education.spending_pct_gdp", "education", "Education spending", "% of GDP",
                   "Public education expenditure as a share of GDP.", None),
    StateVariable("education.digital_literacy_index", "education", "Digital literacy", "index 0-100",
                   "Composite measure of population digital/technology skill levels.", True),

    # --- Transportation ---
    StateVariable("transportation.infrastructure_quality_index", "transportation", "Infrastructure quality", "index 0-100",
                   "Composite measure of road/rail/port/airport physical infrastructure quality.", True),
    StateVariable("transportation.logistics_cost_pct_gdp", "transportation", "Logistics cost", "% of GDP",
                   "Total freight/logistics cost as a share of GDP.", False),
    StateVariable("transportation.emissions_index", "transportation", "Transport emissions", "index 0-100",
                   "Composite transport-sector greenhouse-gas emissions intensity.", False),
    StateVariable("transportation.mobility_access_index", "transportation", "Mobility access", "index 0-100",
                   "Composite measure of population access to affordable transit/mobility options.", True),

    # --- Agriculture ---
    StateVariable("agriculture.food_security_index", "agriculture", "Food security", "index 0-100",
                   "Composite measure of food availability, access, and stability.", True),
    StateVariable("agriculture.output_growth_pct", "agriculture", "Agricultural output growth", "% / year",
                   "Growth in agricultural production index, year over year.", True),
    StateVariable("agriculture.farmland_sustainability_index", "agriculture", "Farmland sustainability", "index 0-100",
                   "Composite soil-health / water-stress / sustainable-practice measure.", True),
    StateVariable("agriculture.export_dependence_pct", "agriculture", "Agricultural export dependence", "% of ag. output",
                   "Share of agricultural output destined for export (higher = more exposed to trade shocks).", None),

    # --- Energy ---
    StateVariable("energy.price_index", "energy", "Energy price index", "index (100=baseline)",
                   "Composite domestic energy price level, indexed to a baseline year.", False),
    StateVariable("energy.grid_reliability_index", "energy", "Grid reliability", "index 0-100",
                   "Composite measure of electricity supply reliability (inverse of outage frequency/duration).", True),
    StateVariable("energy.import_dependence_pct", "energy", "Energy import dependence", "% of consumption",
                   "Share of total energy consumption met by imports.", None),
    StateVariable("energy.renewable_share_pct", "energy", "Renewable energy share", "% of generation",
                   "Share of electricity generation from renewable sources.", True),
]

# Illustrative "typical move" scale per variable, in its own units — see the
# StateVariable.typical_move docstring above. Variables not listed default to 1.0.
_TYPICAL_MOVE: Dict[str, float] = {
    "social.inequality_gini": 0.02, "social.social_trust_index": 5, "social.migration_net_rate": 1.0, "social.unrest_index": 10,
    "economic.gdp_growth_pct": 1.5, "economic.inflation_pct": 2.0, "economic.unemployment_pct": 1.0, "economic.trade_balance_pct_gdp": 1.5,
    "political.institutional_stability_index": 5, "political.policy_uncertainty_index": 15, "political.corruption_perception_index": 3, "political.approval_rating_pct": 5,
    "industrial.industrial_output_growth_pct": 2.0, "industrial.capacity_utilization_pct": 3, "industrial.supply_chain_resilience_index": 6, "industrial.industrial_employment_pct": 1.0,
    "healthcare.access_index": 4, "healthcare.outcomes_index": 3, "healthcare.cost_burden_pct_gdp": 0.8, "healthcare.pandemic_preparedness_index": 5,
    "education.attainment_index": 3, "education.stem_graduate_rate": 15, "education.spending_pct_gdp": 0.4, "education.digital_literacy_index": 4,
    "transportation.infrastructure_quality_index": 4, "transportation.logistics_cost_pct_gdp": 0.5, "transportation.emissions_index": 5, "transportation.mobility_access_index": 4,
    "agriculture.food_security_index": 4, "agriculture.output_growth_pct": 2.5, "agriculture.farmland_sustainability_index": 4, "agriculture.export_dependence_pct": 3,
    "energy.price_index": 8, "energy.grid_reliability_index": 3, "energy.import_dependence_pct": 3, "energy.renewable_share_pct": 2,
}
STATE_VARIABLES = [
    StateVariable(v.key, v.sector, v.label, v.unit, v.description, v.higher_is_better,
                  typical_move=_TYPICAL_MOVE.get(v.key, 1.0))
    for v in STATE_VARIABLES
]
STATE_VAR_BY_KEY: Dict[str, StateVariable] = {v.key: v for v in STATE_VARIABLES}


def sector_variables(sector: str) -> List[StateVariable]:
    return [v for v in STATE_VARIABLES if v.sector == sector]


def ontology_to_dict() -> Dict:
    return {
        "sectors": SECTORS,
        "state_variables": [
            {"key": v.key, "sector": v.sector, "label": v.label, "unit": v.unit,
             "description": v.description, "higher_is_better": v.higher_is_better,
             "typical_move": v.typical_move}
            for v in STATE_VARIABLES
        ],
    }
