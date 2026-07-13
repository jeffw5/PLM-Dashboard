---
name: losses-hazards-definition
description: >-
  Run when evaluating Safety cases for conformance to STPA Handbook. Triggers on STPA
  artifacts in the Safety (STPA) discipline. Returns a 0-3 maturity score with
  defects, risk, and confidence for the PLM ingestion model.
version: 1.0.0
category: STPA
skill_id: 84
source_lineage:
  - title: STPA Handbook
    reference: Step 1
    uri: ref://stpa/losses-hazards-definition
maps_to:
  discipline: Safety (STPA)
  evaluate_agent: Discipline Skill Agents (Pipeline B) — safety
  pipeline: B
  plm_slots: design.*, develop.se.*
---

# Losses & Hazards Definition

## Overview
This skill evaluates whether a safety (stpa) artifact conforms to **STPA Handbook** (Step 1).
It is one skill in the PLM evaluation library; it shares the library's measurement
engine and output contract so its result converges cleanly into the PLM ingestion
model and the assessment console's gate.

## Scope
**Applies to:** Safety cases.
The skill reads the artifact (and, where relevant, its linked Jira items and traced
artifacts from the semantic layer) and evaluates only the criteria owned by this
skill. It does not re-evaluate criteria owned by sibling skills; overlaps are
reconciled at the aggregation step.

## How the discipline is applied
This skill applies system-theoretic safety discipline: the analysis is checked against the STPA step for completeness and traceability to hazards and constraints.
Concretely, it examines the artifact for **Losses, hazards, system-level constraints**. Each of those elements becomes a
scored dimension in the rubric below. Within STPA practice a non-conformance is
**material (major)** when no losses/hazards defined; it is **advisory (minor)** when hazards too broad. Every
judgement must cite evidence located in the artifact and trace back to STPA Handbook, so the
score is defensible to an auditor.

## Evaluation steps
1. Confirm the system boundary and purpose.
2. Enumerate losses (unacceptable outcomes).
3. Derive system-level hazards that can lead to each loss.
4. State system-level safety constraints.
5. Check each hazard traces to at least one loss.
6. Compute conformance (dimension mean, capped by any major), map defects to risk (L×I), and set confidence from evidence completeness.
7. Emit the output contract to the PLM ingestion model; if confidence is below the governance threshold, route to human review instead of scoring.

## Rubric — anchored dimensions
Each dimension is scored 0–3 against explicit anchors. Anchors are deliberately
concrete to keep scoring low-variance across evaluators and runs.

### 1. Losses
**0 — Absent.** No evidence of losses.
**1 — Deficient.** Losses partially addressed; ad hoc or incomplete.
**2 — Adequate.** Losses addressed with cited evidence in the artifact.
**3 — Strong.** Losses complete, evidenced, and traced to STPA Handbook.
### 2. Hazards
**0 — Absent.** No evidence of hazards.
**1 — Deficient.** Hazards partially addressed; ad hoc or incomplete.
**2 — Adequate.** Hazards addressed with cited evidence in the artifact.
**3 — Strong.** Hazards complete, evidenced, and traced to STPA Handbook.
### 3. System-level constraints
**0 — Absent.** No evidence of system-level constraints.
**1 — Deficient.** System-level constraints partially addressed; ad hoc or incomplete.
**2 — Adequate.** System-level constraints addressed with cited evidence in the artifact.
**3 — Strong.** System-level constraints complete, evidenced, and traced to STPA Handbook.

## Measurement — how the score is built
The measurement engine is uniform across the library (a feature — it lets
heterogeneous skills roll up together):

1. **Dimension scores.** Each dimension is scored 0–3 against its anchors, with a cited
   evidence locator. No evidence → 0.
2. **Conformance (0–3).** The skill's conformance is the mean of its dimension scores,
   rounded to the nearest integer — this is the value written to the PLM slot.
3. **Major cap.** Any **major** defect caps conformance at 1; a major on a
   safety- or release-critical artifact caps it at 0 and becomes a hard gate in the
   console. Majors are gate-tripping by design.
4. **Minor accrual.** **Minor** defects do not cap the score but are recorded as debt
   and feed the defect-burndown dashboard.
5. **Coverage (where countable).** For dimensions over enumerable items (requirements,
   control actions, clauses), coverage = covered ÷ total is reported alongside the score.
6. **Confidence.** confidence = evidence_completeness × source_clarity (0–1). Below the
   governance threshold the circuit-breaker (MTBH) routes the result to human review
   rather than letting a low-confidence score reach the gate.

## Defect model
- **Major (gate-tripping):** No losses/hazards defined.
- **Minor (advisory, accrues as debt):** Hazards too broad.

## Risk model
Each detected defect is rated **likelihood × impact** (1–5 each). Likelihood rises with
the size of the conformance gap; impact rises with the artifact's criticality, its
lifecycle phase (release-facing phases weigh higher), and the governance weight of this
discipline. Exposure bands: Low (<5), Moderate (5–9), High (10–15), Critical (≥16).

## Output contract
Returned to the PLM ingestion model — identical shape for every skill:

```json
{
  "skill": "losses-hazards-definition",
  "conformance": 0,
  "coverage": null,
  "defects": [{ "severity": "major|minor", "ref": "<criterion>", "evidence": "<locator>" }],
  "risk": { "L": 0, "I": 0, "E": 0 },
  "confidence": 0.0,
  "lineage": ["STPA Handbook — Step 1", "<artifact uri>"]
}
```

## Governance
- **Confidence threshold:** 0.60. Below this, route to a safety (stpa) reviewer.
- **Provenance:** every score records source → evidence → timestamp for audit.
- **Versioning:** any change to a rubric anchor or the defect model bumps `version`.

## References (lineage)
- STPA Handbook — Step 1.
- PLM Skills Catalog v1.0 — consistent skill template.
- PLM Solution Architecture v1.0 — Evaluate stage, Discipline Skill Agents (Pipeline B) — safety.
