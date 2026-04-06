# Session Deck Builder Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a collector-card-style session browser for AIE Europe '26 where users can filter by track/type and save sessions to a personal deck.

**Architecture:** Single `index.html` monofichier (CSS + JS + HTML). Data loaded from `data/sessions.json` and `data/speakers.json` via fetch. Deck persisted in localStorage with stable IDs. No build step, no framework.

**Tech Stack:** Vanilla HTML/CSS/JS, CSS custom properties, CSS `@property` for animated gradients, `perspective`/`rotateX`/`rotateY` for 3D tilt.

**Spec:** `docs/superpowers/specs/2026-04-06-session-deck-builder-design.md`

---

## File Structure

Single file: `index.html` (complete rewrite). The file has 3 logical sections separated by comments:

1. **`<style>`** — all CSS (~500 lines): variables, layout, card styles, filter bar, animations, responsive breakpoints
2. **`<body>`** — HTML structure (~80 lines): header, filter bar, grid container, empty states
3. **`<script>`** — all JS (~350 lines): data loading, normalization, card rendering, tilt effect, filter logic, deck persistence

Supporting files (already exist, no changes): `data/sessions.json`, `data/speakers.json`

---

### Task 1: HTML skeleton + CSS foundations

Create the `index.html` with the page structure, CSS custom properties, fonts, and the responsive grid layout. No cards rendered yet — just the empty shell with header, filter bar placeholder, and grid container.

**Files:**
- Create: `index.html`

- [ ] **Step 1: Write the HTML document skeleton**

```html
<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>AIE Europe '26 — Session Deck</title>
<link href="https://fonts.googleapis.com/css2?family=Syne:wght@400;700;800&family=Syne+Mono&display=swap" rel="stylesheet">
<style>
/* ── RESET & VARIABLES ── */
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
html{height:100%;-webkit-tap-highlight-color:transparent}
:root{
  --bg:#06080e;--surface:#111827;--deep:#0b0f1a;
  --g:rgba(255,255,255,.06);--g2:rgba(255,255,255,.11);
  --txt:#e8eef8;--muted:rgba(232,238,248,.38);--muted2:rgba(232,238,248,.2);
  --radius:14px;
}
body{
  background:var(--bg);color:var(--txt);
  font-family:'Syne',sans-serif;font-size:14px;
  min-height:100vh;overflow-x:hidden;
}

/* ── HEADER ── */
.header{
  position:fixed;top:0;left:0;right:0;z-index:100;
  background:rgba(6,8,14,.85);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--g);
  padding:16px 24px;
  display:flex;align-items:center;justify-content:space-between;
}
.header-title{font-size:22px;font-weight:800;letter-spacing:-.03em}
.header-sub{font-family:'Syne Mono',monospace;font-size:10px;color:var(--muted2);letter-spacing:.1em;margin-top:2px}
.deck-btn{
  font-family:'Syne Mono',monospace;font-size:11px;
  padding:8px 16px;border-radius:100px;cursor:pointer;
  border:1px solid var(--g2);background:transparent;color:var(--muted);
  transition:all .2s;letter-spacing:.04em;
}
.deck-btn:hover{color:var(--txt);border-color:rgba(255,255,255,.25)}
.deck-btn.active{
  background:rgba(79,255,176,.1);border-color:rgba(79,255,176,.4);
  color:#4fffb0;box-shadow:0 0 12px rgba(79,255,176,.15);
}

/* ── FILTER BAR ── */
.filters{
  position:sticky;top:61px;z-index:90;
  background:rgba(6,8,14,.9);backdrop-filter:blur(12px);
  border-bottom:1px solid var(--g);
  padding:12px 24px;
  display:flex;align-items:center;gap:8px;
  overflow-x:auto;scrollbar-width:none;
}
.filters::-webkit-scrollbar{display:none}
.filters .divider{width:1px;height:20px;background:var(--g2);flex-shrink:0;margin:0 4px}
.pill{
  font-family:'Syne Mono',monospace;font-size:10px;
  padding:6px 14px;border-radius:100px;cursor:pointer;
  border:1px solid var(--g2);background:transparent;
  color:var(--muted2);white-space:nowrap;flex-shrink:0;
  transition:all .2s;letter-spacing:.03em;
}
.pill:hover{color:var(--txt);border-color:rgba(255,255,255,.2)}
.pill.active{color:var(--c1,var(--txt));border-color:var(--c1,var(--txt));background:rgba(var(--c1-rgb,255,255,255),.1)}

/* ── GRID ── */
.grid{
  display:grid;
  grid-template-columns:repeat(4,1fr);
  gap:24px;
  padding:24px;
  padding-top:140px; /* header + filters */
  max-width:1400px;margin:0 auto;
}
@media(max-width:1200px){.grid{grid-template-columns:repeat(3,1fr)}}
@media(max-width:900px){.grid{grid-template-columns:repeat(2,1fr)}}
@media(max-width:600px){.grid{grid-template-columns:1fr;padding:16px;padding-top:130px}}

/* ── EMPTY STATES ── */
.empty-state{
  grid-column:1/-1;text-align:center;padding:80px 20px;
  font-family:'Syne Mono',monospace;color:var(--muted2);font-size:13px;
}
.empty-state a{color:var(--txt);text-decoration:underline;cursor:pointer}

/* ── LOADING SKELETON ── */
.skeleton{
  border-radius:var(--radius);overflow:hidden;
}
.skeleton .skel-card{
  height:280px;
  background:linear-gradient(135deg,var(--surface) 0%,var(--deep) 100%);
  animation:pulse 1.5s ease-in-out infinite;
}
.skeleton .skel-info{
  height:120px;background:var(--surface);
  border-top:1px solid var(--g);
}
@keyframes pulse{0%,100%{opacity:.6}50%{opacity:1}}
</style>
</head>
<body>

<header class="header">
  <div>
    <div class="header-title">AIE EUROPE '26</div>
    <div class="header-sub">SESSION BROWSER</div>
  </div>
  <button class="deck-btn" id="deckBtn" onclick="toggleDeck()">MY DECK (0)</button>
</header>

<div class="filters" id="filters"></div>

<main class="grid" id="grid">
  <!-- Cards rendered by JS -->
</main>

<script>
/* ── APP STATE ── */
const S = {
  sessions: [],
  speakers: {},
  deck: JSON.parse(localStorage.getItem('aie_deck') || '[]'),
  filterTrack: null,
  filterType: null,
  deckMode: false,
};

/* Entry point — called at end of script after all functions defined */
async function init() {
  showSkeleton();
  try {
    const [sessRes, spkRes] = await Promise.all([
      fetch('data/sessions.json').then(r => { if (!r.ok) throw r; return r.json(); }),
      fetch('data/speakers.json').then(r => { if (!r.ok) throw r; return r.json(); }),
    ]);
    S.sessions = normalize(sessRes.sessions, spkRes.speakers);
    renderFilters();
    renderGrid();
    updateDeckCount();
  } catch (e) {
    showError();
  }
}

function showSkeleton() {
  const g = document.getElementById('grid');
  g.innerHTML = Array(8).fill(0).map(() =>
    '<div class="skeleton"><div class="skel-card"></div><div class="skel-info"></div></div>'
  ).join('');
}

function showError() {
  document.getElementById('grid').innerHTML =
    '<div class="empty-state">Could not load sessions. <a onclick="location.reload()">Refresh</a></div>';
}

/* Stubs — implemented in later tasks */
function normalize(sessions, speakers) { return sessions; }
function buildSpeakerMap(speakers) {}
function renderFilters() {}
function renderGrid() { document.getElementById('grid').innerHTML = '<div class="empty-state">Loading...</div>'; }
function updateDeckCount() {}
function toggleDeck() {}

init();
</script>
</body>
</html>
```

- [ ] **Step 2: Verify in browser**

Open `http://localhost:3000` in browser. Confirm:
- Dark background, header with "AIE EUROPE '26" and "MY DECK (0)" button
- Empty filter bar visible
- 8 skeleton cards pulsing while loading (then "Loading..." since stubs)
- Responsive: resize window to confirm 4→3→2→1 column breakpoints

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: HTML skeleton with header, filter bar, grid, and skeleton loading"
```

---

### Task 2: Data normalization + speaker enrichment

Implement the `normalize()` and `buildSpeakerMap()` functions. This task handles all the data parsing: stable IDs, track normalization, type mapping, speaker cross-referencing.

**Files:**
- Modify: `index.html` (script section — replace stub functions)

- [ ] **Step 1: Implement buildSpeakerMap**

Replace the `buildSpeakerMap` stub in the `<script>` section:

```javascript
function buildSpeakerMap(speakers) {
  for (const sp of speakers) {
    S.speakers[sp.name] = { role: sp.role || '', company: sp.company || '', photo: sp.photoUrl || '' };
  }
}
```

- [ ] **Step 2: Implement normalize**

Replace the `normalize` stub:

```javascript
function normalize(sessions, speakers) {
  buildSpeakerMap(speakers);
  return sessions.map((s, i) => {
    /* Stable ID */
    const id = btoa(unescape(encodeURIComponent((s.title||'')+s.day+s.time))).replace(/[+/=]/g,'_').slice(0,16);

    /* Track normalization */
    let track = s.track || '';
    if (track === 'GPUs & LLM Infrastructure') track = 'GPUs & LLM Infra';

    /* Type normalization */
    let type = s.type || 'talk';
    if (type === 'track_keynote') type = 'keynote';
    if (type === 'expo_session') type = 'expo';

    /* Title fallback */
    let title = (s.title || '').trim();
    if (!title) title = (s.speakers||[]).length ? s.speakers[0] : 'TBA';

    /* Day formatting: "April 9" -> "APR 9" */
    const dayShort = s.day.replace('April ', 'APR ');

    /* Speaker enrichment */
    const speakerInfo = s.speakers.map(name => ({
      name,
      ...(S.speakers[name] || { role: '', company: '', photo: '' })
    }));

    return { id, title, description: s.description || '', day: s.day, dayShort, time: s.time,
             room: s.room, track, type, speakers: speakerInfo, _idx: i };
  });
}
```

- [ ] **Step 3: Verify data normalization in console**

Open browser console at `http://localhost:3000` and run:
```javascript
console.log('Total:', S.sessions.length);
console.log('Sample ID:', S.sessions[0].id);
console.log('GPU normalized:', S.sessions.filter(s => s.track === 'GPUs & LLM Infrastructure').length === 0);
console.log('track_keynote gone:', S.sessions.filter(s => s.type === 'track_keynote').length === 0);
console.log('expo_session gone:', S.sessions.filter(s => s.type === 'expo_session').length === 0);
console.log('Speaker enriched:', S.sessions.find(s => s.speakers.length && s.speakers[0].company));
```

Expected: 189 sessions, IDs are strings, no `GPUs & LLM Infrastructure`, no `track_keynote`, no `expo_session`, speakers have company field.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: data normalization with stable IDs, track/type mapping, speaker enrichment"
```

---

### Task 3: Collector card CSS (streaks, iridescent border, layout)

Add all CSS for the collector card visual — the streak backgrounds per track, the iridescent animated border, the inner card layout. No JS tilt yet (that's Task 5).

**Files:**
- Modify: `index.html` (style section — add card CSS)

- [ ] **Step 1: Add @property for animated angle and track color variables**

Add after the `:root` block in the `<style>`:

```css
/* ── ANIMATED ANGLE for iridescent border ── */
@property --angle {
  syntax: '<angle>';
  initial-value: 0deg;
  inherits: false;
}
@keyframes rotate-border { to { --angle: 360deg; } }

/* ── TRACK COLORS (set as CSS vars on each card via JS) ── */
/* --c1: primary, --c2: secondary, --c1-rgb: primary as r,g,b */
```

- [ ] **Step 2: Add collector card CSS**

Add after the skeleton styles:

```css
/* ── CARD WRAPPER (both collector + info panel) ── */
.card-wrap{display:flex;flex-direction:column;contain:layout style}
.card-wrap.hidden{display:none}
.card-wrap.saved .collector{box-shadow:0 0 25px rgba(var(--c1-rgb,79,255,176),.25)}

/* ── COLLECTOR CARD ── */
.collector{
  position:relative;
  aspect-ratio:3/4;
  border-radius:var(--radius);
  overflow:hidden;
  cursor:pointer;
  transform-style:preserve-3d;
  transition:transform .15s ease-out;
  will-change:transform;
  /* Inner content positioning */
  display:flex;flex-direction:column;justify-content:space-between;
  padding:16px 18px;
}

/* Streak background */
.collector::before{
  content:'';position:absolute;inset:0;z-index:0;
  background:
    linear-gradient(135deg, var(--c1,#3b82f6) 0%, transparent 50%),
    linear-gradient(135deg, transparent 40%, var(--c2,#8b5cf6) 70%, transparent 90%),
    linear-gradient(160deg, rgba(0,0,0,.8) 0%, rgba(0,0,0,.3) 40%, rgba(0,0,0,.6) 100%),
    linear-gradient(135deg, #0a0a0a, #1a1a2e);
  background-size:100% 100%;
}

/* Light reflection overlay (positioned by JS on hover) */
.collector::after{
  content:'';position:absolute;inset:0;z-index:2;
  background:radial-gradient(circle at var(--mx,50%) var(--my,50%), rgba(255,255,255,.15), transparent 60%);
  opacity:0;transition:opacity .3s;pointer-events:none;
}
.collector:hover::after{opacity:1}

/* Iridescent border */
.collector-border{
  position:absolute;inset:-2px;z-index:-1;
  border-radius:calc(var(--radius) + 2px);
  background:conic-gradient(from var(--angle,0deg),
    rgba(255,255,255,.15),
    rgba(120,200,255,.3),
    rgba(200,150,255,.3),
    rgba(255,200,150,.2),
    rgba(150,255,200,.3),
    rgba(120,200,255,.3),
    rgba(255,255,255,.15)
  );
  animation:rotate-border 4s linear infinite;
}

/* Card inner content — all positioned above the background */
.c-head,.c-body,.c-foot{position:relative;z-index:1}

.c-head{
  display:flex;justify-content:space-between;
  font-family:'Syne Mono',monospace;font-size:9px;
  color:rgba(255,255,255,.5);letter-spacing:.08em;text-transform:uppercase;
}
.c-head-l,.c-head-r{display:flex;flex-direction:column;gap:2px}
.c-head-r{text-align:right}

/* Decorative barcode */
.c-barcode{
  display:inline-block;height:8px;width:60px;margin-top:4px;
  background:repeating-linear-gradient(90deg,
    rgba(255,255,255,.25) 0px, rgba(255,255,255,.25) var(--bw,2px),
    transparent var(--bw,2px), transparent calc(var(--bw,2px) + 2px)
  );
  opacity:.4;
}

.c-body{
  flex:1;display:flex;align-items:center;justify-content:center;
  text-align:center;padding:12px 8px;
}
.c-title{
  font-size:16px;font-weight:800;text-transform:uppercase;
  letter-spacing:-.01em;line-height:1.25;color:#fff;
  display:-webkit-box;-webkit-line-clamp:4;-webkit-box-orient:vertical;overflow:hidden;
  text-shadow:0 2px 12px rgba(0,0,0,.5);
}

.c-foot{
  display:flex;justify-content:space-between;align-items:flex-end;
  font-family:'Syne Mono',monospace;font-size:9px;
  color:rgba(255,255,255,.45);letter-spacing:.06em;text-transform:uppercase;
}
.c-track{font-size:10px;color:rgba(255,255,255,.6);margin-bottom:4px}
.c-type{display:flex;align-items:center;gap:4px}
.c-type-dot{width:6px;height:6px;border-radius:2px;background:var(--c1,#fff)}
```

- [ ] **Step 3: Verify in browser**

Cards won't render yet (renderGrid is a stub), but the CSS should parse without errors. Open DevTools → Console, check for no CSS parse errors.

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: collector card CSS with streaks, iridescent border, and layout"
```

---

### Task 4: Card rendering + info panel

Implement `renderGrid()` to generate the full card HTML for all 189 sessions. Each card is a `.card-wrap` containing a `.collector` (visual) and `.info-panel` (functional).

**Files:**
- Modify: `index.html` (script section + style section)

- [ ] **Step 1: Add info panel CSS**

Add after the collector card CSS in `<style>`:

```css
/* ── INFO PANEL ── */
.info-panel{
  background:var(--surface);
  border:1px solid var(--g);border-top:none;
  border-radius:0 0 var(--radius) var(--radius);
  padding:14px 16px;
  display:flex;flex-direction:column;gap:8px;
}
.info-top{display:flex;justify-content:space-between;align-items:flex-start}
.info-speaker{font-weight:700;font-size:13px;line-height:1.3}
.info-company{font-family:'Syne Mono',monospace;font-size:10px;color:var(--muted2);margin-top:2px}
.info-desc{
  font-size:12px;color:var(--muted);line-height:1.55;
  display:-webkit-box;-webkit-line-clamp:3;-webkit-box-orient:vertical;overflow:hidden;
}
.info-meta{
  font-family:'Syne Mono',monospace;font-size:10px;color:var(--muted2);
  letter-spacing:.04em;
}

/* Save button */
.save-btn{
  font-family:'Syne Mono',monospace;font-size:10px;
  padding:5px 14px;border-radius:100px;cursor:pointer;
  border:1px solid var(--g2);background:transparent;
  color:var(--muted2);transition:all .2s;letter-spacing:.04em;
  white-space:nowrap;flex-shrink:0;
}
.save-btn:hover{color:var(--txt);border-color:rgba(255,255,255,.25)}
.card-wrap.saved .save-btn{
  background:rgba(var(--c1-rgb,79,255,176),.15);
  border-color:var(--c1,#4fffb0);
  color:var(--c1,#4fffb0);
}
```

- [ ] **Step 2: Implement renderGrid**

Replace the `renderGrid` stub:

```javascript
/* ── TRACK COLOR MAP ── */
const COLORS = {
  'Context Engineering':       { c1:'#3b82f6', c2:'#8b5cf6', rgb:'59,130,246' },
  'MCP':                       { c1:'#10b981', c2:'#06b6d4', rgb:'16,185,129' },
  'Coding Agents':             { c1:'#f97316', c2:'#ef4444', rgb:'249,115,22' },
  'Harness Engineering':       { c1:'#ec4899', c2:'#f43f5e', rgb:'236,72,153' },
  'Evals & Observability':     { c1:'#f59e0b', c2:'#eab308', rgb:'245,158,11' },
  'Voice & Vision':            { c1:'#06b6d4', c2:'#3b82f6', rgb:'6,182,212' },
  'Claws & Personal Agents':   { c1:'#8b5cf6', c2:'#6366f1', rgb:'139,92,246' },
  'AI Architects':             { c1:'#e2e8f0', c2:'#94a3b8', rgb:'226,232,240' },
  'GPUs & LLM Infra':          { c1:'#ef4444', c2:'#f97316', rgb:'239,68,68' },
  'Google DeepMind/Gemini':    { c1:'#4285f4', c2:'#34a853', rgb:'66,133,244' },
  'Generative Media':          { c1:'#84cc16', c2:'#14b8a6', rgb:'132,204,22' },
};
const TYPE_COLORS = {
  'keynote':   { c1:'#fbbf24', c2:'#fef3c7', rgb:'251,191,36' },
  'workshop':  { c1:'#1e40af', c2:'#3b82f6', rgb:'30,64,175' },
  'talk':      { c1:'#6b7280', c2:'#9ca3af', rgb:'107,114,128' },
  'lightning': { c1:'#a78bfa', c2:'#c084fc', rgb:'167,139,250' },
  'expo':      { c1:'#6b7280', c2:'#9ca3af', rgb:'107,114,128' },
};

function getColors(session) {
  return COLORS[session.track] || TYPE_COLORS[session.type] || TYPE_COLORS['talk'];
}

function renderGrid() {
  const g = document.getElementById('grid');
  if (!S.sessions.length) { g.innerHTML = '<div class="empty-state">No sessions found.</div>'; return; }

  g.innerHTML = S.sessions.map(s => {
    const col = getColors(s);
    const saved = S.deck.includes(s.id);
    const bw = 1 + (s._idx % 3); /* barcode width variation */
    const spName = s.speakers.map(sp => sp.name).join(', ') || '';
    const spCompany = s.speakers.length ? [s.speakers[0].role, s.speakers[0].company].filter(Boolean).join(', ') : '';

    return `<div class="card-wrap${saved ? ' saved' : ''}" data-id="${s.id}" data-track="${s.track}" data-type="${s.type}"
      style="--c1:${col.c1};--c2:${col.c2};--c1-rgb:${col.rgb};--bw:${bw}px">
  <div class="collector" onmouseenter="tiltEnter(this)" onmouseleave="tiltLeave(this)" onmousemove="tiltMove(event,this)">
    <div class="collector-border"></div>
    <div class="c-head">
      <div class="c-head-l"><span>${s.dayShort}</span><span>${s.room}</span></div>
      <div class="c-head-r"><span>AIE EUROPE '26</span><span class="c-barcode"></span></div>
    </div>
    <div class="c-body"><div class="c-title">${esc(s.title)}</div></div>
    <div class="c-foot">
      <div><div class="c-track">${esc(s.track)}</div><div class="c-type"><span class="c-type-dot"></span>${s.type.toUpperCase()}</div></div>
      <div>&copy;2026 AIE EUROPE</div>
    </div>
  </div>
  <div class="info-panel">
    <div class="info-top">
      <div>${spName ? `<div class="info-speaker">${esc(spName)}</div>${spCompany ? `<div class="info-company">${esc(spCompany)}</div>` : ''}` : ''}</div>
      <button class="save-btn" onclick="toggleSave('${s.id}')">${saved ? 'SAVED ✓' : 'SAVE'}</button>
    </div>
    ${s.description ? `<div class="info-desc">${esc(s.description)}</div>` : ''}
    <div class="info-meta">${s.time} · ${s.room}</div>
  </div>
</div>`;
  }).join('');
}

const _escEl = document.createElement('div');
function esc(str) {
  _escEl.textContent = str;
  return _escEl.innerHTML;
}

/* Tilt stubs — implemented in Task 5 */
function tiltEnter(el) {}
function tiltLeave(el) {}
function tiltMove(e, el) {}
```

- [ ] **Step 3: Verify in browser**

Open `http://localhost:3000`. Confirm:
- 189 cards rendered in a 4-column grid
- Each card has streak gradient background with track-appropriate colors
- Iridescent border is visible and slowly rotating
- Info panel shows speaker name, company/role, description (truncated), time + room
- Cards without speakers show no speaker row
- Cards without titles show fallback name

- [ ] **Step 4: Commit**

```bash
git add index.html
git commit -m "feat: card rendering with collector visual, info panel, and speaker enrichment"
```

---

### Task 5: 3D tilt effect + light reflection

Implement the mouse-driven 3D tilt and the moving light reflection on hover. Replace the tilt stubs.

**Files:**
- Modify: `index.html` (script section — replace tilt stubs)

- [ ] **Step 1: Implement tilt functions**

Replace the three tilt stubs:

```javascript
let _tiltRAF = 0;
function tiltMove(e, el) {
  if (window.matchMedia('(hover: none)').matches) return;
  cancelAnimationFrame(_tiltRAF);
  _tiltRAF = requestAnimationFrame(() => {
    const rect = el.getBoundingClientRect();
    const x = (e.clientX - rect.left) / rect.width;   /* 0..1 */
    const y = (e.clientY - rect.top) / rect.height;    /* 0..1 */
    const rotY = (x - 0.5) * 20;   /* -10..10 deg */
    const rotX = (0.5 - y) * 20;   /* -10..10 deg */
    el.style.transform = `perspective(800px) rotateX(${rotX}deg) rotateY(${rotY}deg) scale(1.02)`;
    el.style.setProperty('--mx', (x * 100) + '%');
    el.style.setProperty('--my', (y * 100) + '%');
  });
}

function tiltEnter(el) {
  el.style.transition = 'transform .1s ease-out';
}

function tiltLeave(el) {
  el.style.transition = 'transform .4s ease-out';
  el.style.transform = 'perspective(800px) rotateX(0) rotateY(0) scale(1)';
}
```

- [ ] **Step 2: Verify in browser**

Hover over cards at `http://localhost:3000`:
- Card tilts following mouse position (~10deg max rotation)
- Light reflection (white radial gradient) follows the cursor
- Card scales up slightly (1.02) on hover
- Smooth reset when mouse leaves (0.4s ease)

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: 3D tilt effect with perspective and light reflection on hover"
```

---

### Task 6: Filter bar rendering + filter logic

Render the track and type filter pills, implement radio toggle behavior, and wire up cross-filtering.

**Files:**
- Modify: `index.html` (script section — replace renderFilters stub + add filter logic)

- [ ] **Step 1: Implement renderFilters**

Replace the `renderFilters` stub:

```javascript
const TRACKS = [
  'Context Engineering','Evals & Observability','Harness Engineering',
  'Claws & Personal Agents','Voice & Vision','Coding Agents',
  'GPUs & LLM Infra','MCP','AI Architects','Generative Media',
  'Google DeepMind/Gemini'
];
const TYPES = ['keynote','workshop','talk','lightning','expo'];

function renderFilters() {
  const f = document.getElementById('filters');
  const trackPills = TRACKS.map(t => {
    const col = COLORS[t] || TYPE_COLORS['talk'];
    return `<button class="pill" data-filter="track" data-val="${t}" style="--c1:${col.c1};--c1-rgb:${col.rgb}" onclick="setFilter('track','${t}')">${t}</button>`;
  }).join('');

  const typePills = TYPES.map(t => {
    const col = TYPE_COLORS[t] || TYPE_COLORS['talk'];
    return `<button class="pill" data-filter="type" data-val="${t}" style="--c1:${col.c1};--c1-rgb:${col.rgb}" onclick="setFilter('type','${t}')">${t.toUpperCase()}</button>`;
  }).join('');

  f.innerHTML = trackPills + '<div class="divider"></div>' + typePills;
}

function setFilter(kind, val) {
  if (kind === 'track') S.filterTrack = S.filterTrack === val ? null : val;
  if (kind === 'type') S.filterType = S.filterType === val ? null : val;
  applyFilters();
}

function applyFilters() {
  /* Update pill active states */
  document.querySelectorAll('.pill[data-filter="track"]').forEach(p => {
    p.classList.toggle('active', p.dataset.val === S.filterTrack);
  });
  document.querySelectorAll('.pill[data-filter="type"]').forEach(p => {
    p.classList.toggle('active', p.dataset.val === S.filterType);
  });

  /* Filter cards */
  let visible = 0;
  document.querySelectorAll('.card-wrap').forEach(c => {
    const matchTrack = !S.filterTrack || c.dataset.track === S.filterTrack;
    const matchType = !S.filterType || c.dataset.type === S.filterType;
    const matchDeck = !S.deckMode || c.classList.contains('saved');
    const show = matchTrack && matchType && matchDeck;
    c.classList.toggle('hidden', !show);
    if (show) visible++;
  });

  /* Empty state */
  let emptyEl = document.getElementById('emptyState');
  if (!visible) {
    if (!emptyEl) {
      emptyEl = document.createElement('div');
      emptyEl.id = 'emptyState';
      emptyEl.className = 'empty-state';
      document.getElementById('grid').appendChild(emptyEl);
    }
    if (S.deckMode && !S.deck.length) {
      emptyEl.innerHTML = 'Save sessions to build your deck';
    } else {
      emptyEl.innerHTML = 'No sessions match your filters. <a onclick="clearFilters()">Clear filters</a>';
    }
    emptyEl.style.display = '';
  } else if (emptyEl) {
    emptyEl.style.display = 'none';
  }
}

function clearFilters() {
  S.filterTrack = null;
  S.filterType = null;
  S.deckMode = false;
  document.getElementById('deckBtn').classList.remove('active');
  applyFilters();
}
```

- [ ] **Step 2: Verify in browser**

At `http://localhost:3000`:
- Filter pills visible: 11 track pills, divider, 5 type pills
- Click "MCP" → only MCP sessions shown, pill highlighted with MCP green
- Click "MCP" again → deselected, all sessions shown
- Click "Coding Agents" + "Talk" → cross-filter works (only talks in Coding Agents track)
- Apply filters that match 0 results → "No sessions match your filters" with "Clear filters" link
- Click "Clear filters" → all shown again

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: filter bar with track/type radio pills and cross-filtering"
```

---

### Task 7: Deck persistence (save/unsave + My Deck mode)

Implement `toggleSave()`, `updateDeckCount()`, and `toggleDeck()` functions. Wire up localStorage persistence.

**Files:**
- Modify: `index.html` (script section — replace remaining stubs)

- [ ] **Step 1: Implement deck functions**

Replace the three remaining stubs:

```javascript
function toggleSave(id) {
  const idx = S.deck.indexOf(id);
  if (idx === -1) S.deck.push(id);
  else S.deck.splice(idx, 1);
  localStorage.setItem('aie_deck', JSON.stringify(S.deck));

  /* Update card visual */
  const card = document.querySelector(`.card-wrap[data-id="${id}"]`);
  if (card) {
    const saved = S.deck.includes(id);
    card.classList.toggle('saved', saved);
    card.querySelector('.save-btn').textContent = saved ? 'SAVED ✓' : 'SAVE';
  }
  updateDeckCount();

  /* Re-apply filters in case deck mode is active */
  if (S.deckMode) applyFilters();
}

function updateDeckCount() {
  document.getElementById('deckBtn').textContent = `MY DECK (${S.deck.length})`;
}

function toggleDeck() {
  S.deckMode = !S.deckMode;
  document.getElementById('deckBtn').classList.toggle('active', S.deckMode);
  applyFilters();
}
```

- [ ] **Step 2: Verify in browser**

At `http://localhost:3000`:
- Click "SAVE" on a card → button changes to "SAVED ✓", card gets glow, counter updates to "MY DECK (1)"
- Click "SAVED ✓" again → reverts to "SAVE", glow removed, counter back to "MY DECK (0)"
- Save 3 cards → click "MY DECK (3)" → only those 3 cards shown
- Click "MY DECK (3)" again → back to all cards
- Refresh page → saved cards persist (localStorage)
- In My Deck mode with no saves → "Save sessions to build your deck" message

- [ ] **Step 3: Commit**

```bash
git add index.html
git commit -m "feat: deck persistence with localStorage, save/unsave toggle, My Deck filter"
```

---

### Task 8: Mobile responsive + filter scroll + polish

Final pass: ensure filter bar scrolls horizontally on mobile with edge fades, cards look good at all breakpoints, touch tilt disabled (no mousemove on mobile).

**Files:**
- Modify: `index.html` (style section + script section)

- [ ] **Step 1: Add mobile filter scroll fade**

Add CSS after the `.filters` block:

Wrap the `.filters` element in a `.filters-wrap` container for reliable edge fades. Update the HTML in Task 1:

```html
<div class="filters-wrap">
  <div class="filters" id="filters"></div>
</div>
```

Add CSS:

```css
/* Filter bar edge fades on mobile */
.filters-wrap{
  position:sticky;top:61px;z-index:90;
}
.filters-wrap::before,.filters-wrap::after{
  content:'';position:absolute;top:0;bottom:0;width:24px;z-index:2;pointer-events:none;
}
.filters-wrap::before{left:0;background:linear-gradient(to right,rgba(6,8,14,.9),transparent)}
.filters-wrap::after{right:0;background:linear-gradient(to left,rgba(6,8,14,.9),transparent)}

/* Mobile card adjustments */
@media(max-width:600px){
  .collector{aspect-ratio:4/5}
  .c-title{font-size:14px}
  .header{padding:12px 16px}
  .header-title{font-size:18px}
  .filters{padding:10px 16px;top:53px}
  .grid{padding-top:120px}
}
```

- [ ] **Step 2: Verify at all breakpoints**

Note: Touch device tilt disable is already handled in Task 5's `tiltMove` (via `hover: none` media query check).

Test at `http://localhost:3000`:
- Desktop (1200px+): 4 columns, all pills visible
- Tablet (900px): 3 columns
- Small tablet (600px): 2 columns
- Mobile (375px): 1 column, filter bar scrolls horizontally with edge fades
- Touch emulation: tilt effect disabled

- [ ] **Step 4: Final commit**

```bash
git add index.html
git commit -m "feat: mobile responsive, filter scroll fades, touch tilt disabled"
```

---

### Task 9: Visual QA + final polish

Review the full app, fix any visual issues, and ensure everything matches the spec.

**Files:**
- Modify: `index.html`

- [ ] **Step 1: Open app and do full visual QA**

Check at `http://localhost:3000`:
- [ ] Header fixed at top, filter bar sticky below
- [ ] All 189 cards render without errors
- [ ] Track colors are distinct and match spec palette
- [ ] Iridescent border animates smoothly (4s rotation)
- [ ] 3D tilt works on all cards
- [ ] Light reflection follows cursor
- [ ] Save/unsave works, glow appears on saved cards
- [ ] My Deck counter accurate
- [ ] Cross-filter (track + type) works correctly
- [ ] Empty states shown when appropriate
- [ ] localStorage persists across refresh
- [ ] No console errors

- [ ] **Step 2: Fix any issues found in QA**

Address visual bugs, spacing, color contrast, or edge cases.

- [ ] **Step 3: Final commit**

```bash
git add index.html
git commit -m "polish: visual QA fixes and final adjustments"
```
