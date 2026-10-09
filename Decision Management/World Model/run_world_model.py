"""
World Model orchestrator: builds the ontology/registry/causal graph,
runs the 3 HYPOTHETICAL example decisions through the graph-propagation
engine, generates an Impact Assessment for each, and writes everything
to output/ for the dashboard to read.

Run:  python3 run_world_model.py
"""
from __future__ import annotations

import json
import os

from core.audit import AuditTrail
from world_model.causal_graph import build_causal_graph, mechanisms_to_dict
from world_model.decisions import build_decisions
from world_model.impact_assessment import generate_impact_assessment
from world_model.ontology import ontology_to_dict
from world_model.propagation import GraphPropagationEngine
from world_model.registry import registry_to_dict

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "output")
N_SIMULATIONS = 5_000
SEED = 42


def main() -> None:
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    audit = AuditTrail("world_model")

    print("Building ontology, registry, and causal graph...")
    ontology = ontology_to_dict()
    registry = registry_to_dict()
    edges = build_causal_graph(audit=audit)
    mechanisms = mechanisms_to_dict()
    print(f"  {len(ontology['state_variables'])} state variables across {len(ontology['sectors'])} sectors")
    print(f"  {len(registry['countries'])} countries, {len(registry['companies'])} companies, "
          f"{len(registry['trade_links'])} trade links")
    print(f"  {len(edges)} causal edges ({len(mechanisms)} within-country mechanism templates "
          f"x {len(registry['countries'])} countries + {len(registry['trade_links'])} cross-country)")

    decisions = build_decisions(audit=audit)
    engine = GraphPropagationEngine(edges, n_simulations=N_SIMULATIONS, seed=SEED, audit=audit)

    print(f"\nPropagating {len(decisions)} HYPOTHETICAL decisions through the causal graph "
          f"({N_SIMULATIONS} Monte Carlo draws each)...")
    decision_results = []
    for d in decisions:
        result = engine.run(d)
        ia = generate_impact_assessment(d, result)
        decision_results.append(ia.to_dict())
        print(f"  [{d.id}] {len(result.impacts)} nodes reached, "
              f"{len(result.contribution_log)} edge firings, "
              f"{len(ia.domestic_impacts)} domestic + {len(ia.cross_border_impacts)} cross-border "
              f"material impacts reported")

    results_payload = {
        "disclaimer": (
            "EVERYTHING IN THIS FILE IS AN ILLUSTRATIVE MODEL OUTPUT. Baseline statistics are "
            "placeholders, causal edges are expert-elicited hypotheses with explicit uncertainty, "
            "decisions are fictional/hypothetical scenarios, and propagation uses an explicit, "
            "documented damping/hop-limit convention. None of this is a real-world forecast, and "
            "none of it was sent to, or acted on by, any real institution or person."
        ),
        "ontology": ontology,
        "registry": registry,
        "causal_graph": {
            "mechanism_templates": mechanisms,
            "n_within_country_edges": len(edges) - len(registry["trade_links"]),
            "n_cross_country_edges": len(registry["trade_links"]),
            "n_total_edges": len(edges),
            "cross_country_edges": [e.to_dict() for e in edges if e.kind == "cross_country"],
        },
        "decisions": decision_results,
        "simulation_config": {"n_simulations": N_SIMULATIONS, "seed": SEED},
    }

    results_path = os.path.join(OUTPUT_DIR, "world_model_results.json")
    with open(results_path, "w") as f:
        json.dump(results_payload, f, indent=2)

    audit_path = os.path.join(OUTPUT_DIR, "world_model_audit.json")
    with open(audit_path, "w") as f:
        json.dump({"summary": audit.summary(), "events": audit.to_list()}, f, indent=2)

    print(f"\nWrote {results_path}")
    print(f"Wrote {audit_path}  ({audit.summary()['n_events']} audit events, "
          f"chain hash {audit.chain_hash()})")


if __name__ == "__main__":
    main()
