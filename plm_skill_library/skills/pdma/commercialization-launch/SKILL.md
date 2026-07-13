---
name: commercialization-launch
description: >-
  Run when evaluating Launch plans for conformance to PDMA BoK. Triggers on PDMA / PLM
  artifacts in the Product Management (PDMA) discipline. Returns a 0-3 maturity score with
  defects, risk, and confidence for the PLM ingestion model.
version: 1.0.0
category: PDMA / PLM
skill_id: 42
source_lineage:
  - title: PDMA BoK
    reference: Launch
    uri: ref://pdma/commercialization-launch
maps_to:
  discipline: Product Management (PDMA)
  evaluate_agent: Discipline Skill Agents (Pipeline B)
  pipeline: B
  plm_slots: discover.*, deliver.*, run.*
---

# Commercialization / Launch

## Overview
This skill evaluates whether a product management (pdma) artifact conforms to **PDMA BoK** (Launch).
It is one skill in the PLM evaluation library; it shares the library's measurement
engine and output contract so its result converges cleanly into the PLM ingestion
model and the assessment console's gate.

## Scope
**Applies to:** Launch plans.
The skill reads the artifact (and, where relevant, its linked Jira items and traced
artifacts from the semantic layer) and evaluates only the criteria owned by this
skill. It does not re-evaluate criteria owned by sibling skills; overlaps are
reconciled at the aggregation step.

## How the discipline is applied
This skill applies product-development discipline: the artifact is checked against new-product-development practice for stage rigor, evidence, and decision quality.
Concretely, it examines the artifact for **Launch plan, readiness, channels**. Each of those elements becomes a
scored dimension in the rubric below. Within PDMA / PLM practice a non-conformance is
**material (major)** when no launch readiness gate; it is **advisory (minor)** when weak channel plan. Every
judgement must cite evidence located in the artifact and trace back to PDMA BoK, so the
score is defensible to an auditor.

## Evaluation steps
1. Retrieve the governing criteria from **PDMA BoK** (Launch) via the semantic layer's reference cards.
2. Locate and confirm the target artifact(s): _Launch plans_ (type verified by the artifact classifier).
3. For each rubric dimension, find supporting evidence in the artifact and record its locator (section/figure/link).
4. Score each dimension 0–3 against its anchors; absence of evidence scores 0.
5. Detect defects — flag majors and minors, attaching evidence and the source reference for each.
6. Compute conformance (dimension mean, capped by any major), map defects to risk (L×I), and set confidence from evidence completeness.
7. Emit the output contract to the PLM ingestion model; if confidence is below the governance threshold, route to human review instead of scoring.

## Rubric — anchored dimensions
Each dimension is scored 0–3 against explicit anchors. Anchors are deliberately
concrete to keep scoring low-variance across evaluators and runs.

### 1. Launch plan
**0 — Absent.** No evidence of launch plan.
**1 — Deficient.** Launch plan partially addressed; ad hoc or incomplete.
**2 — Adequate.** Launch plan addressed with cited evidence in the artifact.
**3 — Strong.** Launch plan complete, evidenced, and traced to PDMA BoK.
### 2. Readiness
**0 — Absent.** No evidence of readiness.
**1 — Deficient.** Readiness partially addressed; ad hoc or incomplete.
**2 — Adequate.** Readiness addressed with cited evidence in the artifact.
**3 — Strong.** Readiness complete, evidenced, and traced to PDMA BoK.
### 3. Channels
**0 — Absent.** No evidence of channels.
**1 — Deficient.** Channels partially addressed; ad hoc or incomplete.
**2 — Adequate.** Channels addressed with cited evidence in the artifact.
**3 — Strong.** Channels complete, evidenced, and traced to PDMA BoK.

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
- **Major (gate-tripping):** No launch readiness gate.
- **Minor (advisory, accrues as debt):** Weak channel plan.

## Risk model
Each detected defect is rated **likelihood × impact** (1–5 each). Likelihood rises with
the size of the conformance gap; impact rises with the artifact's criticality, its
lifecycle phase (release-facing phases weigh higher), and the governance weight of this
discipline. Exposure bands: Low (<5), Moderate (5–9), High (10–15), Critical (≥16).

## Output contract
Returned to the PLM ingestion model — identical shape for every skill:

```json
{
  "skill": "commercialization-launch",
  "conformance": 0,
  "coverage": null,
  "defects": [{ "severity": "major|minor", "ref": "<criterion>", "evidence": "<locator>" }],
  "risk": { "L": 0, "I": 0, "E": 0 },
  "confidence": 0.0,
  "lineage": ["PDMA BoK — Launch", "<artifact uri>"]
}
```

## Governance
- **Confidence threshold:** 0.60. Below this, route to a product management (pdma) reviewer.
- **Provenance:** every score records source → evidence → timestamp for audit.
- **Versioning:** any change to a rubric anchor or the defect model bumps `version`.

## References (lineage)
- PDMA BoK — Launch.
- PLM Skills Catalog v1.0 — consistent skill template.
- PLM Solution Architecture v1.0 — Evaluate stage, Discipline Skill Agents (Pipeline B).
