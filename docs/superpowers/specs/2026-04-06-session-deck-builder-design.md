# AIE Europe '26 — Session Deck Builder

## Overview

A standalone single-page app that replaces the current AIE Twin briefing app. Users browse all 189 conference sessions displayed as collector-style cards inspired by [aicreatorpack.com](https://www.aicreatorpack.com/), filter by track and session type, and build a personal "deck" of sessions they want to attend.

## Architecture

**Monofichier HTML** — all CSS, JS, and HTML in a single `index.html`. No build step, no framework, no dependencies. Deployed as a static file on Cloudflare Pages.

**Data source:** Sessions and speakers loaded from local `data/sessions.json` and `data/speakers.json` at startup via `fetch()`. Both files are wrapper objects: sessions live at `response.sessions` (array) and speakers at `response.speakers` (array). The backend proxy (`/api/aie/*`) remains available as fallback.

**Persistence:** `localStorage` for saved deck. Key: `aie_deck` storing an array of stable session IDs. Each session ID is generated at parse time as a hash of `title + day + time` (e.g., `btoa(title+day+time).slice(0,16)`). This ensures deck integrity even if the source JSON is reordered or updated. Future Supabase auth + sync layer can wrap this without UI changes.

**Data normalization at parse time:**
- Merge `GPUs & LLM Infrastructure` into `GPUs & LLM Infra` (canonical name)
- Map type `track_keynote` to `keynote` for filtering purposes
- Map type `expo_session` to `expo` for filtering purposes
- Sessions with empty titles: use first speaker name as fallback, or "TBA" if no speakers
- `Google DeepMind/Gemini` track (14 sessions): added as an 11th track filter pill
- `Leadership Lunch` (1 session): no dedicated filter, visible when "all" is shown

## Page Structure

```
┌────────────────────────────────────────────────┐
│  HEADER (fixed top)                            │
│  "AIE EUROPE '26" title    "My Deck (N)" btn  │
├────────────────────────────────────────────────┤
│  FILTER BAR (sticky below header)              │
│  [Track pills ...] | [Type pills ...]         │
├────────────────────────────────────────────────┤
│                                                │
│  CARD GRID (scrollable)                        │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │
│  │ Card │ │ Card │ │ Card │ │ Card │          │
│  ├──────┤ ├──────┤ ├──────┤ ├──────┤          │
│  │ Info │ │ Info │ │ Info │ │ Info │          │
│  └──────┘ └──────┘ └──────┘ └──────┘          │
│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐          │
│  │ ...  │ │ ...  │ │ ...  │ │ ...  │          │
│  └──────┘ └──────┘ └──────┘ └──────┘          │
│                                                │
└────────────────────────────────────────────────┘
```

**Responsive grid:** 4 columns desktop (>1200px), 3 columns (>900px), 2 columns tablet (>600px), 1 column mobile.

## Component 1: Collector Card (upper visual)

Each session renders as a two-part component. The upper part is the collector card.

### Layout

```
┌──────────────────────────────────┐
│ APR 9            AIE EUROPE '26  │  monospace header
│ ST. JAMES        ▪▪▪▪▪▪▪▪▪▪▪▪  │  room + decorative barcode
│                                   │
│          SESSION TITLE            │  centered, bold, uppercase
│          OVER 2-3 LINES          │  Syne 800, white
│                                   │
│ CONTEXT ENGINEERING               │  track name, bottom-left
│ ■ TALK          ©2026 AIE EUROPE │  type badge + copyright
└──────────────────────────────────┘
```

### Visual Effects

**Background streaks:** CSS `linear-gradient` at ~135deg using the track's color palette. Multiple overlapping gradients create the diagonal streak effect.

**Iridescent border:** Double border effect — inner rounded border (dark) + outer border using a `conic-gradient` (rainbow/holographic) on a pseudo-element, with subtle opacity.

**3D tilt on hover:** `mousemove` listener on each card calculates cursor position relative to card center, applies `transform: perspective(800px) rotateX(Ydeg) rotateY(Xdeg)` with max rotation ~15deg. Smooth via `transition: transform 0.1s ease-out`.

**Light reflection:** A `::after` pseudo-element with `radial-gradient(circle at X% Y%, rgba(255,255,255,0.3), transparent 60%)` that follows mouse position, simulating holographic light catching.

**Reset on mouseleave:** Card returns to `rotateX(0) rotateY(0)` with a slower ease-out (~0.4s).

### Track Color Palettes

| Track | Primary | Secondary |
|-------|---------|-----------|
| Context Engineering | #3b82f6 (blue) | #8b5cf6 (violet) |
| MCP | #10b981 (emerald) | #06b6d4 (cyan) |
| Coding Agents | #f97316 (orange) | #ef4444 (red) |
| Harness Engineering | #ec4899 (magenta) | #f43f5e (rose) |
| Evals & Observability | #f59e0b (amber) | #eab308 (yellow) |
| Voice & Vision | #06b6d4 (cyan) | #3b82f6 (sky) |
| Claws & Personal Agents | #8b5cf6 (violet) | #6366f1 (indigo) |
| AI Architects | #e2e8f0 (silver) | #94a3b8 (slate) |
| GPUs & LLM Infra | #ef4444 (red) | #f97316 (deep orange) |
| Google DeepMind/Gemini | #4285f4 (google blue) | #34a853 (google green) |
| Generative Media | #84cc16 (lime) | #14b8a6 (teal) |
| Keynote | #fbbf24 (gold) | #fef3c7 (warm white) |
| Workshop | #1e40af (navy) | #3b82f6 (deep blue) |
| Expo | #6b7280 (gray) | #9ca3af (light gray) |
| Lightning | #a78bfa (light violet) | #c084fc (purple) |

Sessions without a track (keynotes, workshops) use their type color.

## Component 2: Info Panel (lower functional)

Directly attached below the collector card, same width, visually connected.

### Layout

```
┌──────────────────────────────────┐
│  Speaker Name            [♡ Save]│  bold + pill CTA
│  Company Name                    │  muted text
│                                   │
│  "Description text truncated      │  2-3 lines, line-clamp
│   to two or three lines max..."   │
│                                   │
│  🕐 3:30-5:30pm · St. James     │  monospace, muted
└──────────────────────────────────┘
```

### Style

- Background: `--surface` (#111827), `border: 1px solid rgba(255,255,255,0.06)`, border-radius matching the card above (connected look, no gap)
- Top border-radius: 0 (flush with card), bottom border-radius: 12px

### Save Button (CTA)

- **Default state:** Ghost pill — `border: 1px solid rgba(255,255,255,0.15)`, text "Save", muted color
- **Saved state:** Filled pill — background with track's primary color at 20% opacity, border with track color, text "Saved ✓", bright color
- **Card glow when saved:** The collector card above gains a `box-shadow: 0 0 20px trackColor(0.3)` to visually mark it in the grid

### Speaker Data Enrichment

The `sessions.json` contains speaker names as strings. Cross-reference with `speakers.json` (matched by `name` field) to get:
- `company` — displayed on info panel
- `role` — displayed alongside company (e.g., "Founding Engineer, Vercel")
- `photoUrl` — not used in v1, available for future enhancement
- `linkedin` — not used in v1

**Multi-speaker sessions (24 sessions with 2-3 speakers):** Show all names comma-separated on one line. Company shown for the first speaker only to avoid clutter.

**Sessions with no speakers (40 sessions, mostly expo):** Hide the speaker row entirely. The description line moves up to fill the space.

## Component 3: Filter Bar

Sticky below the header. Two groups separated by a visual divider.

### Track Filters

One pill per main track (10 tracks, excluding Expo sub-rooms and duplicates like "GPUs & LLM Infra" / "GPUs & LLM Infrastructure" which merge). Plus "Keynote" and "Workshop" as special pills.

Consolidated track list for filter pills:
1. Context Engineering
2. Evals & Observability
3. Harness Engineering
4. Claws & Personal Agents
5. Voice & Vision
6. Coding Agents
7. GPUs & LLM Infra (normalized from both "GPUs & LLM Infra" and "GPUs & LLM Infrastructure")
8. MCP
9. AI Architects
10. Generative Media
11. Google DeepMind/Gemini (14 sessions, Rutherford room)

Excluded from track filters: Expo sub-room tracks (`Expo Sessions (Abbey|Shelley|Wesley|Wordsworth)`) — these sessions are reachable via the "Expo" type filter instead. `Leadership Lunch` (1 session) — no dedicated pill, always visible in unfiltered view.

### Type Filters

Separate group:
1. Keynote
2. Workshop
3. Talk
4. Lightning
5. Expo

### Behavior

- **Track pills:** Radio behavior — click to activate, re-click to deactivate. Only one track active at a time. Active pill: filled background (track color at 20%), colored border, colored text.
- **Type pills:** Same radio behavior, independent from tracks.
- **Cross-filter:** Track AND Type can be active simultaneously. When both active, show sessions matching BOTH criteria. When neither active, show all.
- **"My Deck" mode:** When "My Deck" button is active, filters further restrict to saved sessions only. Track/Type filters still work within the deck view.
- **Mobile:** Horizontal scroll with edge fade if pills overflow.

## Component 4: Header

Fixed top bar.

```
┌──────────────────────────────────────────────┐
│  AIE EUROPE '26                 My Deck (3)  │
│  Session Browser                              │
└──────────────────────────────────────────────┘
```

- Title: "AIE EUROPE '26" in Syne 800, white. Subtitle "Session Browser" in Syne Mono, muted.
- "My Deck (N)": Pill button, right-aligned. Shows count of saved sessions. Active state = neon glow style.

## Data Flow

1. **Page load:** Fetch `data/sessions.json` and `data/speakers.json`
2. **Parse:** Build enriched session objects (merge speaker info)
3. **Render:** Generate card grid from session array
4. **Filter:** On filter change, toggle `display:none` on cards (no re-render, pure CSS class toggle for performance)
5. **Save/unsave:** Toggle session index in `localStorage` array, update card glow + button state + deck counter
6. **My Deck toggle:** Add/remove a CSS class on the grid container that hides non-saved cards

## UI States

**Loading:** Skeleton card grid (8 placeholder cards with pulsing gradient animation) while `fetch()` is in-flight.

**Fetch error:** Centered message "Could not load sessions. Please refresh." with a retry button.

**Empty filter results:** Centered message "No sessions match your filters" with a "Clear filters" link.

**Empty deck:** When "My Deck" is active with no saved sessions, show "Save sessions to build your deck" with an arrow pointing to the grid.

**Card date formatting:** "April 8" from data displayed as "APR 8" in uppercase monospace on the card.

**Barcode decoration:** CSS-generated pseudo-element with repeating thin vertical bars (`repeating-linear-gradient`) — purely decorative, varies width randomly per card using a CSS custom property seeded from the session index.

**Iridescent border animation:** Slow continuous rotation (`@keyframes rotate { to { --angle: 360deg } }`) at 4s duration on all cards. Uses `@property --angle` for animatable CSS custom property. Performant as it only affects the border pseudo-element.

## Performance

- 189 cards rendered once at startup (no virtual scrolling needed for this count)
- Tilt effect: `requestAnimationFrame` throttled, `will-change: transform` on cards
- Filter: CSS class toggle, no DOM manipulation
- `contain: layout style` on cards to limit reflow

## Future: Supabase Integration

Not in scope for v1. Design accommodates it:
- Save function writes to `localStorage` now, will additionally sync to Supabase `user_decks` table
- A "Sign in" button replaces or sits alongside "My Deck" in the header
- Auth state stored in memory, deck synced on login
- No UI changes needed beyond adding the sign-in button

## Files Changed

- `index.html` — Complete rewrite with new Session Deck Builder app
- `data/sessions.json` — Already downloaded, served by frontend static server
- `data/speakers.json` — Already downloaded, served by frontend static server
- Backend unchanged (proxy endpoints still available as fallback)
