---
name: performance-evaluation
description: >-
  Run when evaluating Audit records for conformance to ISO 9001:2015. Triggers on ISO 9000 / 9001
  artifacts in the Quality (ISO 9001) discipline. Returns a 0-3 maturity score with
  defects, risk, and confidence for the PLM ingestion model.
version: 1.0.0
category: ISO 9000 / 9001
skill_id: 50
source_lineage:
  - title: ISO 9001:2015
    reference: Clause 9
    uri: ref://iso-9001/performance-evaluation
maps_to:
  discipline: Quality (ISO 9001)
  evaluate_agent: Standards Conformance Skill Agents (Pipeline B)
  pipeline: B
  plm_slots: deliver.*, develop.*
---

# Performance Evaluation

## Overview
This skill evaluates whether a quality (iso 9001) artifact conforms to **ISO 9001:2015** (Clause 9).
It is one skill in the PLM evaluation library; it shares the library's measurement
engine and output contract so its result converges cleanly into the PLM ingestion
model and the assessment console's gate.

## Scope
**Applies to:** Audit records.
The skill reads the artifact (and, where relevant, its linked Jira items and traced
artifacts from the semantic layer) and evaluates only the criteria owned by this
skill. It does not re-evaluate criteria owned by sibling skills; overlaps are
reconciled at the aggregation step.

## How the discipline is applied
This skill applies quality-management-system discipline: the clause's requirements are checked for coverage, controlled evidence, and demonstrated improvement.
Concretely, it examines the artifact for **Monitoring, internal audit, mgmt review**. Each of those elements becomes a
scored dimension in the rubric below. Within ISO 9000 / 9001 practice a non-conformance is
**material (major)** when no internal audit; it is **advisory (minor)** when review cadence weak. Every
judgement must cite evidence located in the artifact and trace back to ISO 9001:2015, so the
score is defensible to an auditor.

## Evaluation steps
1. Retrieve the governing criteria from **ISO 9001:2015** (Clause 9) via the semantic layer's reference cards.
2. Locate and confirm the target artifact(s): _Audit records_ (type verified by the artifact classifier).
3. For each rubric dimension, find supporting evidence in the artifact and record its locator (section/figure/link).
4. Score each dimension 0–3 against its anchors; absence of evidence scores 0.
5. Detect defects — flag majors and minors, attaching evidence and the source reference for each.
6. Compute conformance (dimension mean, capped by any major), map defects to risk (L×I), and set confidence from evidence completeness.
7. Emit the output contract to the PLM ingestion model; if confidence is below the governance threshold, route to human review instead of scoring.

## Rubric — anchored dimensions
Each dimension is scored 0–3 against explicit anchors. Anchors are deliberately
concrete to keep scoring low-variance across evaluators and runs.

### 1. Monitoring
**0 — Absent.** No evidence of monitoring.
**1 — Deficient.** Monitoring partially addressed; ad hoc or incomplete.
**2 — Adequate.** Monitoring addressed with cited evidence in the artifact.
**3 — Strong.** Monitoring complete, evidenced, and traced to ISO 9001:2015.
### 2. Internal audit
**0 — Absent.** No evidence of internal audit.
**1 — Deficient.** Internal audit partially addressed; ad hoc or incomplete.
**2 — Adequate.** Internal audit addressed with cited evidence in the artifact.
**3 — Strong.** Internal audit complete, evidenced, and traced to ISO 9001:2015.
### 3. Mgmt review
**0 — Absent.** No evidence of mgmt review.
**1 — Deficient.** Mgmt review partially addressed; ad hoc or incomplete.
**2 — Adequate.** Mgmt review addressed with cited evidence in the artifact.
**3 — Strong.** Mgmt review complete, evidenced, and traced to ISO 9001:2015.

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
- **Major (gate-tripping):** No internal audit.
- **Minor (advisory, accrues as debt):** Review cadence weak.

## Risk model
Each detected defect is rated **likelihood × impact** (1–5 each). Likelihood rises with
the size of the conformance gap; impact rises with the artifact's criticality, its
lifecycle phase (release-facing phases weigh higher), and the governance weight of this
discipline. Exposure bands: Low (<5), Moderate (5–9), High (10–15), Critical (≥16).

## Output contract
Returned to the PLM ingestion model — identical shape for every skill:

```json
{
  "skill": "performance-evaluation",
  "conformance": 0,
  "coverage": null,
  "defects": [{ "severity": "major|minor", "ref": "<criterion>", "evidence": "<locator>" }],
  "risk": { "L": 0, "I": 0, "E": 0 },
  "confidence": 0.0,
  "lineage": ["ISO 9001:2015 — Clause 9", "<artifact uri>"]
}
```

## Governance
- **Confidence threshold:** 0.60. Below this, route to a quality (iso 9001) reviewer.
- **Provenance:** every score records source → evidence → timestamp for audit.
- **Versioning:** any change to a rubric anchor or the defect model bumps `version`.

## References (lineage)
- ISO 9001:2015 — Clause 9.
- PLM Skills Catalog v1.0 — consistent skill template.
- PLM Solution Architecture v1.0 — Evaluate stage, Standards Conformance Skill Agents (Pipeline B).
