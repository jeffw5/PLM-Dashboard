---
name: control-structure-modeling
description: >-
  Run when evaluating Control structure diagrams for conformance to STPA Handbook. Triggers on STPA
  artifacts in the Safety (STPA) discipline. Returns a 0-3 maturity score with
  defects, risk, and confidence for the PLM ingestion model.
version: 1.0.0
category: STPA
skill_id: 85
source_lineage:
  - title: STPA Handbook
    reference: Step 2
    uri: ref://stpa/control-structure-modeling
maps_to:
  discipline: Safety (STPA)
  evaluate_agent: Discipline Skill Agents (Pipeline B) — safety
  pipeline: B
  plm_slots: design.*, develop.se.*
---

# Control Structure Modeling

## Overview
This skill evaluates whether a safety (stpa) artifact conforms to **STPA Handbook** (Step 2).
It is one skill in the PLM evaluation library; it shares the library's measurement
engine and output contract so its result converges cleanly into the PLM ingestion
model and the assessment console's gate.

## Scope
**Applies to:** Control structure diagrams.
The skill reads the artifact (and, where relevant, its linked Jira items and traced
artifacts from the semantic layer) and evaluates only the criteria owned by this
skill. It does not re-evaluate criteria owned by sibling skills; overlaps are
reconciled at the aggregation step.

## How the discipline is applied
This skill applies system-theoretic safety discipline: the analysis is checked against the STPA step for completeness and traceability to hazards and constraints.
Concretely, it examines the artifact for **Controllers, actions, feedback, process model**. Each of those elements becomes a
scored dimension in the rubric below. Within STPA practice a non-conformance is
**material (major)** when incomplete control structure; it is **advisory (minor)** when feedback loops missing. Every
judgement must cite evidence located in the artifact and trace back to STPA Handbook, so the
score is defensible to an auditor.

## Evaluation steps
1. Identify controllers, controlled processes, and actuators/sensors.
2. Draw control actions (down) and feedback (up) for each loop.
3. Capture each controller's process model (beliefs about state).
4. Check every control action has corresponding feedback.
5. Verify the structure covers all hazards from Step 1.
6. Compute conformance (dimension mean, capped by any major), map defects to risk (L×I), and set confidence from evidence completeness.
7. Emit the output contract to the PLM ingestion model; if confidence is below the governance threshold, route to human review instead of scoring.

## Rubric — anchored dimensions
Each dimension is scored 0–3 against explicit anchors. Anchors are deliberately
concrete to keep scoring low-variance across evaluators and runs.

### 1. Controllers
**0 — Absent.** No evidence of controllers.
**1 — Deficient.** Controllers partially addressed; ad hoc or incomplete.
**2 — Adequate.** Controllers addressed with cited evidence in the artifact.
**3 — Strong.** Controllers complete, evidenced, and traced to STPA Handbook.
### 2. Actions
**0 — Absent.** No evidence of actions.
**1 — Deficient.** Actions partially addressed; ad hoc or incomplete.
**2 — Adequate.** Actions addressed with cited evidence in the artifact.
**3 — Strong.** Actions complete, evidenced, and traced to STPA Handbook.
### 3. Feedback
**0 — Absent.** No evidence of feedback.
**1 — Deficient.** Feedback partially addressed; ad hoc or incomplete.
**2 — Adequate.** Feedback addressed with cited evidence in the artifact.
**3 — Strong.** Feedback complete, evidenced, and traced to STPA Handbook.
### 4. Process model
**0 — Absent.** No evidence of process model.
**1 — Deficient.** Process model partially addressed; ad hoc or incomplete.
**2 — Adequate.** Process model addressed with cited evidence in the artifact.
**3 — Strong.** Process model complete, evidenced, and traced to STPA Handbook.

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
- **Major (gate-tripping):** Incomplete control structure.
- **Minor (advisory, accrues as debt):** Feedback loops missing.

## Risk model
Each detected defect is rated **likelihood × impact** (1–5 each). Likelihood rises with
the size of the conformance gap; impact rises with the artifact's criticality, its
lifecycle phase (release-facing phases weigh higher), and the governance weight of this
discipline. Exposure bands: Low (<5), Moderate (5–9), High (10–15), Critical (≥16).

## Output contract
Returned to the PLM ingestion model — identical shape for every skill:

```json
{
  "skill": "control-structure-modeling",
  "conformance": 0,
  "coverage": null,
  "defects": [{ "severity": "major|minor", "ref": "<criterion>", "evidence": "<locator>" }],
  "risk": { "L": 0, "I": 0, "E": 0 },
  "confidence": 0.0,
  "lineage": ["STPA Handbook — Step 2", "<artifact uri>"]
}
```

## Governance
- **Confidence threshold:** 0.60. Below this, route to a safety (stpa) reviewer.
- **Provenance:** every score records source → evidence → timestamp for audit.
- **Versioning:** any change to a rubric anchor or the defect model bumps `version`.

## References (lineage)
- STPA Handbook — Step 2.
- PLM Skills Catalog v1.0 — consistent skill template.
- PLM Solution Architecture v1.0 — Evaluate stage, Discipline Skill Agents (Pipeline B) — safety.
