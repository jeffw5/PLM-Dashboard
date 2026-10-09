"""
World Model decision library: a small set of HYPOTHETICAL institutional
decisions used to exercise the causal graph end-to-end.

******************************************************************
EVERY DECISION IN THIS FILE IS FICTIONAL / HYPOTHETICAL. None of them
describe a real announced policy, law, or corporate action. Country and
company names are used only to anchor the decision to a registry actor
with plausible structural characteristics (e.g. "an energy exporter,"
"a chip-fab operator") — they are not claims about what that government
or company has done, is doing, or is considering. The company, "Helion
Semiconductors," is explicitly fictional (see registry.py).
******************************************************************

Each Decision is represented the same way the original Assembly Decision
Engine represents a strategy: an Assembly of Primitives (the concrete
action steps an institution would actually have to take, with their own
cost/lead-time/Assembly-Index), PLUS one or more OriginShocks — the
state-variable deltas that the graph-propagation engine (propagation.py)
uses as the seed for walking the causal graph outward.

A company decision's shock does not live on any causal-graph edge
directly (the graph only models country<->country spillover, built from
TRADE_LINKS). Instead it is routed through a `proxy_route`: an explicit,
documented, and necessarily approximate rule saying "treat this company's
shock as if it were this fraction of its home country's corresponding
sector shock." That attenuation factor is itself a modeling choice, not
a measured fact, and is called out as such wherever it is used.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from core.audit import AuditTrail
from core.primitives import Assembly, Primitive


@dataclass(frozen=True)
class OriginShock:
    actor: str
    var: str
    delta: float          # change in the variable's own native units
    rationale: str


@dataclass(frozen=True)
class ProxyRoute:
    home_country: str
    scope: float           # illustrative fraction of the home country's sector this actor represents
    rationale: str


@dataclass
class Decision:
    id: str
    name: str
    actor: str
    actor_kind: str        # "country" | "company"
    description: str
    assembly: Assembly
    origin_shocks: List[OriginShock]
    proxy_route: Optional[ProxyRoute] = None
    status: str = "HYPOTHETICAL"

    def to_dict(self) -> Dict:
        return {
            "id": self.id, "name": self.name, "actor": self.actor, "actor_kind": self.actor_kind,
            "status": self.status, "description": self.description,
            "assembly": self.assembly.to_dict(),
            "origin_shocks": [{"actor": s.actor, "var": s.var, "delta": s.delta, "rationale": s.rationale}
                               for s in self.origin_shocks],
            "proxy_route": ({"home_country": self.proxy_route.home_country, "scope": self.proxy_route.scope,
                              "rationale": self.proxy_route.rationale} if self.proxy_route else None),
        }


def build_decisions(audit: Optional[AuditTrail] = None) -> List[Decision]:
    decisions: List[Decision] = []

    # ------------------------------------------------------------------
    # Decision 1 — Nigeria (country, energy/political actor): HYPOTHETICAL
    # crude-energy export levy. Chosen to exercise the cross-country energy
    # trade-link edges: Nigeria is the exporter in 5 of the 15 TRADE_LINKS
    # (to Germany, Japan, China, USA, and India), so this one decision's
    # shock should ripple into every one of those importers' domestic
    # energy price index via build_causal_graph's cross_country edges.
    # ------------------------------------------------------------------
    nigeria_primitives = [
        Primitive("NGA-P1", "Draft levy framework & legal basis", cost=4.0, lead_time=2,
                  prior_failure_rate=0.10, tags=("regulatory",)),
        Primitive("NGA-P2", "Legislative approval", cost=2.0, lead_time=3,
                  prior_failure_rate=0.25, tags=("political",)),
        Primitive("NGA-P3", "Customs & enforcement rollout", cost=6.0, lead_time=2,
                  prior_failure_rate=0.15, tags=("operational",)),
    ]
    nigeria_assembly = Assembly("Nigeria: HYPOTHETICAL crude-export levy", nigeria_primitives, audit=audit)
    decisions.append(Decision(
        id="dec:nigeria_export_levy",
        name="Nigeria — HYPOTHETICAL 15% crude-energy export levy",
        actor="nigeria", actor_kind="country",
        description=(
            "HYPOTHETICAL scenario: Nigeria's government imposes a new 15% levy on crude-energy exports, "
            "intended to raise fiscal revenue. This is a fictional illustrative scenario, not a real "
            "announced policy. Modeled origin effect: a rise in Nigeria's domestic energy price index "
            "(cost pass-through plus reduced production incentive at the margin)."
        ),
        assembly=nigeria_assembly,
        origin_shocks=[
            OriginShock("nigeria", "energy.price_index", 14.0,
                        "Illustrative: levy cost passes through to domestic energy pricing and dampens "
                        "production incentives at the margin."),
        ],
    ))

    # ------------------------------------------------------------------
    # Decision 2 — Helion Semiconductors (company, industrial actor):
    # HYPOTHETICAL fab relocation out of its current East-Asia site.
    # Chosen to exercise the company->home-country proxy route and the
    # cross-country industrial trade-link edges where China is the
    # exporter (to Germany, Japan, India, Brazil, Nigeria).
    # ------------------------------------------------------------------
    helion_primitives = [
        Primitive("HEL-P1", "Site selection & permitting", cost=120.0, lead_time=6,
                  prior_failure_rate=0.20, tags=("capital",)),
        Primitive("HEL-P2", "Equipment relocation & requalification", cost=340.0, lead_time=9,
                  prior_failure_rate=0.30, tags=("operational",)),
        Primitive("HEL-P3", "Workforce retraining & production ramp", cost=85.0, lead_time=6,
                  prior_failure_rate=0.25, tags=("workforce",)),
    ]
    helion_assembly = Assembly("Helion Semiconductors: HYPOTHETICAL fab relocation", helion_primitives, audit=audit)
    decisions.append(Decision(
        id="dec:helion_fab_relocation",
        name="Helion Semiconductors (fictional) — HYPOTHETICAL primary fab relocation",
        actor="helion_semi", actor_kind="company",
        description=(
            "HYPOTHETICAL scenario: Helion Semiconductors (a fictional company) relocates its primary "
            "fabrication plant out of its current East-Asia site over an 18-month program. Modeled origin "
            "effect: a temporary drop in Helion's own industrial output growth during the transition."
        ),
        assembly=helion_assembly,
        origin_shocks=[
            OriginShock("helion_semi", "industrial.industrial_output_growth_pct", -9.0,
                        "Illustrative: production disruption during equipment relocation and requalification."),
        ],
        proxy_route=ProxyRoute(
            home_country="china", scope=0.03,
            rationale=(
                "Illustrative modeling simplification: Helion is treated as representing roughly 3% of "
                "China's industrial-output-growth variance, so this fraction of its shock is additionally "
                "injected into China's own industrial.industrial_output_growth_pct, letting the shock reach "
                "China's within-country and cross-country (trade-link) edges. This scope fraction is a "
                "modeling convenience, not a measured market-share statistic."
            ),
        ),
    ))

    # ------------------------------------------------------------------
    # Decision 3 — Germany (country, energy/climate actor): HYPOTHETICAL
    # accelerated renewable-electricity mandate. Chosen to exercise a
    # mostly-domestic, multi-hop, multi-lag cascade (renewable share ->
    # transport emissions; plus the general energy-price/industrial
    # channel) rather than cross-border spillover.
    # ------------------------------------------------------------------
    germany_primitives = [
        Primitive("DEU-P1", "Legislative mandate & subsidy design", cost=15.0, lead_time=2,
                  prior_failure_rate=0.10, tags=("regulatory",)),
        Primitive("DEU-P2", "Grid & storage infrastructure buildout", cost=220.0, lead_time=10,
                  prior_failure_rate=0.30, tags=("capital", "operational")),
        Primitive("DEU-P3", "Phased fossil-capacity retirement", cost=40.0, lead_time=8,
                  prior_failure_rate=0.20, tags=("operational",)),
    ]
    germany_assembly = Assembly("Germany: HYPOTHETICAL accelerated renewable mandate", germany_primitives, audit=audit)
    decisions.append(Decision(
        id="dec:germany_renewable_mandate",
        name="Germany — HYPOTHETICAL accelerated renewable-electricity mandate",
        actor="germany", actor_kind="country",
        description=(
            "HYPOTHETICAL scenario: Germany legislates a target of +20 percentage points of renewable "
            "electricity generation share within 3 years, backed by grid/storage investment and phased "
            "fossil retirement. This is a fictional illustrative scenario, not a real announced policy. "
            "Modeled origin effect: a direct increase in Germany's renewable generation share."
        ),
        assembly=germany_assembly,
        origin_shocks=[
            OriginShock("germany", "energy.renewable_share_pct", 20.0,
                        "Illustrative: direct legislative/infrastructure effect on generation mix."),
        ],
    ))

    if audit:
        audit.log("DecisionLibrary", "built",
                   inputs={"n_decisions": len(decisions)},
                   outputs={"decision_ids": [d.id for d in decisions]})
    return decisions
