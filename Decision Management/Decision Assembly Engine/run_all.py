"""
Orchestrator: runs all three domains through the SAME six-component engine
and four reusable patterns, and writes everything a downstream consumer
(the dashboard, an auditor, another program) needs:

  output/results.json        — machine-readable results for all domains
  output/audit_trail.json     — full structured, hashed event log
  output/audit_summary.json   — per-domain event counts + chain hash

Run with: python3 run_all.py [--n 10000]
"""
from __future__ import annotations

import argparse
import json
import time
from pathlib import Path

from core.audit import AuditTrail
from domains import cyber_defense, rd_portfolio, supply_chain

OUTPUT_DIR = Path(__file__).parent / "output"


def run_domain(module, n_simulations: int, **kwargs):
    domain_name = module.DOMAIN
    audit = AuditTrail(domain_name)
    t0 = time.time()
    result = module.run(audit, n_simulations=n_simulations, **kwargs)
    result["_meta"] = {
        "n_simulations": n_simulations,
        "runtime_seconds": round(time.time() - t0, 2),
        "audit_summary": audit.summary(),
    }
    return result, audit


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10_000, help="Monte Carlo draws per strategy/scenario")
    args = ap.parse_args()

    OUTPUT_DIR.mkdir(exist_ok=True)

    print(f"Running Reusable Decision Engine across 3 domains (N={args.n} draws each)...\n")

    rd_result, rd_audit = run_domain(rd_portfolio, args.n, liquidity_available=25.0)
    print(f"[1/3] {rd_result['title']}: recommended -> {rd_result['selection']['recommended']} "
          f"({rd_result['_meta']['runtime_seconds']}s, {rd_result['_meta']['audit_summary']['n_events']} audit events)")

    sc_result, sc_audit = run_domain(supply_chain, args.n, liquidity_available=8.0)
    print(f"[2/3] {sc_result['title']}: recommended -> {sc_result['selection']['recommended']} "
          f"({sc_result['_meta']['runtime_seconds']}s, {sc_result['_meta']['audit_summary']['n_events']} audit events)")

    cy_result, cy_audit = run_domain(cyber_defense, args.n)
    print(f"[3/3] {cy_result['title']}: recommended -> {cy_result['selection']['recommended']} "
          f"({cy_result['_meta']['runtime_seconds']}s, {cy_result['_meta']['audit_summary']['n_events']} audit events)")

    all_results = {"rd_portfolio": rd_result, "supply_chain": sc_result, "cyber_defense": cy_result}
    all_audit = {"rd_portfolio": rd_audit.to_json(), "supply_chain": sc_audit.to_json(),
                 "cyber_defense": cy_audit.to_json()}
    all_summary = {"rd_portfolio": rd_audit.summary(), "supply_chain": sc_audit.summary(),
                   "cyber_defense": cy_audit.summary()}

    (OUTPUT_DIR / "results.json").write_text(json.dumps(all_results, indent=2, default=str))
    (OUTPUT_DIR / "audit_trail.json").write_text(json.dumps(all_audit, indent=2, default=str))
    (OUTPUT_DIR / "audit_summary.json").write_text(json.dumps(all_summary, indent=2, default=str))

    total_events = sum(s["n_events"] for s in all_summary.values())
    print(f"\nWrote {OUTPUT_DIR / 'results.json'}")
    print(f"Wrote {OUTPUT_DIR / 'audit_trail.json'}  ({total_events} total audit events, "
          f"chain hashes: " + ", ".join(f"{d}={s['chain_hash']}" for d, s in all_summary.items()) + ")")
    print(f"Wrote {OUTPUT_DIR / 'audit_summary.json'}")


if __name__ == "__main__":
    main()
