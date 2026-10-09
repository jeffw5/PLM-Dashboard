#!/usr/bin/env python3
"""
Generates world_model_dashboard.html from output/world_model_results.json
and output/world_model_audit.json. Run run_world_model.py first.

The generated page is a SELF-CONTAINED artifact: no external scripts (an
Artifact-published page blocks every external host except Google Fonts),
so all charts here are hand-built inline SVG, not Chart.js.
"""
import json
import os

BASE = os.path.dirname(__file__)
with open(os.path.join(BASE, "output", "world_model_results.json")) as f:
    RESULTS = json.load(f)
with open(os.path.join(BASE, "output", "world_model_audit.json")) as f:
    AUDIT = json.load(f)

DATA_JSON = json.dumps(RESULTS)
AUDIT_JSON = json.dumps(AUDIT)

HTML_TEMPLATE = r"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>World Model — Causal Decision Impact Explorer</title>
<style>
:root{
  --bg:#f5f6f8; --panel:#ffffff; --panel-2:#fafbfc; --text:#1a1d23; --muted:#656b76;
  --border:#e1e4e9; --accent:#3b6fd6; --accent-2:#6a8fe0; --good:#2e8b57; --bad:#c0392b;
  --warn:#c98a1f; --chip-bg:#eef1f6; --shadow:0 1px 3px rgba(0,0,0,0.06);
  --mono:ui-monospace,SFMono-Regular,Menlo,Consolas,monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --bg:#15171c; --panel:#1d2026; --panel-2:#20242b; --text:#e7e9ee; --muted:#9aa0ab;
    --border:#2c3038; --accent:#6a8fe0; --accent-2:#3b6fd6; --good:#52c285; --bad:#e2695c;
    --warn:#e0a94a; --chip-bg:#262a32; --shadow:0 1px 3px rgba(0,0,0,0.4);
  }
}
:root[data-theme="dark"]{
  --bg:#15171c; --panel:#1d2026; --panel-2:#20242b; --text:#e7e9ee; --muted:#9aa0ab;
  --border:#2c3038; --accent:#6a8fe0; --accent-2:#3b6fd6; --good:#52c285; --bad:#e2695c;
  --warn:#e0a94a; --chip-bg:#262a32; --shadow:0 1px 3px rgba(0,0,0,0.4);
}
*{box-sizing:border-box;}
body{margin:0;background:var(--bg);color:var(--text);font:14px/1.5 -apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;}
header{position:sticky;top:0;z-index:20;background:var(--panel);border-bottom:1px solid var(--border);padding:10px 20px;display:flex;align-items:center;gap:16px;flex-wrap:wrap;}
header h1{font-size:16px;margin:0;font-weight:650;}
header .tag{font-size:11px;color:var(--bad);border:1px solid var(--bad);border-radius:10px;padding:1px 8px;font-weight:600;letter-spacing:.02em;}
nav{display:flex;gap:4px;margin-left:auto;flex-wrap:wrap;}
nav button{background:none;border:1px solid transparent;color:var(--muted);padding:6px 12px;border-radius:7px;cursor:pointer;font-size:13px;font-weight:500;}
nav button:hover{background:var(--chip-bg);color:var(--text);}
nav button.active{background:var(--accent);color:#fff;}
#themeToggle{border:1px solid var(--border);background:var(--panel-2);color:var(--text);border-radius:7px;padding:5px 10px;cursor:pointer;font-size:12px;}
main{max-width:1180px;margin:0 auto;padding:20px;}
.panel{display:none;}
.panel.active{display:block;}
.card{background:var(--panel);border:1px solid var(--border);border-radius:10px;padding:16px 18px;margin-bottom:16px;box-shadow:var(--shadow);}
.card h2{margin:0 0 10px;font-size:15px;}
.card h3{margin:14px 0 8px;font-size:13px;color:var(--muted);text-transform:uppercase;letter-spacing:.04em;}
.disclaimer{background:linear-gradient(180deg,var(--chip-bg),var(--panel));border:1px solid var(--warn);border-left:4px solid var(--warn);border-radius:8px;padding:12px 16px;font-size:13px;margin-bottom:16px;}
.disclaimer b{color:var(--warn);}
p.lead{color:var(--muted);font-size:13.5px;}
.grid-sectors{display:grid;grid-template-columns:repeat(auto-fill,minmax(230px,1fr));gap:10px;margin-top:10px;}
.sector-chip{border-radius:8px;padding:10px 12px;border:1px solid var(--border);cursor:pointer;background:var(--panel-2);}
.sector-chip .dot{width:9px;height:9px;border-radius:50%;display:inline-block;margin-right:6px;}
.sector-chip .n{float:right;color:var(--muted);font-size:11.5px;}
table{width:100%;border-collapse:collapse;font-size:13px;}
table th{text-align:left;color:var(--muted);font-weight:600;font-size:11.5px;text-transform:uppercase;letter-spacing:.03em;border-bottom:1px solid var(--border);padding:7px 8px;cursor:pointer;user-select:none;white-space:nowrap;}
table th:hover{color:var(--text);}
table th.sort-asc::after{content:" \25B2";}
table th.sort-desc::after{content:" \25BC";}
table td{padding:7px 8px;border-bottom:1px solid var(--border);vertical-align:top;}
table tr.clickable{cursor:pointer;}
table tr.clickable:hover td{background:var(--chip-bg);}
.badge{display:inline-block;padding:1px 8px;border-radius:9px;font-size:11px;font-weight:600;}
.badge.high{background:rgba(192,57,43,.15);color:var(--bad);}
.badge.moderate{background:rgba(201,138,31,.16);color:var(--warn);}
.badge.low{background:rgba(58,110,214,.15);color:var(--accent);}
.badge.negligible{background:var(--chip-bg);color:var(--muted);}
.badge.hyp{background:rgba(201,138,31,.18);color:var(--warn);border:1px solid var(--warn);}
.pill{display:inline-block;background:var(--chip-bg);border:1px solid var(--border);border-radius:6px;padding:1px 7px;font-size:11.5px;color:var(--muted);margin-right:4px;}
.mono{font-family:var(--mono);font-size:12px;}
.muted{color:var(--muted);}
.rangebar{position:relative;height:16px;background:var(--chip-bg);border-radius:4px;min-width:140px;}
.rangebar .track{position:absolute;top:6px;height:4px;border-radius:2px;background:var(--border);}
.rangebar .mean{position:absolute;top:2px;width:2px;height:12px;border-radius:1px;}
.tabs-inner{display:flex;gap:6px;margin-bottom:12px;flex-wrap:wrap;}
.tabs-inner button{background:var(--panel-2);border:1px solid var(--border);color:var(--muted);padding:5px 11px;border-radius:7px;cursor:pointer;font-size:12.5px;}
.tabs-inner button.active{background:var(--accent);color:#fff;border-color:var(--accent);}
.decision-card{border:1px solid var(--border);border-radius:9px;padding:14px;margin-bottom:12px;background:var(--panel-2);}
.decision-card h3{margin:0 0 4px;font-size:14px;color:var(--text);text-transform:none;letter-spacing:0;}
.decision-card .meta{font-size:12px;color:var(--muted);margin-bottom:8px;}
.decision-card button.go{background:var(--accent);color:#fff;border:none;border-radius:6px;padding:5px 11px;font-size:12px;cursor:pointer;}
.concept-card{border:1px solid var(--border);border-radius:8px;padding:10px 12px;background:var(--panel-2);cursor:pointer;margin-bottom:8px;}
.concept-card b{font-size:13px;}
.concept-card p{margin:4px 0 0;font-size:12.5px;color:var(--muted);}
#overlay{position:fixed;inset:0;background:rgba(0,0,0,.35);display:none;z-index:40;}
#drawer{position:fixed;top:0;right:-440px;width:420px;max-width:92vw;height:100%;background:var(--panel);border-left:1px solid var(--border);box-shadow:-6px 0 24px rgba(0,0,0,.2);z-index:41;transition:right .18s ease;overflow-y:auto;padding:18px;}
#drawer.open{right:0;}
#drawer h2{margin:0 0 10px;font-size:15px;}
#drawer .close{position:absolute;top:14px;right:14px;cursor:pointer;color:var(--muted);font-size:18px;background:none;border:none;}
#drawer dl{margin:0;}
#drawer dt{font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em;margin-top:10px;}
#drawer dd{margin:2px 0 0;font-size:13px;}
#drawer pre{background:var(--panel-2);border:1px solid var(--border);border-radius:6px;padding:8px;font-size:11.5px;overflow-x:auto;white-space:pre-wrap;word-break:break-word;}
.path-chain{font-size:12.5px;line-height:1.7;}
.path-chain .step{display:block;padding:6px 10px;border-left:2px solid var(--accent);margin-bottom:4px;background:var(--panel-2);border-radius:0 6px 6px 0;}
footer{max-width:1180px;margin:0 auto;padding:18px 20px 60px;color:var(--muted);font-size:12px;}
.flex-between{display:flex;justify-content:space-between;align-items:baseline;flex-wrap:wrap;gap:8px;}
.search-box{background:var(--panel-2);border:1px solid var(--border);border-radius:7px;padding:5px 10px;font-size:12.5px;color:var(--text);width:220px;}
</style>
</head>
<body>
<div id="overlay"></div>
<div id="drawer"><button class="close" id="drawerClose">&times;</button><div id="drawerContent"></div></div>

<header>
  <h1>World Model</h1>
  <span class="tag">ILLUSTRATIVE — NOT REAL-WORLD DATA</span>
  <nav id="tabNav"></nav>
  <button id="themeToggle">Theme</button>
</header>

<main>
  <div class="disclaimer">
    <b>What this is:</b> an architecture demonstration of a causal, Bayesian-uncertain decision-impact model
    spanning 9 sectors and several illustrative country/company actors — built so a future real build has a
    schema to fill with sourced data. <b>What this is not:</b> a validated forecasting system, a set of real
    national statistics, or a channel that contacts or alerts any real person or institution. Every number you
    see here is either an illustrative placeholder or an explicitly-uncertain modeled hypothesis — see the
    Overview tab for the full framing, and the assumptions list on every Impact Assessment.
  </div>

  <section id="panel-overview" class="panel active"></section>
  <section id="panel-ontology" class="panel"></section>
  <section id="panel-registry" class="panel"></section>
  <section id="panel-graph" class="panel"></section>
  <section id="panel-decisions" class="panel"></section>
  <section id="panel-impact" class="panel"></section>
  <section id="panel-audit" class="panel"></section>
</main>

<footer>
  World Model v1 — architecture demo, illustrative data throughout. Part of the Assembly Decision Engine family.
  Simulation: __N_SIM__ draws/decision, seed __SEED__.
</footer>

<script id="world-model-data" type="application/json">__DATA_JSON__</script>
<script id="world-model-audit" type="application/json">__AUDIT_JSON__</script>
<script>
const DATA = JSON.parse(document.getElementById('world-model-data').textContent);
const AUDIT = JSON.parse(document.getElementById('world-model-audit').textContent);

// ---------- theme ----------
(function(){
  let saved = null;
  try { saved = localStorage.getItem('wm-theme'); } catch(e) {}
  if (saved) document.documentElement.setAttribute('data-theme', saved);
  document.getElementById('themeToggle').addEventListener('click', () => {
    const cur = document.documentElement.getAttribute('data-theme');
    const next = cur === 'dark' ? 'light' : 'dark';
    document.documentElement.setAttribute('data-theme', next);
    try { localStorage.setItem('wm-theme', next); } catch(e) {}
  });
})();

// ---------- tabs ----------
const TABS = [
  ['overview','Overview'], ['ontology','Ontology'], ['registry','Registry'],
  ['graph','Causal Graph'], ['decisions','Decisions'], ['impact','Impact Assessments'],
  ['audit','Audit Trail'],
];
const nav = document.getElementById('tabNav');
TABS.forEach(([id,label],i)=>{
  const b = document.createElement('button');
  b.textContent = label; b.dataset.tab = id;
  if(i===0) b.classList.add('active');
  b.addEventListener('click', ()=> showTab(id));
  nav.appendChild(b);
});
function showTab(id){
  document.querySelectorAll('nav#tabNav button').forEach(b=>b.classList.toggle('active', b.dataset.tab===id));
  document.querySelectorAll('main .panel').forEach(p=>p.classList.toggle('active', p.id==='panel-'+id));
  window.scrollTo({top:0, behavior:'instant'});
}

// ---------- drawer (Inspector) ----------
const drawer = document.getElementById('drawer');
const overlay = document.getElementById('overlay');
function openDrawer(html){
  document.getElementById('drawerContent').innerHTML = html;
  drawer.classList.add('open'); overlay.style.display = 'block';
}
function closeDrawer(){ drawer.classList.remove('open'); overlay.style.display='none'; }
document.getElementById('drawerClose').addEventListener('click', closeDrawer);
overlay.addEventListener('click', closeDrawer);

function esc(s){ return String(s).replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c])); }
function fmt(n, d=2){ return (typeof n === 'number') ? n.toFixed(d) : n; }

// ---------- event delegation for data-inspect ----------
document.addEventListener('click', (e) => {
  const el = e.target.closest('[data-inspect]');
  if(!el) return;
  try {
    const payload = JSON.parse(el.getAttribute('data-inspect'));
    renderInspector(payload);
  } catch(err) { console.error('inspect parse failed', err); }
});

function renderInspector(p){
  let html = `<h2>${esc(p.title||'Detail')}</h2>`;
  if(p.subtitle) html += `<p class="muted">${esc(p.subtitle)}</p>`;
  if(p.badges){ html += p.badges.map(b=>`<span class="badge ${esc(b.cls)}">${esc(b.text)}</span> `).join(''); }
  if(p.fields){
    html += '<dl>';
    p.fields.forEach(([k,v])=>{ html += `<dt>${esc(k)}</dt><dd>${v}</dd>`; });
    html += '</dl>';
  }
  if(p.pathChain && p.pathChain.length){
    html += '<dt style="font-size:11px;color:var(--muted);text-transform:uppercase;letter-spacing:.03em;margin-top:14px;">Dominant Causal Path</dt>';
    html += '<div class="path-chain">' + p.pathChain.map(s=>`<span class="step">${s}</span>`).join('') + '</div>';
  }
  if(p.raw){
    html += `<dt style="margin-top:14px;">Raw</dt><pre>${esc(JSON.stringify(p.raw, null, 2))}</pre>`;
  }
  renderInspectorRaw(html);
}
function renderInspectorRaw(html){ openDrawer(html); }

// =====================================================================
// OVERVIEW
// =====================================================================
(function(){
  const el = document.getElementById('panel-overview');
  const sectors = DATA.ontology.sectors;
  const sectorCounts = {};
  DATA.ontology.state_variables.forEach(v => sectorCounts[v.sector] = (sectorCounts[v.sector]||0)+1);

  let html = `
  <div class="card">
    <h2>What is a World Model, here?</h2>
    <p class="lead">This extends the Assembly Decision Engine's pattern — primitives + Bayesian beliefs + Monte
    Carlo + an immutable audit trail — from a single company's strategy decisions to a <b>causal graph spanning
    multiple sectors and multiple countries/companies</b>. A decision by one actor (a government or a company)
    is modeled as an origin shock to one of its own state variables; the graph then propagates that shock outward
    — within that actor's own sectors, and across borders through illustrative trade-dependency links — producing
    a Monte Carlo distribution of effects on every variable it reaches, each with an explicit uncertainty band.</p>
    <p class="lead"><b>The deliberate scope limit:</b> this produces an <i>Impact Assessment artifact</i> — a
    disclosure report with assumptions, confidence, and causal-path explanations attached — for a human to read
    and share through their own channels. It does not contact real leaders, does not assert a decision should be
    opposed, and has no such channel. Treat every causal edge as "a reasonable analyst's starting prior," not
    an established fact.</p>
  </div>

  <div class="card">
    <h2>Four things that make this trustworthy to read, not just impressive to look at</h2>
    <div class="concept-card" data-inspect='${esc(JSON.stringify({title:'Illustrative data, honestly labeled', fields:[["Where", "Registry (countries/companies) + all baseline statistics"],["Why it matters","Every number is directionally plausible but not sourced or current — replacing them with real World Bank / IMF / OECD / WHO statistics is the obvious next step before this is used for anything beyond demonstrating the architecture."]]}))}'>
    <b>1. Illustrative data, honestly labeled</b><p>Country/company baselines are placeholders, flagged everywhere they appear.</p></div>
    <div class="concept-card" data-inspect='${esc(JSON.stringify({title:'Expert-elicited causal edges, not fitted ones', fields:[["Representation","Each edge is a NormalBelief(mean coefficient, sigma) — a standardized path coefficient with an explicit uncertainty band"],["Why it matters","No statistical fitting or causal inference was run against real data. Each edge is a sourced hypothesis a domain expert should be able to challenge and recalibrate."]]}))}'>
    <b>2. Expert-elicited causal edges, not fitted ones</b><p>Every edge carries a mean effect AND a sigma — sampled fresh each Monte Carlo draw.</p></div>
    <div class="concept-card" data-inspect='${esc(JSON.stringify({title:'Bounded, damped propagation', fields:[["Why damping","The graph has cycles (e.g. energy price → inflation → approval → ... → energy price). Each hop\\'s newly produced effect is multiplied by 0.65 before continuing, and the walk stops after a small number of hops."],["What this means","Without this, a cyclic graph could make a shock grow without bound on paper. This is a modeling safeguard, not an empirical decay rate."]]}))}'>
    <b>3. Bounded, damped propagation</b><p>Cycles in the graph can't make an effect blow up — hops are capped and damped by design.</p></div>
    <div class="concept-card" data-inspect='${esc(JSON.stringify({title:'A content-hashed audit trail', fields:[["What\\'s logged","Every graph build, decision assembly, and propagation run"],["Why it matters","Each event hashes its own inputs/outputs and chains onto the previous event, so the whole run is tamper-evident and byte-for-byte replayable from its seed."]]}))}'>
    <b>4. A content-hashed, replayable audit trail</b><p>Every step of every run is logged, hash-chained, and reproducible from its seed. See the Audit Trail tab.</p></div>
  </div>

  <div class="card">
    <h2>The 9-sector ontology</h2>
    <p class="lead">36 standardized state variables, 4 per sector. Click a sector to jump to its variables.</p>
    <div class="grid-sectors">
      ${Object.entries(sectors).map(([key,s])=>`
        <div class="sector-chip" onclick="showTab('ontology'); setTimeout(()=>filterOntologySector('${key}'),0);">
          <span class="dot" style="background:${s.color}"></span><b>${esc(s.label)}</b><span class="n">${sectorCounts[key]||0} vars</span>
        </div>`).join('')}
    </div>
  </div>

  <div class="card">
    <h2>Model coverage, at a glance</h2>
    <table><tbody>
      <tr><td>Countries modeled</td><td>${Object.keys(DATA.registry.countries).length}</td></tr>
      <tr><td>Companies modeled (fictional)</td><td>${Object.keys(DATA.registry.companies).length}</td></tr>
      <tr><td>Bilateral trade-dependency links</td><td>${DATA.registry.trade_links.length}</td></tr>
      <tr><td>Within-country causal mechanism templates</td><td>${DATA.causal_graph.mechanism_templates.length}</td></tr>
      <tr><td>Total causal edges instantiated</td><td>${DATA.causal_graph.n_total_edges} (${DATA.causal_graph.n_within_country_edges} within-country + ${DATA.causal_graph.n_cross_country_edges} cross-country)</td></tr>
      <tr><td>HYPOTHETICAL example decisions</td><td>${DATA.decisions.length}</td></tr>
      <tr><td>Monte Carlo draws per decision</td><td>${DATA.simulation_config.n_simulations.toLocaleString()}</td></tr>
    </tbody></table>
  </div>`;
  el.innerHTML = html;
})();

// =====================================================================
// ONTOLOGY
// =====================================================================
let ontologySectorFilter = null;
function filterOntologySector(sector){
  ontologySectorFilter = sector;
  renderOntology();
}
function renderOntology(){
  const el = document.getElementById('panel-ontology');
  const sectors = DATA.ontology.sectors;
  const vars = DATA.ontology.state_variables;
  let html = `<div class="card"><h2>Ontology — 9 sectors × 4 state variables</h2>
    <p class="lead">Each variable carries an illustrative "typical move" scale (its own units) — the normalization
    convention that lets causal edges connect variables with different units, the same way standardized path
    coefficients work in SEM/regression. Click any row for full detail.</p>
    <div class="tabs-inner" id="ontoSectorTabs">
      <button data-s="__all__" class="${ontologySectorFilter===null?'active':''}">All</button>
      ${Object.entries(sectors).map(([k,s])=>`<button data-s="${k}" class="${ontologySectorFilter===k?'active':''}" style="border-color:${s.color}">${esc(s.label)}</button>`).join('')}
    </div>
    <table><thead><tr><th>Sector</th><th>Variable</th><th>Unit</th><th>Typical move</th><th>Higher = better?</th></tr></thead><tbody>
    ${vars.filter(v=>!ontologySectorFilter || v.sector===ontologySectorFilter).map(v=>{
      const s = sectors[v.sector];
      const hib = v.higher_is_better === true ? 'Yes' : v.higher_is_better === false ? 'No' : '—';
      const payload = {title:v.label, subtitle:v.key, badges:[{cls:'low',text:s.label}],
        fields:[["Description",esc(v.description)],["Unit",esc(v.unit)],["Typical move (normalization scale)",v.typical_move],["Higher is better?",hib]]};
      return `<tr class="clickable" data-inspect='${esc(JSON.stringify(payload))}'>
        <td><span class="dot" style="display:inline-block;width:8px;height:8px;border-radius:50%;background:${s.color};margin-right:6px;"></span>${esc(s.label)}</td>
        <td><b>${esc(v.label)}</b><div class="muted mono" style="font-size:11px;">${esc(v.key)}</div></td>
        <td>${esc(v.unit)}</td><td>${v.typical_move}</td><td>${hib}</td>
      </tr>`;
    }).join('')}
    </tbody></table>
  </div>`;
  el.innerHTML = html;
  document.querySelectorAll('#ontoSectorTabs button').forEach(b=>{
    b.addEventListener('click', ()=>{ ontologySectorFilter = b.dataset.s==='__all__'?null:b.dataset.s; renderOntology(); });
  });
}
renderOntology();

// =====================================================================
// REGISTRY
// =====================================================================
(function(){
  const el = document.getElementById('panel-registry');
  const sectors = DATA.ontology.sectors;
  const varByKey = {}; DATA.ontology.state_variables.forEach(v=>varByKey[v.key]=v);

  function actorCard(id, actor){
    const rows = Object.entries(actor.baseline).map(([k,v])=>{
      const def = varByKey[k]; if(!def) return '';
      return `<tr><td><span class="dot" style="display:inline-block;width:7px;height:7px;border-radius:50%;background:${sectors[def.sector].color};margin-right:5px;"></span>${esc(def.label)}</td><td class="mono">${v}</td><td class="muted">${esc(def.unit)}</td></tr>`;
    }).join('');
    const payload = {title:actor.name, subtitle:(actor.region||actor.kind), fields:[["Description",esc(actor.description)]], raw:actor.baseline};
    return `<div class="decision-card">
      <div class="flex-between"><h3 style="margin:0;">${esc(actor.name)}</h3><span class="pill">${esc(actor.region||actor.kind)}</span></div>
      <div class="meta">${esc(actor.description)}</div>
      <table><tbody>${rows}</tbody></table>
      <div style="margin-top:8px;"><button class="go" data-inspect='${esc(JSON.stringify(payload))}'>Full baseline JSON</button></div>
    </div>`;
  }

  let html = `<div class="card"><h2>Actor registry</h2>
    <p class="lead">${esc(DATA.registry.disclaimer)}</p>
    <h3>Countries (${Object.keys(DATA.registry.countries).length})</h3>
    ${Object.entries(DATA.registry.countries).map(([id,a])=>actorCard(id,a)).join('')}
    <h3>Companies (${Object.keys(DATA.registry.companies).length}, fictional)</h3>
    ${Object.entries(DATA.registry.companies).map(([id,a])=>actorCard(id,a)).join('')}
    </div>
    <div class="card"><h2>Bilateral trade-dependency links</h2>
    <p class="lead">Illustrative, not sourced trade-flow data — used only to generate cross-country causal edges (see Causal Graph tab).</p>
    <table><thead><tr><th>Exporter</th><th>Importer</th><th>Channel</th><th>Dependency share</th><th>Rationale</th></tr></thead><tbody>
    ${DATA.registry.trade_links.map(t=>`<tr><td><b>${esc(t.exporter)}</b></td><td><b>${esc(t.importer)}</b></td><td>${esc(t.channel)}</td><td>${(t.dependency_share*100).toFixed(0)}%</td><td class="muted">${esc(t.rationale)}</td></tr>`).join('')}
    </tbody></table></div>`;
  el.innerHTML = html;
})();

// =====================================================================
// CAUSAL GRAPH
// =====================================================================
(function(){
  const el = document.getElementById('panel-graph');
  let html = `<div class="card"><h2>Expert-elicited mechanism templates (within-country)</h2>
    <p class="lead">Each of these ${DATA.causal_graph.mechanism_templates.length} templates is instantiated once per
    country (${DATA.registry? Object.keys(DATA.registry.countries).length: ''} independent copies, each with its own
    separately-updatable belief) — ${DATA.causal_graph.n_within_country_edges} within-country edges total.
    Coefficients are standardized: "mean" ≈ how many typical-moves the target shifts per typical-move of the source.
    Click a row to see the full rationale.</p>
    <table id="mechTable"><thead><tr>
      <th data-k="source_label">Source</th><th data-k="target_label">Target</th>
      <th data-k="mean_coef">Mean coef.</th><th data-k="sigma_coef">± sigma</th><th data-k="lag">Lag</th>
    </tr></thead><tbody></tbody></table>
  </div>
  <div class="card"><h2>Cross-country edges (generated from trade links)</h2>
    <p class="lead">${DATA.causal_graph.n_cross_country_edges} edges, one per trade link, with
    mean coefficient = channel base rate × dependency share.</p>
    <table id="ccTable"><thead><tr>
      <th data-k="source_actor">Exporter</th><th data-k="target_actor">Importer</th>
      <th data-k="source_var">Source var</th><th data-k="target_var">Target var</th>
      <th data-k="mean">Mean coef.</th><th data-k="sigma">± sigma</th>
    </tr></thead><tbody></tbody></table>
  </div>`;
  el.innerHTML = html;

  function makeSortable(tableId, rows, renderRow, defaultKey){
    let sortKey = defaultKey, sortDir = -1;
    function draw(){
      const sorted = [...rows].sort((a,b)=>{
        const av=a[sortKey], bv=b[sortKey];
        if(typeof av === 'number') return (av-bv)*sortDir;
        return String(av).localeCompare(String(bv))*sortDir;
      });
      document.querySelector(`#${tableId} tbody`).innerHTML = sorted.map(renderRow).join('');
      document.querySelectorAll(`#${tableId} thead th`).forEach(th=>{
        th.classList.remove('sort-asc','sort-desc');
        if(th.dataset.k===sortKey) th.classList.add(sortDir===1?'sort-asc':'sort-desc');
      });
    }
    document.querySelectorAll(`#${tableId} thead th`).forEach(th=>{
      th.addEventListener('click', ()=>{
        if(sortKey===th.dataset.k) sortDir*=-1; else {sortKey=th.dataset.k; sortDir=-1;}
        draw();
      });
    });
    draw();
  }

  makeSortable('mechTable', DATA.causal_graph.mechanism_templates, m=>{
    const payload = {title:`${m.source_label} → ${m.target_label}`, subtitle:`${m.source_var} → ${m.target_var}`,
      fields:[["Mean standardized coefficient",m.mean_coef],["Sigma (uncertainty)",m.sigma_coef],["Lag (periods)",m.lag],["Rationale",esc(m.rationale)]]};
    return `<tr class="clickable" data-inspect='${esc(JSON.stringify(payload))}'>
      <td>${esc(m.source_label)}</td><td>${esc(m.target_label)}</td>
      <td class="mono">${m.mean_coef>=0?'+':''}${m.mean_coef}</td><td class="mono">${m.sigma_coef}</td><td>${m.lag}</td>
    </tr>`;
  }, 'mean_coef');

  const ccRows = DATA.causal_graph.cross_country_edges.map(e=>({...e, mean:e.belief.mu, sigma:e.belief.sigma}));
  makeSortable('ccTable', ccRows, e=>{
    const payload = {title:`${e.source_actor} → ${e.target_actor}`, subtitle:e.id,
      fields:[["Source var",e.source_var],["Target var",e.target_var],["Mean coef.",e.mean],["Sigma",e.sigma],["Lag",e.lag],["Rationale",esc(e.rationale)]]};
    return `<tr class="clickable" data-inspect='${esc(JSON.stringify(payload))}'>
      <td><b>${esc(e.source_actor)}</b></td><td><b>${esc(e.target_actor)}</b></td>
      <td class="mono" style="font-size:11.5px;">${esc(e.source_var)}</td><td class="mono" style="font-size:11.5px;">${esc(e.target_var)}</td>
      <td class="mono">${e.mean}</td><td class="mono">${e.sigma}</td>
    </tr>`;
  }, 'mean');
})();

// =====================================================================
// DECISIONS
// =====================================================================
(function(){
  const el = document.getElementById('panel-decisions');
  let html = `<div class="card"><h2>HYPOTHETICAL example decisions</h2>
  <p class="lead">Fictional/illustrative scenarios used to exercise the graph end-to-end — not real announced
  policies or corporate actions. Each is modeled as an Assembly of action primitives (cost, lead time, Assembly
  Index) plus one or more origin shocks that seed the propagation engine.</p>
  ${DATA.decisions.map((d,i)=>{
    const dec = d.decision;
    return `<div class="decision-card">
      <div class="flex-between"><h3>${esc(dec.name)}</h3><span class="badge hyp">${esc(dec.status)}</span></div>
      <div class="meta">${esc(dec.description)}</div>
      <div style="margin:8px 0;">
        <span class="pill">Actor: ${esc(dec.actor)} (${esc(dec.actor_kind)})</span>
        <span class="pill">Assembly Index: ${dec.assembly.assembly_index}</span>
        <span class="pill">Illustrative cost: ${dec.assembly.total_cost.toLocaleString()}</span>
        <span class="pill">Critical path: ${dec.assembly.critical_path_lead_time} periods</span>
      </div>
      <table><thead><tr><th>Primitive</th><th>Cost</th><th>Lead time</th><th>Prior failure rate</th></tr></thead><tbody>
      ${dec.assembly.primitives.map(p=>`<tr><td>${esc(p.name)}</td><td>${p.cost}</td><td>${p.lead_time}</td><td>${(p.prior_failure_rate*100).toFixed(0)}%</td></tr>`).join('')}
      </tbody></table>
      <div style="margin-top:8px;"><b class="muted" style="font-size:11.5px;text-transform:uppercase;">Origin shock(s)</b>
      ${dec.origin_shocks.map(s=>`<div class="pill" style="margin-top:4px;">${esc(s.actor)}: ${esc(s.var)} ${s.delta>=0?'+':''}${s.delta} — ${esc(s.rationale)}</div>`).join('')}
      ${dec.proxy_route ? `<div class="pill" style="margin-top:4px;">Proxy route → ${esc(dec.proxy_route.home_country)} @ ${(dec.proxy_route.scope*100).toFixed(0)}% scope</div>` : ''}
      </div>
      <div style="margin-top:10px;"><button class="go" onclick="showTab('impact'); setTimeout(()=>showImpact(${i}),0);">View Impact Assessment →</button></div>
    </div>`;
  }).join('')}
  </div>`;
  el.innerHTML = html;
})();

// =====================================================================
// IMPACT ASSESSMENTS
// =====================================================================
function rangebar(p5, mean, p95, higherIsBetter){
  const lo = Math.min(p5, 0, p95), hi = Math.max(p5, 0, p95);
  const span = (hi-lo) || 1;
  const pct = v => ((v-lo)/span*100);
  const good = higherIsBetter===true ? mean>=0 : higherIsBetter===false ? mean<0 : null;
  const color = good===null ? 'var(--accent)' : (good ? 'var(--good)' : 'var(--bad)');
  return `<div class="rangebar">
    <div class="track" style="left:${pct(p5)}%;width:${pct(p95)-pct(p5)}%;"></div>
    <div class="mean" style="left:${pct(mean)}%;background:${color};"></div>
  </div>`;
}
function impactRow(entry){
  const chain = (entry.dominant_path||[]).map(c=>`${esc(c.source)} → ${esc(c.target)} <span class="muted">(hop ${c.hop}, lag ${c.lag})</span><br><span class="muted" style="font-size:11.5px;">${esc(c.rationale)}</span>`);
  const payload = {title:`${entry.var_label} — ${entry.actor_label}`, subtitle:entry.var,
    badges:[{cls:entry.materiality_tier,text:entry.materiality_tier}],
    fields:[["Mean effect",`${fmt(entry.mean)} ${esc(entry.unit)}`],["P5 .. P95",`${fmt(entry.p5)} .. ${fmt(entry.p95)}`],
      ["Direction-consistency across draws",`${entry.sign_consistency_pct}%`],["First reached at hop",entry.first_hop_reached]],
    pathChain: chain.length?chain:[esc(entry.dominant_path_text||'')]};
  return `<tr class="clickable" data-inspect='${esc(JSON.stringify(payload))}'>
    <td><b>${esc(entry.actor_label)}</b></td>
    <td>${esc(entry.var_label)}</td>
    <td class="mono">${entry.mean>=0?'+':''}${fmt(entry.mean)}</td>
    <td>${rangebar(entry.p5, entry.mean, entry.p95, entry.higher_is_better)}</td>
    <td><span class="badge ${esc(entry.materiality_tier)}">${esc(entry.materiality_tier)}</span></td>
    <td class="muted">${entry.sign_consistency_pct}%</td>
  </tr>`;
}
function showImpact(idx){
  document.querySelectorAll('#impactTabs button').forEach(b=>b.classList.toggle('active', +b.dataset.i===idx));
  renderImpactBody(idx);
}
function renderImpactBody(idx){
  const d = DATA.decisions[idx];
  const body = document.getElementById('impactBody');
  body.innerHTML = `
    <div class="card">
      <div class="flex-between"><h2>${esc(d.decision.name)}</h2><span class="badge hyp">${esc(d.status)}</span></div>
      <h3>Executive summary</h3>
      ${d.executive_summary.map(s=>`<p class="lead" style="margin:4px 0;">${esc(s)}</p>`).join('')}
      <h3>Assumptions &amp; limitations</h3>
      <ul style="font-size:12.5px;color:var(--muted);padding-left:18px;margin:4px 0;">
        ${d.assumptions_and_limitations.map(a=>`<li style="margin-bottom:4px;">${esc(a)}</li>`).join('')}
      </ul>
      ${d.unmodeled_note?`<p class="lead"><i>${esc(d.unmodeled_note)}</i></p>`:''}
    </div>
    <div class="card">
      <h2>Domestic impacts</h2>
      ${d.domestic_impacts.length ? `<table><thead><tr><th>Actor</th><th>Variable</th><th>Mean</th><th>P5–P95</th><th>Materiality</th><th>Direction consistency</th></tr></thead>
      <tbody>${d.domestic_impacts.map(impactRow).join('')}</tbody></table>` : '<p class="muted">No materially-reached domestic effects beyond the origin shock itself.</p>'}
    </div>
    <div class="card">
      <h2>Cross-border impacts</h2>
      ${d.cross_border_impacts.length ? `<table><thead><tr><th>Actor</th><th>Variable</th><th>Mean</th><th>P5–P95</th><th>Materiality</th><th>Direction consistency</th></tr></thead>
      <tbody>${d.cross_border_impacts.map(impactRow).join('')}</tbody></table>` : '<p class="muted">No materially-reached cross-border effects for this decision.</p>'}
    </div>
    <div class="card">
      <h2>Simulation</h2>
      <table><tbody>
        <tr><td>Monte Carlo draws</td><td>${d.simulation.n_simulations.toLocaleString()}</td></tr>
        <tr><td>Derived seed</td><td class="mono">${d.simulation.seed}</td></tr>
        <tr><td>Nodes reached</td><td>${d.simulation.n_nodes_reached}</td></tr>
        <tr><td>Edge firings</td><td>${d.simulation.n_edge_firings}</td></tr>
      </tbody></table>
    </div>`;
}
(function(){
  const el = document.getElementById('panel-impact');
  el.innerHTML = `<div class="card"><h2>Impact Assessments</h2>
    <p class="lead">One report per decision — the "alert" artifact for this model: a disclosure document a
    person can read, challenge, and choose to share through their own channels. Not an automated notification
    to any real leader.</p>
    <div class="tabs-inner" id="impactTabs">
      ${DATA.decisions.map((d,i)=>`<button data-i="${i}" class="${i===0?'active':''}" onclick="showImpact(${i})">${esc(d.decision.name.split(' — ')[0])}</button>`).join('')}
    </div>
    </div>
    <div id="impactBody"></div>`;
  renderImpactBody(0);
})();

// =====================================================================
// AUDIT TRAIL
// =====================================================================
(function(){
  const el = document.getElementById('panel-audit');
  const s = AUDIT.summary;
  let html = `<div class="card"><h2>Audit Trail</h2>
    <p class="lead">Content-hashed, chain-linked log of every component call in this run. Each event hashes its
    own inputs/outputs (SHA-256) and chains onto the previous event's hash — editing or reordering any single
    event breaks the chain hash below.</p>
    <table><tbody>
      <tr><td>Domain</td><td class="mono">${esc(s.domain)}</td></tr>
      <tr><td>Events logged</td><td>${s.n_events}</td></tr>
      <tr><td>Final chain hash</td><td class="mono">${esc(s.chain_hash)}</td></tr>
      <tr><td>Events by component</td><td>${Object.entries(s.events_by_component).map(([k,v])=>`<span class="pill">${esc(k)}: ${v}</span>`).join(' ')}</td></tr>
    </tbody></table>
  </div>
  <div class="card"><h2>Event log</h2>
    <table><thead><tr><th>#</th><th>Component</th><th>Event</th><th>Inputs hash</th><th>Outputs hash</th><th>Chain id</th></tr></thead><tbody>
    ${AUDIT.events.map(e=>{
      const payload = {title:`${e.component} · ${e.event}`, subtitle:`seq ${e.seq}`,
        fields:[["Inputs hash",e.inputs_hash],["Outputs hash",e.outputs_hash],["Chain id",e.id]], raw:{inputs:e.inputs, outputs:e.outputs}};
      return `<tr class="clickable" data-inspect='${esc(JSON.stringify(payload))}'>
        <td>${e.seq}</td><td>${esc(e.component)}</td><td>${esc(e.event)}</td>
        <td class="mono">${esc(e.inputs_hash)}</td><td class="mono">${esc(e.outputs_hash)}</td><td class="mono">${esc(e.id)}</td>
      </tr>`;
    }).join('')}
    </tbody></table>
  </div>`;
  el.innerHTML = html;
})();
</script>
</body>
</html>
"""

html = (HTML_TEMPLATE
         .replace("__DATA_JSON__", DATA_JSON)
         .replace("__AUDIT_JSON__", AUDIT_JSON)
         .replace("__N_SIM__", str(RESULTS["simulation_config"]["n_simulations"]))
         .replace("__SEED__", str(RESULTS["simulation_config"]["seed"])))

out_path = os.path.join(BASE, "world_model_dashboard.html")
with open(out_path, "w") as f:
    f.write(html)
print(f"Wrote {out_path} ({len(html):,} bytes)")

# A separate fragment build for the Artifact tool: it wraps published content
# in its own page skeleton, so that file must carry no doctype/html/head/body
# tags of its own -- just the <style> block followed by the body content.
style_start = html.index("<style>")
style_end = html.index("</style>") + len("</style>")
style_block = html[style_start:style_end]
body_start = html.index("<body>") + len("<body>")
body_end = html.index("</body>")
body_block = html[body_start:body_end]
fragment = style_block + "\n" + body_block

frag_path = os.path.join(BASE, "world_model_dashboard_artifact_fragment.html")
with open(frag_path, "w") as f:
    f.write(fragment)
print(f"Wrote {frag_path} ({len(fragment):,} bytes) — fragment for Artifact tool publish")
