# Phase 1 Validation

**Phase:** Dashboard Shell
**Status:** Complete
**Started:** 2026-05-11 (Session 5 — first build session)
**Completed:** 2026-05-15
**Validated by:** Magnus Thomassen
**Session:** 16

---

## Phase deliverables checklist

Derived from `04_BUILD_SEQUENCE.docx` Phase 1 entry and the build-priority ordering in `05_DASHBOARD_SPEC.docx`.

### Visual-identity scaffolding (foundation before any zone layout)

- [x] Theme module — both dark and light token sets
  - evidence: `mfip/dashboard/theme.py` — DARK + LIGHT token dicts, `apply_theme(fig, mode)` helper
- [x] Theme CSS — `[data-theme]` selectors defining all color tokens on `:root` / `html`
  - evidence: `mfip/dashboard/assets/theme.css` — mirrors theme.py DARK + LIGHT; tokens confirmed during Item C-1 discovery (`--bg-canvas`, `--bg-surface`, `--bg-surface-raised`, `--border-subtle`, `--border-strong`, `--text-primary`, `--text-secondary`, `--text-muted`)
- [x] AG Grid CSS overrides — CSS vars from same token set as theme.py
  - evidence: `mfip/dashboard/assets/ag-grid-overrides.css` — sync enforced by unit test
- [x] Type system — Inter and JetBrains Mono loaded, type scale defined, utility classes applied
  - evidence: `mfip/dashboard/assets/typography.css` — `--type-h2-size`, `--type-h2-weight`, `--type-caption-size`, `--type-caption-weight` (plus line-height tokens) confirmed during Item C-1 discovery; visible application across Zone 1 title and the new placeholder titles/captions
- [x] Density classes — three CSS utility classes for Tight / Comfortable / Roomy
  - evidence: `mfip/dashboard/assets/density.css` present and loaded; Zone 1 uses Roomy density per spec
- [x] Motion CSS — global rules respecting `prefers-reduced-motion`
  - evidence: `mfip/dashboard/assets/motion.css` present and loaded

### Four zones designed before coding (Phase 1 principle)

- [x] Design all four dashboard zones before coding
  - evidence: `05_DASHBOARD_SPEC.docx` v1.2 (locked 2026-05-11) — full zone designs in place before Session 5 build kicked off
- [x] Routing note (2026-05-13): Zones 1-4 are components on the `/analysis` route, not separately routed pages
  - evidence: `decisions.md` 2026-05-13 "Routing architecture: Pages affirmed"; `pages/analysis.py` composes Zone 1 + Zone 2-4 placeholder containers under id `analysis-page` + `analysis-body`

### Zone implementation (placeholder data throughout)

- [x] Build Zone 1: Command Centre — pipeline status, alerts, company selector
  - evidence: `mfip/dashboard/zones/zone1.py` (exports `layout` constant; composed into `pages/analysis.py`); MFIP logo, Idle indicator, active-jobs counter with hover breakdown, three alert badges (Critical/Warning/Advisory), date filter presets (1Y/3Y/5Y/MAX/Custom), company selector dropdown, settings cog all rendered and interactive
- [x] Build Zone 2: Company Deep Dive — placeholder container
  - evidence: `pages/analysis.py` Zone 2 placeholder shipped in PR #50 (Session 16 Item C-1); visible bordered card occupying ~60% of body width, top-left
- [x] Build Zone 3: Intelligence Feed — placeholder container
  - evidence: `pages/analysis.py` Zone 3 placeholder shipped in PR #50; visible bordered card occupying ~40% of body width, top-right
- [x] Build Zone 4: Portfolio View — placeholder container
  - evidence: `pages/analysis.py` Zone 4 placeholder shipped in PR #50; visible bordered card spanning full width across the bottom ~35% body height
- [ ] Build Backtesting Panel (tab view) — placeholder only
  - evidence: Not built. Phase 1 spec called for tab-view placeholder; not present in current dashboard. Tab-view framing predates the multi-route stance per `worklog.md` 2026-05-13 entry; full backtesting is v2. Phase 1 close-out leaves this unbuilt by design.
- [ ] Build Security Alert overlay — warning card display
  - evidence: Not exercised during walkthrough. The Security Alert Overlay is a modal that appears when a Critical alert fires; idle dashboard correctly shows no overlay. Overlay rendering will be exercised at Phase 8 (Security Council build) when actual Critical alerts are produced. Phase 1 close-out leaves this not-yet-verified by design.
- [x] Wire placeholder data throughout
  - evidence: dashboard renders Zone 1 chrome with placeholder badge counts (0/0/0), placeholder Idle status, and the three zone placeholder cards with their titles + "Phase 1 placeholder" captions
- [x] Test full-screen rendering on Windows desktop
  - evidence: Browser maximised on Windows desktop during Session 16 walkthrough; layout fills viewport correctly, no overflow, no scrollbar; resize down to narrow widths reflows gracefully (zones shrink proportionally, gaps remain consistent)

### Phase 1 close-out deliverables (committed during Phase 1, not in 04_BUILD_SEQUENCE checklist explicitly)

- [x] Served-layout callback ID resolution smoke test (IDEA-023, graduated)
  - evidence: `tests/test_served_layout.py` shipped in PR #30; passes against the post-PR-50 served DOM
- [x] Two-route registration: `/` (Home stub) and `/analysis` (zones composed)
  - evidence: `pages/home.py` and `pages/analysis.py`; `mfip/dashboard/app.py` registers both via Dash Pages; route registration verified via `tests/test_app.py`

---

## Runtime artifacts verified on disk

Verified during the Session 16 walkthrough (2026-05-15) and the Item C-1 discovery + post-merge confirmation.

- [x] `mfip/dashboard/` module present and importable
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: `python -m mfip.dashboard` invokes the module's entry point cleanly; structure matches `MEMORY.md` `What Is Built` rows for `app.py`, `pages/home.py`, `pages/analysis.py`, `zones/zone1.py`, `theme.py`, and the `assets/` CSS files

- [x] Dashboard launches via `python -m mfip.dashboard`
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: Starts with `Dash is running on http://127.0.0.1:8050/`, Flask app `mfip.dashboard.app` serving, debug mode on, no startup errors

- [x] `/` route renders Home stub
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: Home stub renders at `http://127.0.0.1:8050/`; deeper Home content design is a separate open item per `ideas.md` 2026-05-10 "Project Dashboard View" entry — Home contents are deferred until `/analysis` is in routine use

- [x] `/analysis` route renders Zone 1 + Zone 2-4 placeholder containers
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: Initial walkthrough found Zone 1 visible but Zones 2-4 not rendering (containers existed in DOM as empty inert `html.Div`s but had no CSS targeting them and no internal labels — see Findings below for the F5 fix). After PR #50 merged, Zone 2-4 placeholder containers render visibly with correct titles, captions, proportions (60/40 horizontal × 65/35 vertical), and 8px gaps. Served-layout walk confirms the expected DOM tree (`#analysis-page` → `#analysis-body.analysis-grid` → three placeholders, each with title + caption children).

- [x] Theme toggle works across both routes
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: Dark, Light, and System modes all apply uniformly to Zone 1 chrome, the body canvas, and all three placeholder cards (borders, backgrounds, title and caption colours). System mode correctly resolves to the OS theme (Dark on this machine). Theme stays applied across route navigation `/` → `/analysis` → `/`. **Known exception**: the company selector dropdown and the Custom date range picker do not inherit theme tokens (F7 — see Findings).

- [ ] AG Grid renders in both themes
  - [ ] verified existing
  - [ ] verified behaving correctly
  - notes: **Cannot exercise this artifact during Phase 1 close-out.** AG Grid lives in Zone 4 (Holdings Table) per spec; Zone 4 is currently a placeholder card with no grid inside it. AG Grid theme propagation will be exercised when Zone 4's first real component ships in a future session. The existing `MEMORY.md` Active Decisions open loop on "AG Grid dark↔light visual check" stays open until then.

- [x] `tests/test_served_layout.py` exists and passes
  - [x] verified existing
  - [x] verified behaving correctly
  - notes: `python -m pytest tests/test_served_layout.py -v` returns `test_all_callback_ids_resolve PASSED` (0.07s). The test asserts callback IDs resolve against the union of served-layout + page-registry IDs; passes against the post-PR-50 served DOM including the three new placeholder IDs.

---

## Live exercise log

Time stamps approximate to "Session 16 working day, 2026-05-15." Walkthrough conducted on Windows desktop, browser maximised.

### Launch

- 2026-05-15 — `cd C:\MFIP\repo` + `git rev-parse HEAD` → `70792e8` (post Item B merge) → `git status` clean → `.\.venv\Scripts\Activate.ps1` activated → `python -m pytest -q` → `56 passed in 10.47s` → `python -m mfip.dashboard` → `Dash is running on http://127.0.0.1:8050/`, no errors
- 2026-05-15 — Open `http://127.0.0.1:8050/` in browser → Home stub renders correctly
- 2026-05-15 — Navigate to `http://127.0.0.1:8050/analysis` → Zone 1 renders at top; **vast empty canvas below** — Zones 2-4 not visible. Initial diagnosis suspected DOM-absence. Page source check (Ctrl+U) on `/analysis` returned only the React mount point — confirmed substantive Phase 1 finding (later resolved as F5).

### Zone 1 — Command Centre

- 2026-05-15 — Company selector dropdown → opens cleanly, shows all six tickers (EQNR, DNB, TEL, NOVO B, MSFT, CKN). **Theme inheritance broken**: in Dark/System modes, dropdown text is transparent over dark canvas (unreadable); in Light mode dropdown shows white background with black text (readable but unstyled). Logged as F3, subsumed into F7.
- 2026-05-15 — Theme toggle (cog → popover with Dark/Light/System radios) → switches mode, colours update across Zone 1 and (after PR #50) the placeholders. **Popover does not close on outside-click** — must click toggle again to dismiss. Logged as F1.
- 2026-05-15 — Global Date Filter preset buttons (1Y/3Y/5Y/MAX) → all clickable, active state shows correctly.
- 2026-05-15 — Custom date filter button → opens date range picker showing "MM/DD/YYYY → MM/DD/YYYY" inputs. **Does not close on outside-click**, but **does close** when any preset (1Y/3Y/5Y/MAX) is selected. Logged as F4a-dismiss. **Theme inheritance broken** in Dark mode (white inputs on dark canvas). Logged as F4a-style, subsumed into F7. At narrow viewport widths the picker fallback layout stacks vertically rather than horizontally (preference: prefer horizontal with smaller text). Logged as F8, sub-bullet under F7.
- 2026-05-15 — Alert badges (red/amber/yellow with placeholder "0" counts) → render correctly with placeholder counts.
- 2026-05-15 — Idle status indicator (`● Idle`) → displays correctly per spec (display-only status, not interactive). No tooltip explaining the four possible states (Normal/Warnings/Critical/Idle). Logged as F4b-i.
- 2026-05-15 — Active-jobs counter (un-coloured `0`) → hover reveals "Extraction: 0 | Modelling: 0 | Complete: 0" tooltip, exactly per spec. Working as intended.
- 2026-05-15 — Settings cog → opens theme popover (the cog is the theme toggle entry point). No label or tooltip on the cog itself indicating it's specifically for themes. Logged as F2.

### Zone 2 — Company Deep Dive (placeholder container)

- 2026-05-15 — Initial check: container exists in DOM (confirmed via Item C-1 discovery — `id="zone-2"`, `class="zone-placeholder"`) but renders to zero visible pixels (no layout CSS, no internal content). Logged as F5.
- 2026-05-15 (post PR #50) — Visible bordered card occupying ~60% of body width, top-left. Title "Zone 2 — Company Deep Dive" centred in the card, "Phase 1 placeholder" caption below. Reads as inert chrome. Theme propagation works (Dark/Light both apply).

### Zone 3 — Intelligence Feed (placeholder container)

- 2026-05-15 — Same trajectory as Zone 2: empty inert container pre-PR-50, visible bordered placeholder card post-PR-50. ~40% of body width, top-right. Title "Zone 3 — Intelligence Feed" + caption "Phase 1 placeholder."

### Zone 4 — Portfolio View (placeholder container)

- 2026-05-15 — Same trajectory: empty pre-PR-50, visible post-PR-50. Full body width spanning the bottom ~35% of body height. Title "Zone 4 — Portfolio View" + caption "Phase 1 placeholder."
- 2026-05-15 — AG Grid theme check **not exercisable** — Zone 4 is a placeholder card with no AG Grid inside. The AG Grid dark↔light visual check open loop stays open until Zone 4's Holdings Table ships in a future session.

### Cross-cutting

- 2026-05-15 — Full-screen on Windows desktop (browser maximised) → layout fills viewport, no overflow, no scrollbar, zones proportioned correctly per spec (60/40 horizontal × 65/35 vertical).
- 2026-05-15 — Resize browser window to roughly half-width → grid reflows beautifully. Zone 2 and Zone 3 maintain 60/40 ratio at narrow width; Zone 4 stays full-width; gaps remain consistent at ~8px; borders intact; no content overflow, no broken layout. CSS Grid `fr` units doing their job exactly as intended. **Confirmed working as intended.** Exception: Custom date picker's open popover stacks vertically at narrow widths (F8 under F7).
- 2026-05-15 — Theme persistence across route navigation `/` → `/analysis` → `/` → theme preserved as expected.
- 2026-05-15 — Tab order from URL bar → focus walks all Zone 1 interactive elements in order: Critical badge (red `0`) → Warning badge → Advisory badge → preset buttons 1Y/3Y/5Y/MAX/Custom → company dropdown → theme cog. Every focused element shows a visible focus ring. Placeholders correctly inert (no tab-stops). **Supersedes Session 7 Parts 2-3 worklog OPEN entries** about focus-ring invisibility on Zone 1 non-native interactive elements. Logged as F9.

### Tests

- 2026-05-15 — `python -m pytest -q` → `56 passed in 10.22s`
- 2026-05-15 — `python -m pytest tests/test_served_layout.py -v` → `test_all_callback_ids_resolve PASSED in 0.07s` (1 test collected, 1 passed)

---

## Findings

### Working as intended

- **Layout proportions per spec** — 60/40 horizontal split between Zones 2 and 3, 65/35 vertical split between Zones 2+3 and Zone 4. Visually correct in both Dark and Light modes.
- **Theme propagation across Zone 1 + all three placeholders** — Dark, Light, and System modes all apply uniformly to Zone 1 chrome, body canvas, and the three placeholder cards (borders, backgrounds, title and caption colours). Known exceptions documented under F7.
- **Resize reflow at narrow widths** — grid shrinks proportionally, gaps remain consistent at ~8px, no content overflow, no scrollbar appears, no broken layout. CSS Grid `fr` units behaving correctly.
- **Active-jobs counter hover breakdown** — un-coloured `0` in Zone 1 reveals "Extraction: 0 | Modelling: 0 | Complete: 0" on hover, exactly per `05_DASHBOARD_SPEC.docx` spec.
- **Tab order across Zone 1** — focus walks all interactive elements (alert badges → date preset buttons → company dropdown → theme cog) with visible focus rings on every focused element. Placeholders correctly inert (no tab-stops). Logged as F9. **Supersedes Session 7 Parts 2-3 worklog OPEN entries** about focus-ring invisibility on Zone 1 non-native interactive elements — those concerns are resolved by current state, not just deferred.
- **IDEA-023 graduated served-layout smoke test** — `tests/test_served_layout.py` passes against the post-PR-50 served DOM, including the three new placeholder container IDs (`zone-2`, `zone-3`, `zone-4`).
- **Theme persistence across route navigation** — theme stays applied when navigating `/` ↔ `/analysis`.
- **Custom date picker dismissal via preset selection** — picker closes cleanly when any preset (1Y/3Y/5Y/MAX) is clicked. Outside-click dismissal still missing (logged as F4a-dismiss), but a usable recovery path exists.

### Issues discovered (fixed in this session)

- **F5 — Zone 2-4 placeholder containers shipped without layout or visible content.** Discovered during the live walkthrough: containers existed in DOM as inert empty `html.Div`s with IDs `zone-2`/`zone-3`/`zone-4` and class `zone-placeholder`, but no CSS targeted any of those IDs and the divs were content-empty — they rendered to zero visible pixels. Fixed in PR #50 (Session 16 Item C-1) by adding CSS Grid layout in new file `mfip/dashboard/assets/analysis-layout.css` plus title and caption children to each placeholder. Container IDs unchanged so the same IDs carry through to when each zone's real components ship. Closed.

### Issues discovered (fixed in later sessions)

- (none for this validation — all issues either fixed in-session or deferred)

### Issues discovered (deferred)

New findings from the walkthrough — all logged to `worklog.md` for future Zone 1 chrome cluster or architectural follow-up:

- **F1 — Theme popover doesn't close on outside-click.** Must click the cog again to dismiss. → `worklog.md` outside-click-dismissal cluster (with F4a-dismiss).
- **F2 — Theme cog needs a tooltip / label.** The cog icon gives no indication that it opens the theme selector specifically. → `worklog.md` Zone 1 chrome cluster.
- **F4a-dismiss — Custom date range picker doesn't close on outside-click**, but does close when any preset (1Y/3Y/5Y/MAX) is selected. Recovery path exists but isn't intuitive. → `worklog.md` outside-click-dismissal cluster (with F1).
- **F4b-i — `● Idle` indicator has no tooltip explaining its four possible states** (Normal pulse / Warnings amber / Critical red / Idle muted). → `worklog.md` Zone 1 chrome cluster.
- **F7 — Dash core components (Dropdown, DatePickerRange) don't inherit theme tokens.** Architectural finding: Dash-bundled components render with their own stylesheets that don't reference the dashboard's CSS variables. The company selector dropdown text is invisible in Dark/System modes (transparent over dark canvas) and readable but unstyled in Light mode. The Custom date picker has the same problem. Both surface a single underlying gap that needs a `mfip/dashboard/assets/dash-component-overrides.css` file (sibling pattern to `ag-grid-overrides.css`). F3 and the styling dimension of F4a both subsumed into F7. → `worklog.md` new entry, architectural — not Zone 1 chrome cluster.
- **F8 (sub-bullet under F7) — Custom date picker narrow-width preference.** At narrow viewports the picker's open popover falls back to a vertical stack; preference is for the dates to stay inline horizontal with smaller text. Same root cause as F7 (Dash component layout overrides needed), captured as a specific instance of the architectural work. → `worklog.md` as sub-bullet of F7 entry.

Pre-existing deferrals confirmed still appropriate at Phase 1 close-out:

- **Zone 1 chrome styling completeness — partially resolves.** Focus-ring visibility across all Zone 1 interactive elements is **confirmed working today (F9)** — this supersedes the Session 7 Parts 2-3 OPEN entries about focus-ring invisibility. The remaining components of this cluster (badge styling refinement, theme application completeness on Dash core components) merge into F7 architectural work.
- **Zone 1 settings-panel density-roomy class missing** — `worklog.md` 2026-05-13 entry stays open. One-line fix scheduled with Zone 1 chrome cluster work.
- **AG Grid dark↔light visual check** — cannot close this loop yet. AG Grid renders only when Zone 4's Holdings Table ships in a future session. `MEMORY.md` Active Decisions open loop stays open until then with the framing adjusted to "exercisable at Zone 4 first-component build."
- **Home screen contents design** — still deferred per `ideas.md` 2026-05-10 "Project Dashboard View" entry. Phase 1's Home deliverable is a working stub at `/`, not a designed Home page.
- **Backtesting Panel placeholder not built** — Phase 1 checklist item left unticked. Tab-view framing predates the multi-route stance per `worklog.md` 2026-05-13 entry; full backtesting is v2. Phase 1 close-out accepts this as deferred-by-design.
- **Security Alert overlay not exercised** — modal only appears when a Critical alert fires; idle dashboard correctly shows no overlay. Overlay rendering will be exercised at Phase 8 (Security Council build).

---

## Sign-off

- [x] I have personally walked through every deliverable and runtime artifact above and confirmed each one. New findings (F1, F2, F4a-dismiss, F4b-i, F7, F8) are logged in `worklog.md` per the boundary rule. F5 (the substantive Phase 1 gap) was fixed in-session via PR #50. F9 (focus-ring visibility) supersedes prior Session 7 worklog entries and is recorded under "Working as intended."

**Signed:** Magnus Thomassen
**Date:** 2026-05-15
