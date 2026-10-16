#!/usr/bin/env python3
"""Generate SKOS Turtle files for the core vocabularies and taxonomies
from the compact source DSL, following Semantic Governance v1.8
(Sections 3.2, 3.7, 3.8, 3.9; Appendix E Step 3), and validate them.

Usage: python3 gen.py SRC_DIR OUT_DIR
"""
import re, sys, os, glob, json, datetime

BASE = "https://www.insperity.com"
NS = {
    "core":    f"{BASE}/ontology/core/",
    "tax":     f"{BASE}/taxonomy/core/",
    "voc":     f"{BASE}/vocabulary/core/",
    "persona": f"{BASE}/vocabulary/persona/",
    "skos":    "http://www.w3.org/2004/02/skos/core#",
    "dcterms": "http://purl.org/dc/terms/",
    "owl":     "http://www.w3.org/2002/07/owl#",
    "rdfs":    "http://www.w3.org/2000/01/rdf-schema#",
    "rdf":     "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
    "xsd":     "http://www.w3.org/2001/XMLSchema#",
}
TODAY = "2026-10-14"
VERSION = "0.1.0"
STATUS = "voc:lifecycle-status-draft"

ERR, WARN = [], []
def err(m): ERR.append(m)
def warn(m): WARN.append(m)

def camel(label):
    words = re.split(r"[^A-Za-z0-9]+", label)
    return "".join(w[:1].upper() + w[1:] for w in words if w)

def kebab(label):
    return "-".join(w.lower() for w in re.split(r"[^A-Za-z0-9]+", label) if w)

def lit(s, lang="en"):
    s = s.replace("\\", "\\\\").replace('"', '\\"')
    return f'"{s}"@{lang}' if lang else f'"{s}"'

# ---------------------------------------------------------------- parsing
class Node:
    def __init__(self, label, fields, depth, line):
        self.label, self.f, self.depth, self.line = label, fields, depth, line
        self.parent, self.children, self.id, self.prefix = None, [], None, None

def parse_file(path):
    blocks, cur = [], None
    for ln, raw in enumerate(open(path, encoding="utf-8"), 1):
        line = raw.rstrip("\n")
        if not line.strip() or line.lstrip().startswith("#"):
            continue
        m = re.match(r"^=== (taxonomy|vocabulary) (\S+)\s*$", line)
        if m:
            cur = {"kind": m.group(1), "name": m.group(2), "hdr": {}, "datatypes": [],
                   "nodes": [], "in_body": False, "src": f"{os.path.basename(path)}:{ln}"}
            blocks.append(cur); continue
        if cur is None: err(f"{path}:{ln} content before block"); continue
        if line.strip() == "---":
            cur["in_body"] = True; continue
        if not cur["in_body"]:
            k, _, v = line.partition(":")
            k, v = k.strip(), v.strip()
            if k == "datatype":
                cur["datatypes"].append([x.strip() for x in v.split("|")])
            else:
                cur["hdr"][k] = v
            continue
        indent = len(line) - len(line.lstrip(" "))
        if indent % 2: err(f"{path}:{ln} odd indent")
        body = line.strip()
        label, sep, rest = body.partition(" :: ")
        if not sep: err(f"{path}:{ln} missing ' :: '"); continue
        parts = [p.strip() for p in rest.split(" || ")]
        fields = {"def": parts[0]}
        for p in parts[1:]:
            k, _, v = p.partition(":")
            fields[k.strip()] = v.strip()
        cur["nodes"].append(Node(label.strip(), fields, indent // 2, f"{os.path.basename(path)}:{ln}"))
    return blocks

def build_tree(b):
    stack, tops = [], []
    for n in b["nodes"]:
        while stack and stack[-1].depth >= n.depth: stack.pop()
        if n.depth == 0: tops.append(n)
        else:
            if not stack or stack[-1].depth != n.depth - 1:
                err(f"{n.line} bad nesting"); continue
            n.parent = stack[-1]; stack[-1].children.append(n)
        stack.append(n)
    b["tops"] = tops

def assign_ids(b):
    for n in b["nodes"]:
        ns = n.f.get("ns")
        if b["kind"] == "taxonomy":
            n.qn = "tax:" + (n.f.get("id") or camel(n.label))
        else:
            # value-set prefixes: a heading may declare 'prefix:'; children inherit
            p = n.parent
            inherited = None
            while p is not None:
                if p.f.get("prefix"): inherited = p.f["prefix"]; break
                p = p.parent
            if n.f.get("id"):
                local = n.f["id"]
            elif inherited:
                local = f"{inherited}-{kebab(n.label)}"
            else:
                local = kebab(n.label)
            n.qn = (ns or "voc") + ":" + local

# ---------------------------------------------------------------- emit
def emit(b, registry):
    kind, name, h = b["kind"], b["name"], b["hdr"]
    if kind == "taxonomy":
        scheme = "tax:" + camel(name) + "Taxonomy"
    else:
        scheme = f"voc:{name}-vocabulary"
    b["scheme"] = scheme
    used = {"core", "skos", "dcterms", "owl", "rdfs", "xsd", "voc"}
    used.add("tax" if kind == "taxonomy" else "voc")
    out = []
    title = h.get("title")
    out.append(f"# {'Taxonomy' if kind=='taxonomy' else 'Vocabulary'}: {title}")
    out.append(f"# File: {kind}-core-{name}.ttl   Version {VERSION}   Status: Draft")
    out.append("# Conforms to Semantic Governance v1.8 (Sections 3.2, 3.7, 3.8, 3.9; Appendix E Step 3).")
    out.append("# One skos:ConceptScheme per file; load through RDF Studio's taxonomy import.")
    out.append("")
    body = []
    # scheme
    S = [f"{scheme} a skos:ConceptScheme ;",
         f"    dcterms:title {lit(title)} ;",
         f"    skos:prefLabel {lit(title)} ;",
         f"    dcterms:description {lit(h['description'])} ;"]
    if h.get("subject"):
        S.append(f"    dcterms:subject core:{h['subject']} ;")
    if h.get("scope"):
        S.append(f"    skos:scopeNote {lit(h['scope'])} ;")
    if h.get("standard"):
        S.append(f"    dcterms:source {lit(h['standard'])} ;")
    S += [f"    dcterms:publisher {lit('Architecture')} ;",
          f"    dcterms:creator {lit('Knowledge Engineering')} ;",
          f'    dcterms:created "{TODAY}"^^xsd:date ;',
          f'    dcterms:modified "{TODAY}"^^xsd:date ;',
          f'    owl:versionInfo "{VERSION}" ;',
          f"    core:hasLifecycleStatus {STATUS} ;",
          "    skos:hasTopConcept " + " ,\n        ".join(t.qn for t in b["tops"]) + " ."]
    body.append("\n".join(S))
    # datatypes for notations
    for dt in b["datatypes"]:
        local, label, definition = dt
        body.append("\n".join([
            f"voc:{local} a rdfs:Datatype ;",
            f"    rdfs:label {lit(label)} ;",
            f"    skos:definition {lit(definition)} ;",
            f"    rdfs:isDefinedBy {scheme} ."]))
        registry["datatypes"].add(f"voc:{local}")
    # concepts
    for n in b["nodes"]:
        types = ["skos:Concept"]
        if n.f.get("type"):
            types.append(n.f["type"])
        L = [f"{n.qn} a {', '.join(types)} ;",
             f"    skos:prefLabel {lit(n.label)} ;"]
        if n.f.get("alt"):
            L.append("    skos:altLabel " + " , ".join(lit(a.strip()) for a in n.f["alt"].split(";")) + " ;")
        if n.f.get("hidden"):
            L.append("    skos:hiddenLabel " + " , ".join(lit(a.strip()) for a in n.f["hidden"].split(";")) + " ;")
        if n.f.get("notation"):
            dt = n.f.get("ndt") or inherited_field(n, "ndt")
            dts = f"^^voc:{dt}" if dt else ""
            L.append(f'    skos:notation "{n.f["notation"]}"{dts} ;')
        L.append(f"    skos:definition {lit(n.f['def'])} ;")
        if n.f.get("scope"):
            L.append(f"    skos:scopeNote {lit(n.f['scope'])} ;")
        if n.f.get("ex"):
            L.append(f"    skos:example {lit(n.f['ex'])} ;")
        if n.parent is None:
            L.append(f"    skos:topConceptOf {scheme} ;")
        else:
            L.append(f"    skos:broader {n.parent.qn} ;")
        if n.children:
            L.append("    skos:narrower " + " , ".join(c.qn for c in n.children) + " ;")
        for key, prop in (("rel", "skos:related"), ("relm", "skos:relatedMatch"),
                          ("bm", "skos:broadMatch"), ("cm", "skos:closeMatch"),
                          ("em", "skos:exactMatch")):
            if n.f.get(key):
                targets = [t.strip() for t in n.f[key].split(",")]
                n.f["_" + key] = targets
                L.append(f"    {prop} " + " , ".join(targets) + " ;")
        if n.f.get("props"):
            for pair in n.f["props"].split(";"):
                pr, ob = pair.split()
                n.f.setdefault("_props", []).append(ob)
                L.append(f"    {pr} {ob} ;")
        L.append(f"    skos:inScheme {scheme} .")
        body.append("\n".join(L))
        for t in types[1:]:
            used.add(t.split(":")[0])
        if n.qn.startswith("persona:"): used.add("persona")
        for key in ("rel", "relm", "bm", "cm", "em", "props"):
            for t in n.f.get("_" + key, []):
                used.add(t.split(":")[0])
    used.add("tax") if "tax:" in "\n".join(body) else None
    pref = [f"@prefix {p}: <{NS[p]}> ." for p in
            ["core", "tax", "voc", "persona", "skos", "dcterms", "owl", "rdfs", "xsd"] if p in used]
    return "\n".join(out + pref + [""] + ["\n\n".join(body), ""])

def inherited_field(n, key):
    p = n.parent
    while p is not None:
        if p.f.get(key): return p.f[key]
        p = p.parent
    return None

# ---------------------------------------------------------------- validate
ACR = re.compile(r"\b[A-Z]{2,}\b")
TAX_ID = re.compile(r"^tax:[A-Z][A-Za-z0-9]*$")
VOC_ID = re.compile(r"^voc:[a-z0-9]+(-[a-z0-9]+)*$")
PER_ID = re.compile(r"^persona:[A-Z][A-Za-z0-9]*$")

def validate(blocks, proper_nouns):
    ids = {}
    for b in blocks:
        h = b["hdr"]
        for k in ("title", "description"):
            if not h.get(k): err(f"{b['name']}: header '{k}' missing")
        if not b["tops"]: err(f"{b['name']}: no top concepts")
        prefs = {}
        for n in b["nodes"]:
            if n.qn in ids: err(f"duplicate id {n.qn} ({n.line} and {ids[n.qn]})")
            ids[n.qn] = n.line
            if n.qn.startswith("tax:") and not TAX_ID.match(n.qn): err(f"{n.line} id {n.qn} not UpperCamelCase")
            if n.qn.startswith("voc:") and not VOC_ID.match(n.qn): err(f"{n.line} id {n.qn} not lower-hyphen")
            if n.qn.startswith("persona:") and not PER_ID.match(n.qn): err(f"{n.line} id {n.qn} bad persona id")
            key = n.label.lower()
            if key in prefs: err(f"{n.line} prefLabel '{n.label}' duplicates {prefs[key]} in scheme")
            prefs[key] = n.line
            if ACR.search(n.label): err(f"{n.line} acronym in prefLabel '{n.label}'")
            if not n.label[0].isupper() and not n.label[0].isdigit(): err(f"{n.line} label not sentence case '{n.label}'")
            for w in n.label.split()[1:]:
                if w[:1].isupper() and w not in proper_nouns:
                    warn(f"{n.line} capitalised word '{w}' in '{n.label}' (sentence case?)")
            d = n.f["def"]
            if not re.match(r"^An? ", d) or not d.endswith("."):
                err(f"{n.line} definition not 'A/An ... .' form: {d[:60]}")
            if d.count(". ") > 0:
                warn(f"{n.line} definition may be more than one sentence")
            if n.parent is not None and b["kind"] == "taxonomy":
                genus = n.parent.label.lower()
                if not re.match(rf"^an? {re.escape(genus)}\b", d.lower()) and "genus" not in n.f:
                    warn(f"{n.line} genus mismatch: '{n.label}' def does not start with parent '{genus}'")
        for n in b["nodes"]:
            for a in (n.f.get("alt") or "").split(";"):
                a = a.strip().lower()
                if not a: continue
                if a == n.label.lower(): err(f"{n.line} altLabel repeats own prefLabel")
                elif a in prefs: err(f"{n.line} altLabel '{a}' collides with a prefLabel in scheme")
    for b in blocks:
        for n in b["nodes"]:
            for key in ("rel", "relm", "bm", "cm", "em", "props"):
                for t in n.f.get("_" + key, []):
                    if t not in ids: err(f"{n.line} {key} target {t} not found")
    return ids

# ---------------------------------------------------------------- mini Turtle parser (syntax re-check)
TOK = re.compile(r'''\s*(?:
   (?P<comment>\#[^\n]*)
 | (?P<prefix>@prefix)
 | (?P<iri><[^<>"{}|^`\\\s]*>)
 | (?P<lit>"(?:[^"\\\n]|\\.)*")(?P<lang>@[a-zA-Z]+(?:-[a-zA-Z0-9]+)*)?(?:\^\^(?P<dt>[A-Za-z][\w-]*:[\w-]+|<[^>]+>))?
 | (?P<punct>[;,.])
 | (?P<a>a)(?=\s)
 | (?P<pname>[A-Za-z][\w-]*:(?:[A-Za-z0-9_](?:[\w.-]*[\w-])?)?)
 | (?P<pdecl>[A-Za-z][\w-]*:)
)''', re.X)

def parse_turtle(text, fname):
    pos, toks = 0, []
    while pos < len(text):
        if text[pos:].strip() == "": break
        m = TOK.match(text, pos)
        if not m or m.end() == pos:
            raise SyntaxError(f"{fname}: cannot tokenize at {pos}: {text[pos:pos+40]!r}")
        pos = m.end()
        kind = m.lastgroup if m.lastgroup not in ("lang", "dt") else "lit"
        if m.group("lit") is not None: kind = "lit"
        if kind == "comment": continue
        toks.append((kind, m.group(0).strip()))
    prefixes, triples, i = {}, [], 0
    def term(t):
        k, v = t
        if k == "pname":
            p = v.split(":")[0]
            if p not in prefixes: raise SyntaxError(f"{fname}: undeclared prefix {p}")
            return prefixes[p] + v.split(":", 1)[1]
        if k == "iri": return v[1:-1]
        if k == "lit":
            dm = re.search(r'\^\^([A-Za-z][\w-]*):', v)
            if dm and dm.group(1) not in prefixes: raise SyntaxError(f"{fname}: undeclared prefix {dm.group(1)}")
            return v
        if k == "a": return NS["rdf"] + "type"
        raise SyntaxError(f"{fname}: unexpected token {t}")
    while i < len(toks):
        if toks[i][0] == "prefix":
            pd, iri, dot = toks[i+1], toks[i+2], toks[i+3]
            if pd[0] not in ("pdecl", "pname") or iri[0] != "iri" or dot[1] != ".":
                raise SyntaxError(f"{fname}: bad @prefix near {pd}")
            prefixes[pd[1].rstrip(":")] = iri[1][1:-1]; i += 4; continue
        s = term(toks[i]); i += 1
        while True:
            p = term(toks[i]); i += 1
            while True:
                o = term(toks[i]); i += 1
                triples.append((s, p, o))
                if toks[i][1] == ",": i += 1; continue
                break
            if toks[i][1] == ";": i += 1; continue
            if toks[i][1] == ".": i += 1; break
            raise SyntaxError(f"{fname}: expected ; or . got {toks[i]}")
    return triples

# ---------------------------------------------------------------- graph checks (Appendix E Step 5 equivalents)
def graph_checks(fname, triples):
    T = NS["rdf"] + "type"; SK = NS["skos"]
    schemes = {s for s, p, o in triples if p == T and o == SK + "ConceptScheme"}
    if len(schemes) != 1: err(f"{fname}: {len(schemes)} ConceptSchemes (must be exactly 1)")
    concepts = {s for s, p, o in triples if p == T and o == SK + "Concept"}
    by = {}
    for s, p, o in triples: by.setdefault((s, p), []).append(o)
    for c in concepts:
        pl = [o for o in by.get((c, SK + "prefLabel"), []) if o.endswith("@en")]
        if len(pl) != 1: err(f"{fname}: {c} has {len(pl)} @en prefLabels")
        if not by.get((c, SK + "definition")): err(f"{fname}: {c} no definition")
        if by.get((c, SK + "inScheme")) != list(schemes): err(f"{fname}: {c} inScheme wrong")
        if not (by.get((c, SK + "broader")) or by.get((c, SK + "topConceptOf"))):
            err(f"{fname}: {c} neither broader nor topConceptOf")
        for b in by.get((c, SK + "broader"), []):
            if b not in concepts: err(f"{fname}: {c} broader {b} not in file (use broadMatch)")
    sch = next(iter(schemes))
    tops = set(by.get((sch, SK + "hasTopConcept"), []))
    tco = {s for s, p, o in triples if p == SK + "topConceptOf"}
    if tops != tco: err(f"{fname}: hasTopConcept / topConceptOf mismatch")
    for s, p, o in triples:
        for x in (s, o):
            if x.startswith("http") and "insperity" in x and not x.startswith(BASE + "/"):
                err(f"{fname}: IRI outside base {x}")
    return len(concepts)

def main(src, out):
    os.makedirs(out, exist_ok=True)
    blocks = []
    for f in sorted(glob.glob(os.path.join(src, "*.txt"))):
        blocks += parse_file(f)
    proper = set(open(os.path.join(src, "proper_nouns.lst")).read().split())
    for b in blocks: build_tree(b); assign_ids(b)
    registry = {"datatypes": set()}
    texts = {}
    for b in blocks:
        texts[f"{b['kind']}-core-{b['name']}.ttl"] = emit(b, registry)
    validate(blocks, proper)
    summary = []
    for fn, txt in sorted(texts.items()):
        try:
            tr = parse_turtle(txt, fn)
            nc = graph_checks(fn, tr)
            summary.append((fn, nc, len(tr)))
        except SyntaxError as e:
            err(str(e))
        with open(os.path.join(out, fn), "w", encoding="utf-8") as fh:
            fh.write(txt)
    # manifest json for README build
    man = []
    for b in blocks:
        man.append({"file": f"{b['kind']}-core-{b['name']}.ttl", "kind": b["kind"], "name": b["name"],
                    "title": b["hdr"]["title"], "scheme": b["scheme"], "subject": b["hdr"].get("subject"),
                    "concepts": len(b["nodes"]), "tops": [t.label for t in b["tops"]],
                    "depth": max(n.depth for n in b["nodes"]) + 1})
    json.dump(man, open(os.path.join(out, "_manifest.json"), "w"), indent=1)
    print("FILES", len(summary), "CONCEPTS", sum(s[1] for s in summary), "TRIPLES", sum(s[2] for s in summary))
    for s in summary: print(f"  {s[0]:45s} {s[1]:4d} concepts {s[2]:5d} triples")
    print(f"\nERRORS {len(ERR)}"); [print("  E", e) for e in ERR]
    print(f"WARNINGS {len(WARN)}"); [print("  W", w) for w in WARN]
    return 1 if ERR else 0

if __name__ == "__main__":
    sys.exit(main(sys.argv[1], sys.argv[2]))
