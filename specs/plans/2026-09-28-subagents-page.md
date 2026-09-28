# Dedicated Subagents Page Implementation Plan

> **For agentic workers:** Use test-driven development and the Token Meter standard verification route. This plan is executed inline by the coordinator as the sole tracked-file writer. Do not commit without explicit user authorization.

**Goal:** Give Subagents a primary navigation home and display useful, coverage-aware role spend metrics.

**Architecture:** Keep existing privacy-safe aggregate payloads and inventory. Mount the shared explorer in the top-level page for Roles, and under Sessions for child-run Sessions and Issues; retain distinct hashes and covered-cost metrics.

**Tech Stack:** Dependency-free Python server, embedded JavaScript/CSS in `page.html`, Python unittest invoking Node for dashboard behavior.

**Spec:** `specs/2026-09-28-subagents-page-design.md`

## Global constraints

- Keep numbered Option shortcuts in visible rail order and preserve stored filters.
- Preserve `#sessions-subagents` as the investigation route and Back from View runs and selected parent session.
- Never infer missing cost as zero or change pricing.
- Do not overwrite the concurrently used installed runtime at 8722.

## Task 1: Coverage-aware role economics

**Files:** `tests/test_meter.py`, `page.html`.

**Interface:** `buildSubagentRoleEconomics(usage, filters, nowMs)` returns `runs`, `costCovered`, `cost`, `averageCost`, and comparison fields. `renderSubagentRoleEconomics(economics)` presents them.

- [x] Add a partial-coverage fixture; assert known spend, cost per priced run, coverage, and no spend delta. Add a zero-covered-run case that stays unavailable.
- [x] Run the focused test and confirm it fails because `cost` and `averageCost` are null.
- [x] Change `totals()` to retain known covered spend and use `costCovered` as the average denominator; keep `costComplete` to guard deltas. Render `Covered spend` and `Cost / covered run` when coverage is incomplete.
- [x] Rerun the focused test and the existing role-economics tests.

## Task 2: Primary navigation and compatibility

**Files:** `tests/test_meter.py`, `page.html`, `specs/AGENTS.md`, generated discovery files if needed.

**Interface:** `#subagents` is the primary Roles route; `#sessions-subagents` is the Sessions investigation route. `showTab('subagents')` controls `#view-subagents`.

- [x] Add a navigation contract test that checks the new top-level view and legacy route; verify it fails on the old nested layout.
- [x] Mount the explorer DOM into `#view-subagents` for Roles, add the sidebar tab after Models, and retain the Sessions → Subagents sub-tab for Sessions and Issues. Keep existing element IDs and stored filter keys.
- [x] Update route handling, live refresh, role-to-runs history, and parent-session return behavior. Number Subagents ⌥4 and shift later shortcuts through Settings ⌥9.
- [x] Rerun navigation tests, then browser-check direct links, View runs, Back, parent session, and legacy link.

## Task 3: Professional page hierarchy

**Files:** `page.html`, focused dashboard tests, `specs/ARCHITECTURE.md` and relevant user navigation docs.

- [x] Add focused assertions for visible coverage labeling and the role/session/issue hierarchy, tied to rendered output where practical.
- [x] Replace repeated copy with one page purpose line, compact metric labels, and short row details. Retain per-role daily charts and incomplete/run counts. Keep color subordinate to numeric cost.
- [ ] Parse embedded JS, run focused tests and the broader suite, inspect `git diff --check`, and browser-check wide desktop plus 1024 px.
- [ ] Send the unchanged final diff to an independent Token Meter tester and reviewer; rerun the gates after any tracked edit.
