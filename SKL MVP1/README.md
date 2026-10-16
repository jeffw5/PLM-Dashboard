# Core vocabularies and taxonomies: SKL MVP1

Version 0.1.0 · Status: Draft · 14 October 2026
Built to *Semantic Governance v1.8 (Draft)*, Sections 3.1–3.10 and Appendix E.

These are the core vocabularies and taxonomies for the Semantic Knowledge Layer. They are the parent artifacts that the core ontology and the unifying ontology will be built from, and every future domain vocabulary, taxonomy, and ontology inherits from them.

| Artifact | Files | Concepts |
|---|---|---|
| Core taxonomies (`taxonomy-core-{name}.ttl`) | 21 | 684 |
| Core vocabularies (`vocabulary-core-{name}.ttl`) | 21 | 456 |
| **Total** | **42** | **1,140** (about 9,000 triples) |

All 42 files passed every check in the "Validation" section below, with zero errors and zero warnings.

## Folder contents

```
SKL MVP1/
├── README.md
├── core/       42 Turtle files, one skos:ConceptScheme each (load these into RDF Studio)
├── bundle/     core-vocabularies-taxonomies.trig — the same content, one named graph per artifact, for loading a graph store such as GraphDB
├── checks/     quality-checks-core.rq — 15 read-only SPARQL checks for the RDF Studio SPARQL panel
└── source/     gen.py and src/*.txt — the authoring source and the generator/validator that produced core/
```

## Loading into RDF Studio

1. Use the **taxonomy import**, not the model import or the mapping import. Load one file at a time. Each file declares exactly one `skos:ConceptScheme`, every concept has `skos:inScheme` and exactly one `skos:prefLabel@en`, and top concepts carry `skos:topConceptOf` (Appendix E, Step 3).
2. Suggested order:
   1. `vocabulary-core-lifecycle.ttl`, because every scheme points to `voc:lifecycle-status-draft`.
   2. `vocabulary-core-governance.ttl`.
   3. The 21 taxonomies.
   4. The remaining vocabularies. Persona goes after the persona taxonomy, and location after the location taxonomy, because their `skos:broadMatch` links point into those taxonomies.

   References between files are plain IRIs, so a file still loads if its targets are not loaded yet.
3. Run each query in `checks/quality-checks-core.rq` in the SPARQL panel. Every check should return no rows.
4. Export from RDF Studio, compare the export with these files to confirm nothing was dropped, then commit with a change record (Appendix E, Step 7).

## Standards applied

| Standard (v1.8) | How it is applied |
|---|---|
| Base URL and URI patterns (3.2) | Taxonomy concepts: `https://www.insperity.com/taxonomy/core/{UpperCamelCase}`. Vocabulary terms: `https://www.insperity.com/vocabulary/core/{lower-hyphenated}`. Personas: `https://www.insperity.com/vocabulary/persona/{UpperCamelCase}`. Slash namespaces, no versions in term IRIs, no hierarchy in paths. |
| No acronyms (3.2, 3.8) | Identifiers and preferred labels are spelled out in full. Acronyms appear only as `skos:altLabel` (for example, "Key performance indicator" with alt label "KPI"). Codes go only in `skos:notation`. |
| Term definition (3.7) | Every concept has one `skos:definition` sentence in genus + differentia form (ISO 704). Each child's definition begins with its parent's label: "A defect in data values or records." Scope notes and examples are added where they help. |
| Labels (3.8) | Sentence case, tagged `@en`. Preferred labels are unique within each scheme, and also across all 21 taxonomies. No alt label collides with a preferred label in its scheme. Misspellings go in `skos:hiddenLabel`. |
| Taxonomy attributes (3.9, ISO 25964) | Each scheme has `dcterms:title`, `dcterms:description`, `owl:versionInfo`, `dcterms:created` and `dcterms:modified`, `dcterms:publisher`, and `skos:hasTopConcept`. Concepts use `skos:broader` and `skos:narrower` for "is a kind of" only. There is no polyhierarchy. Links across schemes use `skos:broadMatch` or `skos:relatedMatch`, never `skos:broader` (Appendix E, Step 3). |
| Governance fields (3.3, 3.7) | Every scheme has `core:hasLifecycleStatus voc:lifecycle-status-draft` and version `0.1.0`. |
| BFO alignment (3.10) | Each scheme names its BFO category and source standards in `dcterms:source`, ready for the core ontology. |

## How these feed the core and unifying ontology

Each scheme carries `dcterms:subject` pointing at the core class it classifies. The next step, `ontology-core-*`, declares these classes, aligns them to BFO, and lets domain classes subclass them. Taxonomy concepts can then be promoted to subclasses where a hierarchy needs OWL semantics.

| Taxonomy | Core class (`dcterms:subject`) | Suggested BFO parent |
|---|---|---|
| asset | `core:Asset` | material entity / generically dependent continuant |
| event | `core:Event` | process boundary |
| issue | `core:Issue` | generically dependent continuant (record of a condition) |
| lifecycle | `core:Lifecycle` | generically dependent continuant (plan specification) |
| party | `core:Party` | object / object aggregate |
| persona | `core:Persona` | generically dependent continuant |
| process | `core:Process` (and `core:ProcessStep`) | process |
| product | `core:Product` | generically dependent continuant (offering specification) |
| requirement | `core:Requirement` | generically dependent continuant |
| role | `core:Role` | role |
| rule, logic, policy | `core:Rule`, `core:Logic`, `core:Policy` | generically dependent continuant (information) |
| measure | `core:Measure` | generically dependent continuant (measurement datum); quality for the measured attribute |
| decision | `core:Decision` | process (act of deciding) plus its information record |
| time | `core:TemporalEntity` | temporal region |
| location | `core:Location` | site / spatial region |
| service | `core:Service` | disposition, realized in process |
| capability | `core:Capability` | disposition / function |
| value | `core:Value` | quality / generically dependent continuant |
| governance | `core:Governance` | process and information (mixed; decide at ontology design) |

The unifying relations in Section 3.1 already have anchor concepts here:

| Unifying relation | Anchor concepts |
|---|---|
| performedBy | `tax:ProcessStep` → roles and parties |
| consumes / produces | asset |
| triggers | event |
| governedBy | policy, `tax:Norm`, rule |
| measuredBy | measure |

## Decisions to confirm

These are the places where v1.8 leaves a choice open or conflicts with itself.

1. **One namespace for all core taxonomies.** All 21 taxonomies share `/taxonomy/core/`, which follows the `{domain}` pattern with `core` as the domain. Concept names are therefore unique across all of them; the validator enforces this. The alternative is one namespace per taxonomy, such as `/taxonomy/core-asset/`, which v1.8 does not define.
2. **Vocabulary term IRIs** are lower-hyphenated with a value-set prefix (for example `voc:lifecycle-status-draft` and `voc:classification-internal`), because "Draft", "High", and "Active" recur across value sets. The v1.8 examples use `core:Draft`, `core:Internal`, and `core:Passed` in the ontology namespace. I recommend the ontology reference these vocabulary IRIs instead, and that the examples be updated.
3. **Persona identifiers.** v1.8 shows `persona:HRSpecialist` and `persona:ClientHRAdministrator`, which put acronyms in identifiers and contradict Section 3.2. These files use `persona:HumanResourcesSpecialist` and `persona:ClientHumanResourcesAdministrator`, with "HR specialist" and "Client HR administrator" as alt labels. Personas follow the individual naming rule (UpperCamelCase); all other vocabulary terms follow the vocabulary URI pattern (lower-hyphenated).
4. **Core properties referenced before they exist.** `core:hasLifecycleStatus`, `core:hasExpertiseLevel`, `core:usesChannel`, and `core:Persona` are used here as Sections 3.7 and 3.8 name them. They need declaring in `ontology-core`.
5. **`owl:versionIRI`** is left for the release pipeline to stamp on vocabulary releases. Putting it on a `skos:ConceptScheme` now would let an OWL reasoner infer the scheme is an `owl:Ontology`.
6. **Time.** The core class is named `core:TemporalEntity`, after W3C OWL-Time, because the v1.8 core list says only "Time". Rename it if you prefer `core:Time`.
7. **Business-specific concepts in the core.** The core includes co-employer, worksite employee, plan roles, human resources services, and the 12 MVP1 personas, because they are business-wide at Insperity. Domain ontologies specialize them. Move any of them to a domain if you want the core strictly domain-neutral.
8. **Top concepts that are not kinds of the subject.** Some top concepts classify the subject area rather than being kinds of the core class:
   - Target, Threshold, Observation, and Calculation under measure
   - Decision model under decision
   - Value stream and Value proposition under value
   - Governance record under governance

   Their children are strict kinds of them. Definitions that do not start with the scheme's own genus are flagged `genus: ok` in the source.
9. **Jurisdictions.** The federal jurisdiction and the 50 states plus the District of Columbia are siblings, because `skos:broader` is for classification only. The legal containment of a state within the United States belongs in the ontology as `locatedIn`. ISO 3166 codes go in typed `skos:notation`, and the IRIs use full names such as `voc:jurisdiction-texas`.

## Validation

`source/gen.py` validates every file as it generates it, then re-parses the Turtle it wrote. The checks:

- **Syntax:** every file re-parses as Turtle, and every prefix is declared.
- **Structure:**
  - exactly one `skos:ConceptScheme` per file
  - one `prefLabel@en` per concept
  - every concept has a definition and `inScheme`
  - every concept has either `broader` or `topConceptOf`
  - `hasTopConcept` and `topConceptOf` agree
  - no `skos:broader` crosses files
- **Naming:**
  - UpperCamelCase for taxonomy concepts and personas, lower-hyphenated for vocabulary terms
  - all IRIs under the base URL
  - no acronyms in preferred labels or identifiers
  - sentence case
- **Labels:** preferred labels unique per scheme, and globally across taxonomies; no alt label collides with a preferred label.
- **Definitions:** "A/An …" form, one sentence, and the genus matches the parent label.
- **Links:** every `broadMatch`, `relatedMatch`, and property target resolves to a term in this set.

Result: 42 files, 1,140 concepts, 0 errors, 0 warnings.

## Making changes

Edit `source/src/*.txt`, then run `python3 source/gen.py source/src core`. The source format is one concept per line:

```
Label :: Definition. || alt: Synonym; ACRONYM || scope: … || ex: … || relm: tax:OtherConcept
```

Indent children by two spaces under their parent. After a release, follow change control (Section 3.3): bump `VERSION` in `gen.py`, deprecate rather than delete, and record the change.
