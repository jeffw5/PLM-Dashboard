# PLM Evaluation Skills — Library

89 skills across 11 disciplines. Every skill is a `SKILL.md` built to one consistent template with source lineage, an anchored 0–3 rubric, a shared measurement engine, and a uniform output contract that feeds the PLM ingestion model.

## Template (every skill)

`frontmatter` (name · description · version · category · **source_lineage** · maps_to) then:
**Overview · Scope · How the discipline is applied · Evaluation steps · Rubric (anchored 0–3 dimensions) · Measurement (how the score is built) · Defect model (major/minor) · Risk model · Output contract · Governance · References**.

## Measurement engine (shared)

Dimension scores (0–3, evidence-cited) → conformance = rounded mean → **major defects cap the score** (hard-gate on critical artifacts) → minors accrue as debt → confidence gates low-evidence results to human review (MTBH).

## Catalog

### AI Governance (7)
- **AI Risk Management** — NIST AI RMF (1.0, 2023) · `skills/ai-governance/ai-risk-management/SKILL.md`
- **AI Management System** — ISO/IEC 42001 (2023) · `skills/ai-governance/ai-management-system/SKILL.md`
- **AI Risk Process** — ISO/IEC 23894 (2023) · `skills/ai-governance/ai-risk-process/SKILL.md`
- **Transparency & Explainability** — EU AI Act · model cards (2024) · `skills/ai-governance/transparency-explainability/SKILL.md`
- **Human Oversight (HITL)** — EU AI Act (Art. 14) · `skills/ai-governance/human-oversight-hitl/SKILL.md`
- **AI Provenance & Documentation** — Model cards · datasheets (—) · `skills/ai-governance/ai-provenance-documentation/SKILL.md`
- **Confidence Governance (MTBH)** — HSGA · AI Circuit Breaker (—) · `skills/ai-governance/confidence-governance-mtbh/SKILL.md`

### Analytic Governance (5)
- **Metric Definition & Validation** — Analytics governance practice (—) · `skills/analytic-governance/metric-definition-validation/SKILL.md`
- **Model Documentation & Validation** — SR 11-7 (Fed/OCC) (2011) · `skills/analytic-governance/model-documentation-validation/SKILL.md`
- **Method Transparency & Reproducibility** — Reproducible analytics practice (—) · `skills/analytic-governance/method-transparency-reproducibility/SKILL.md`
- **Analytic Lineage & Versioning** — MLOps governance (—) · `skills/analytic-governance/analytic-lineage-versioning/SKILL.md`
- **KPI / OKR Governance** — OKR / BSC practice (—) · `skills/analytic-governance/kpi-okr-governance/SKILL.md`

### Business Architecture (7)
- **Capability Map Conformance** — BIZBOK Guide (Capability Mapping) · `skills/business-architecture/capability-map-conformance/SKILL.md`
- **Value Stream Mapping** — BIZBOK Guide (Value Streams) · `skills/business-architecture/value-stream-mapping/SKILL.md`
- **Strategy Map Alignment** — BIZBOK Guide · Kaplan-Norton (Strategy / BSC) · `skills/business-architecture/strategy-map-alignment/SKILL.md`
- **Organization Map** — BIZBOK Guide (Organization) · `skills/business-architecture/organization-map/SKILL.md`
- **Information Map** — BIZBOK Guide (Information) · `skills/business-architecture/information-map/SKILL.md`
- **Capability→Initiative Traceability** — BIZBOK Guide (Blueprint linkage) · `skills/business-architecture/capability-initiative-traceability/SKILL.md`
- **Value Stream × Capability Cross-Map** — BIZBOK Guide (Cross-mapping) · `skills/business-architecture/value-stream-capability-cross-map/SKILL.md`

### Data Governance (8)
- **Data Governance Framework** — DAMA-DMBOK2 (Ch.3) · `skills/data-governance/data-governance-framework/SKILL.md`
- **Data Quality Management** — DAMA-DMBOK2 · DCAM (Ch.13) · `skills/data-governance/data-quality-management/SKILL.md`
- **Metadata Management** — DAMA-DMBOK2 (Ch.12) · `skills/data-governance/metadata-management/SKILL.md`
- **Data Architecture & Modeling** — DAMA-DMBOK2 (Ch.4–5) · `skills/data-governance/data-architecture-modeling/SKILL.md`
- **Master & Reference Data** — DAMA-DMBOK2 (Ch.10) · `skills/data-governance/master-reference-data/SKILL.md`
- **Data Lineage & Provenance** — DAMA-DMBOK2 · DCAM (Lineage) · `skills/data-governance/data-lineage-provenance/SKILL.md`
- **Data Security & Privacy** — DAMA-DMBOK2 (Ch.7) · `skills/data-governance/data-security-privacy/SKILL.md`
- **DCAM Capability Assessment** — EDM Council DCAM (v2.x) · `skills/data-governance/dcam-capability-assessment/SKILL.md`

### ISO 9000 / 9001 (8)
- **Context of the Organization** — ISO 9001:2015 (Clause 4) · `skills/iso-9001/context-of-the-organization/SKILL.md`
- **Leadership** — ISO 9001:2015 (Clause 5) · `skills/iso-9001/leadership/SKILL.md`
- **Planning (risk-based)** — ISO 9001:2015 (Clause 6) · `skills/iso-9001/planning-risk-based/SKILL.md`
- **Support** — ISO 9001:2015 (Clause 7) · `skills/iso-9001/support/SKILL.md`
- **Operation** — ISO 9001:2015 (Clause 8) · `skills/iso-9001/operation/SKILL.md`
- **Performance Evaluation** — ISO 9001:2015 (Clause 9) · `skills/iso-9001/performance-evaluation/SKILL.md`
- **Improvement** — ISO 9001:2015 (Clause 10) · `skills/iso-9001/improvement/SKILL.md`
- **Documented Information Control** — ISO 9001:2015 (§7.5) · `skills/iso-9001/documented-information-control/SKILL.md`

### PDMA / PLM (8)
- **Product Strategy & Portfolio** — PDMA Body of Knowledge (Portfolio Mgmt) · `skills/pdma/product-strategy-portfolio/SKILL.md`
- **Opportunity & Idea Management** — PDMA BoK (Discovery) · `skills/pdma/opportunity-idea-management/SKILL.md`
- **Stage-Gate Process** — PDMA BoK · Cooper Stage-Gate (Process Mgmt) · `skills/pdma/stage-gate-process/SKILL.md`
- **Voice of Customer / Market Research** — PDMA BoK (Market Research) · `skills/pdma/voice-of-customer-market-research/SKILL.md`
- **Product Design & Development** — PDMA BoK (Design & Dev) · `skills/pdma/product-design-development/SKILL.md`
- **Commercialization / Launch** — PDMA BoK (Launch) · `skills/pdma/commercialization-launch/SKILL.md`
- **Lifecycle Management (launch→retire)** — PDMA BoK (PLM) · `skills/pdma/lifecycle-management-launch-retire/SKILL.md`
- **NPD Governance & Metrics** — PDMA BoK (Metrics) · `skills/pdma/npd-governance-metrics/SKILL.md`

### PMI (Waterfall & Agile) (14)
- **Integration Management** — PMBOK Guide (6th · Integration KA) · `skills/pmi/integration-management/SKILL.md`
- **Scope Management** — PMBOK Guide (6th · Scope KA) · `skills/pmi/scope-management/SKILL.md`
- **Schedule Management** — PMBOK Guide (6th · Schedule KA) · `skills/pmi/schedule-management/SKILL.md`
- **Cost Management** — PMBOK Guide (6th · Cost KA) · `skills/pmi/cost-management/SKILL.md`
- **Quality Management** — PMBOK Guide (6th · Quality KA) · `skills/pmi/quality-management/SKILL.md`
- **Resource Management** — PMBOK Guide (6th · Resource KA) · `skills/pmi/resource-management/SKILL.md`
- **Communications Management** — PMBOK Guide (6th · Comms KA) · `skills/pmi/communications-management/SKILL.md`
- **Risk Management (PMI)** — PMBOK Guide (6th · Risk KA) · `skills/pmi/risk-management-pmi/SKILL.md`
- **Procurement Management** — PMBOK Guide (6th · Procurement KA) · `skills/pmi/procurement-management/SKILL.md`
- **Stakeholder Management** — PMBOK Guide (6th · Stakeholder KA) · `skills/pmi/stakeholder-management/SKILL.md`
- **Performance Domains** — PMBOK Guide (7th · 8 performance domains) · `skills/pmi/performance-domains/SKILL.md`
- **Agile Delivery Conformance** — PMI Agile Practice Guide (2017) · `skills/pmi/agile-delivery-conformance/SKILL.md`
- **Backlog & Flow Management** — Agile Practice Guide · Scrum Guide (2020) · `skills/pmi/backlog-flow-management/SKILL.md`
- **Agile Metrics & DoD/DoR** — Agile Practice Guide (2017) · `skills/pmi/agile-metrics-dod-dor/SKILL.md`

### Risk Management (5)
- **Risk Framework & Process** — ISO 31000 (2018) · `skills/risk-management/risk-framework-process/SKILL.md`
- **Risk Register Quality** — ISO 31000 · PMI (—) · `skills/risk-management/risk-register-quality/SKILL.md`
- **Risk Assessment (L×I)** — ISO 31000 (§6.4) · `skills/risk-management/risk-assessment-l-i/SKILL.md`
- **Risk Treatment & Mitigation** — ISO 31000 (§6.5) · `skills/risk-management/risk-treatment-mitigation/SKILL.md`
- **Opportunity (Positive Risk)** — PMI · Hillson (—) · `skills/risk-management/opportunity-positive-risk/SKILL.md`

### STPA (6)
- **Losses & Hazards Definition** — STPA Handbook (Step 1) · `skills/stpa/losses-hazards-definition/SKILL.md`
- **Control Structure Modeling** — STPA Handbook (Step 2) · `skills/stpa/control-structure-modeling/SKILL.md`
- **Unsafe Control Actions (UCA)** — STPA Handbook (Step 3) · `skills/stpa/unsafe-control-actions-uca/SKILL.md`
- **Loss Scenarios & Causal Factors** — STPA Handbook (Step 4) · `skills/stpa/loss-scenarios-causal-factors/SKILL.md`
- **Safety Constraints & Requirements** — STPA · Engineering a Safer World (—) · `skills/stpa/safety-constraints-requirements/SKILL.md`
- **STPA-Sec (Security)** — Young & Leveson (2014) · `skills/stpa/stpa-sec-security/SKILL.md`

### Semantic Governance (6)
- **Ontology Conformance** — W3C OWL 2 (2012) · `skills/semantic-governance/ontology-conformance/SKILL.md`
- **Constraint Validation** — W3C SHACL (2017) · `skills/semantic-governance/constraint-validation/SKILL.md`
- **Vocabulary & Taxonomy Governance** — SKOS · ISO 25964 (—) · `skills/semantic-governance/vocabulary-taxonomy-governance/SKILL.md`
- **Semantic Mapping Quality (RDSG)** — RDSG · HSGA (v3.0) · `skills/semantic-governance/semantic-mapping-quality-rdsg/SKILL.md`
- **FAIR Conformance** — FAIR Principles (Wilkinson 2016) · `skills/semantic-governance/fair-conformance/SKILL.md`
- **Holonic Governance (HSGA)** — HSGA (v3.0) · `skills/semantic-governance/holonic-governance-hsga/SKILL.md`

### Systems Engineering (15)
- **Stakeholder Needs & Requirements** — ISO/IEC/IEEE 15288 · SEBoK (§6.4.2 · SEBoK Concept Def.) · `skills/systems-engineering/stakeholder-needs-requirements/SKILL.md`
- **System Requirements Definition** — ISO/IEC/IEEE 15288 (§6.4.3) · `skills/systems-engineering/system-requirements-definition/SKILL.md`
- **Requirements Quality (individual)** — INCOSE GtWR (v4 · individual characteristics) · `skills/systems-engineering/requirements-quality-individual/SKILL.md`
- **Requirements Set Quality** — INCOSE GtWR (v4 · set characteristics) · `skills/systems-engineering/requirements-set-quality/SKILL.md`
- **Architecture Definition** — ISO/IEC/IEEE 15288 (§6.4.4) · `skills/systems-engineering/architecture-definition/SKILL.md`
- **Architecture Description Conformance** — ISO/IEC/IEEE 42010 (2022) · `skills/systems-engineering/architecture-description-conformance/SKILL.md`
- **Design Definition** — ISO/IEC/IEEE 15288 (§6.4.5) · `skills/systems-engineering/design-definition/SKILL.md`
- **System Analysis / Trade Studies** — ISO/IEC/IEEE 15288 · SEBoK (§6.4.6) · `skills/systems-engineering/system-analysis-trade-studies/SKILL.md`
- **Verification** — ISO/IEC/IEEE 15288 (§6.4.9) · `skills/systems-engineering/verification/SKILL.md`
- **Validation** — ISO/IEC/IEEE 15288 (§6.4.11) · `skills/systems-engineering/validation/SKILL.md`
- **Integration** — ISO/IEC/IEEE 15288 (§6.4.8) · `skills/systems-engineering/integration/SKILL.md`
- **Transition / Operation / Maintenance** — ISO/IEC/IEEE 15288 (§6.4.10–6.4.13) · `skills/systems-engineering/transition-operation-maintenance/SKILL.md`
- **Enterprise SE Alignment** — SEBoK Enterprise SE KA (v2.x (attachment)) · `skills/systems-engineering/enterprise-se-alignment/SKILL.md`
- **Measurement (MoE / MoP / TPM)** — SEBoK Measurement · ISO/IEC 15939 (—) · `skills/systems-engineering/measurement-moe-mop-tpm/SKILL.md`
- **Traceability & Lifecycle Coverage** — ISO/IEC/IEEE 15288 · SEBoK (—) · `skills/systems-engineering/traceability-lifecycle-coverage/SKILL.md`
