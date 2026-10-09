"""
World Model actor registry: countries and companies, each with illustrative
baseline values for every state variable in ontology.py, plus a bilateral
trade-dependency matrix used to generate cross-country causal edges.

******************************************************************
IMPORTANT — ALL NUMBERS IN THIS FILE ARE ILLUSTRATIVE PLACEHOLDERS.
They are directionally plausible (informed by general, pre-2026
public knowledge of each country's broad economic structure) but are
NOT sourced, verified, or current real-world statistics, and must
never be cited or relied on as such. They exist only to let the
World Model's propagation mechanics run end-to-end on something
more concrete than all-zeros. Replacing them with real, sourced,
dated statistics (World Bank, IMF, OECD, UN, WHO, national
statistical offices) is the obvious next step before this model is
used for anything beyond illustrating the architecture.
******************************************************************
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from .ontology import STATE_VARIABLES


@dataclass
class Actor:
    id: str
    name: str
    kind: str          # "country" | "company"
    region: Optional[str]
    description: str
    baseline: Dict[str, float]  # state variable key -> illustrative baseline value

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "kind": self.kind, "region": self.region,
            "description": self.description, "baseline": self.baseline,
        }


# key order matches ontology.STATE_VARIABLES, grouped by sector for readability:
# social(4): inequality_gini, social_trust_index, migration_net_rate, unrest_index
# economic(4): gdp_growth_pct, inflation_pct, unemployment_pct, trade_balance_pct_gdp
# political(4): institutional_stability_index, policy_uncertainty_index, corruption_perception_index, approval_rating_pct
# industrial(4): industrial_output_growth_pct, capacity_utilization_pct, supply_chain_resilience_index, industrial_employment_pct
# healthcare(4): access_index, outcomes_index, cost_burden_pct_gdp, pandemic_preparedness_index
# education(4): attainment_index, stem_graduate_rate, spending_pct_gdp, digital_literacy_index
# transportation(4): infrastructure_quality_index, logistics_cost_pct_gdp, emissions_index, mobility_access_index
# agriculture(4): food_security_index, output_growth_pct, farmland_sustainability_index, export_dependence_pct
# energy(4): price_index, grid_reliability_index, import_dependence_pct, renewable_share_pct

_RAW_BASELINES: Dict[str, List[float]] = {
    "usa": [
        0.41, 62, 3.0, 28,
        2.1, 3.2, 3.9, -3.5,
        72, 38, 62, 48,
        1.8, 76, 58, 8.0,
        68, 74, 17.0, 61,
        70, 310, 5.0, 66,
        66, 10.5, 22, 58,
        72, 1.1, 70, 11,
        103, 82, 15, 23,
    ],
    "china": [
        0.47, 54, -0.3, 22,
        4.6, 1.8, 5.1, 1.8,
        58, 46, 50, 46,
        5.2, 79, 55, 18.0,
        60, 68, 5.0, 55,
        64, 190, 4.0, 72,
        60, 7.0, 32, 42,
        62, 2.6, 46, 2,
        98, 78, 21, 31,
    ],
    "germany": [
        0.31, 68, 4.2, 14,
        0.6, 2.6, 3.1, 6.8,
        80, 31, 76, 55,
        0.3, 81, 68, 5.5,
        76, 80, 11.8, 70,
        74, 240, 6.5, 74,
        68, 11.0, 15, 62,
        70, 0.5, 78, 4,
        118, 90, 64, 48,
    ],
    "india": [
        0.36, 48, -0.4, 36,
        6.3, 4.8, 7.2, -2.1,
        54, 58, 42, 40,
        5.8, 68, 42, 14.0,
        44, 46, 3.3, 38,
        52, 95, 4.2, 44,
        52, 14.0, 24, 36,
        54, 3.4, 40, 16,
        106, 58, 35, 22,
    ],
    "brazil": [
        0.52, 44, -0.5, 40,
        2.2, 4.5, 8.0, 1.2,
        48, 62, 48, 36,
        1.0, 72, 48, 10.5,
        56, 60, 4.0, 48,
        50, 60, 5.5, 46,
        46, 12.5, 30, 42,
        70, 2.8, 56, 38,
        101, 68, 10, 46,
    ],
    "nigeria": [
        0.35, 40, 1.8, 48,
        2.8, 19.5, 4.2, 3.0,
        34, 80, 28, 32,
        0.2, 74, 32, 3.5,
        36, 38, 3.5, 28,
        38, 20, 6.0, 30,
        36, 22.0, 48, 20,
        44, 3.2, 44, 72,
        108, 42, -35, 24,
    ],
    "japan": [
        0.33, 70, 1.2, 10,
        0.8, 1.9, 2.5, 2.4,
        82, 28, 72, 58,
        0.4, 78, 60, 4.0,
        78, 82, 11.0, 68,
        78, 180, 4.5, 72,
        72, 8.0, 18, 58,
        66, 0.2, 68, 2,
        115, 86, 88, 22,
    ],
}

_COUNTRY_META = {
    "usa": ("United States", "North America", "Large diversified service/tech-heavy economy; dollar reserve-currency role."),
    "china": ("China", "East Asia", "Large industrial-export-heavy economy in services transition."),
    "germany": ("Germany", "Europe", "Export/industrial-heavy economy, high energy-import dependence post-2022."),
    "india": ("India", "South Asia", "Large, fast-growing, services-and-agriculture-heavy economy."),
    "brazil": ("Brazil", "South America", "Commodity/agriculture-export-heavy economy."),
    "nigeria": ("Nigeria", "West Africa", "Energy(oil)-export-dependent economy, young and fast-urbanizing population."),
    "japan": ("Japan", "East Asia", "Aging, high-income, industrial-export economy, energy-import-dependent."),
}


def _build_countries() -> Dict[str, Actor]:
    keys = [v.key for v in STATE_VARIABLES]
    out = {}
    for cid, values in _RAW_BASELINES.items():
        name, region, desc = _COUNTRY_META[cid]
        assert len(values) == len(keys), f"{cid}: {len(values)} values vs {len(keys)} state variables"
        out[cid] = Actor(cid, name, "country", region, desc, dict(zip(keys, values)))
    return out


# --- Companies: deliberately fictional names (illustrative actors, not real
# corporations) so nothing here reads as a factual claim about a real company. ---
_COMPANY_META = {
    "helion_semi": ("Helion Semiconductors (fictional)", None,
                     "Illustrative multinational chip-fabrication company, headquartered with its primary fab in East Asia."),
    "meridian_agri": ("Meridian AgriCorp (fictional)", None,
                       "Illustrative multinational agricultural commodities trading and processing company."),
}
# Companies get a partial baseline: only the sectors they meaningfully act in/through.
_COMPANY_BASELINES = {
    "helion_semi": {
        "industrial.industrial_output_growth_pct": 6.0,
        "industrial.capacity_utilization_pct": 83.0,
        "industrial.supply_chain_resilience_index": 52.0,
        "industrial.industrial_employment_pct": None,  # not meaningful for a single company
        "economic.trade_balance_pct_gdp": None,
    },
    "meridian_agri": {
        "agriculture.output_growth_pct": 3.5,
        "agriculture.export_dependence_pct": 74.0,
        "agriculture.farmland_sustainability_index": 46.0,
        "agriculture.food_security_index": None,
    },
}


def _build_companies() -> Dict[str, Actor]:
    out = {}
    for cid, (name, region, desc) in _COMPANY_META.items():
        baseline = {k: v for k, v in _COMPANY_BASELINES[cid].items() if v is not None}
        out[cid] = Actor(cid, name, "company", region, desc, baseline)
    return out


COUNTRIES: Dict[str, Actor] = _build_countries()
COMPANIES: Dict[str, Actor] = _build_companies()
ACTORS: Dict[str, Actor] = {**COUNTRIES, **COMPANIES}


@dataclass(frozen=True)
class TradeLink:
    importer: str
    exporter: str
    channel: str              # "energy" | "agriculture" | "industrial"
    dependency_share: float   # illustrative: share of importer's channel consumption sourced from exporter
    rationale: str


# Illustrative bilateral trade-dependency links (NOT sourced trade-flow data —
# directionally plausible linkages used only to generate cross-country causal
# edges programmatically; see causal_graph.py).
TRADE_LINKS: List[TradeLink] = [
    TradeLink("germany", "nigeria", "energy", 0.18, "Illustrative: partial crude/LNG sourcing."),
    TradeLink("germany", "china", "industrial", 0.22, "Illustrative: intermediate-goods/components sourcing."),
    TradeLink("japan", "nigeria", "energy", 0.12, "Illustrative: partial crude sourcing."),
    TradeLink("japan", "china", "industrial", 0.19, "Illustrative: intermediate-goods sourcing."),
    TradeLink("china", "nigeria", "energy", 0.15, "Illustrative: crude-oil import share."),
    TradeLink("china", "brazil", "agriculture", 0.21, "Illustrative: soy/grain import share."),
    TradeLink("usa", "china", "industrial", 0.14, "Illustrative: manufactured-goods import share."),
    TradeLink("usa", "nigeria", "energy", 0.04, "Illustrative: minor crude import share."),
    TradeLink("india", "nigeria", "energy", 0.10, "Illustrative: crude-oil import share."),
    TradeLink("india", "china", "industrial", 0.16, "Illustrative: intermediate-goods import share."),
    TradeLink("brazil", "china", "industrial", 0.12, "Illustrative: manufactured-goods import share."),
    TradeLink("nigeria", "china", "industrial", 0.24, "Illustrative: manufactured/infrastructure-goods import share."),
    TradeLink("germany", "brazil", "agriculture", 0.09, "Illustrative: agricultural commodity import share."),
    TradeLink("china", "usa", "agriculture", 0.08, "Illustrative: grain import share."),
    TradeLink("japan", "india", "industrial", 0.05, "Illustrative: component import share."),
]


def actor_label(actor_id: str) -> str:
    return ACTORS[actor_id].name if actor_id in ACTORS else actor_id


def registry_to_dict() -> Dict:
    return {
        "countries": {k: a.to_dict() for k, a in COUNTRIES.items()},
        "companies": {k: a.to_dict() for k, a in COMPANIES.items()},
        "trade_links": [
            {"importer": t.importer, "exporter": t.exporter, "channel": t.channel,
             "dependency_share": t.dependency_share, "rationale": t.rationale}
            for t in TRADE_LINKS
        ],
        "disclaimer": (
            "All baseline values and trade-dependency shares in this registry are "
            "illustrative placeholders for demonstrating the model's architecture — "
            "directionally plausible but NOT sourced, verified, or current real-world "
            "statistics. Do not cite them as fact."
        ),
    }
