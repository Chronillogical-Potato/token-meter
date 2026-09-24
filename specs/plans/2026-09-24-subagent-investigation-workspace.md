# Subagent Investigation Workspace Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Turn Sessions -> Subagents into a parent-session investigation workspace with Issues, Sessions, and Roles views plus a persistent evidence inspector.

**Architecture:** Keep the existing content-free agent-usage payload and derive presentation groups in browser JavaScript. Join parent titles only from the existing local `/logs` inventory, render one grouped workspace and one sticky inspector, and reuse current filters and cohort evidence without changing accounting or projections.

**Tech Stack:** Dependency-free Python tests, embedded HTML/CSS/JavaScript in `page.html`, standard-library server and installer.

**Spec:** `specs/2026-09-24-subagent-investigation-workspace-design.md`

## Global Constraints

- Preserve existing routes, stored filters, accounting, and privacy boundaries.
- Use provider-reported roles as primary identity and never infer role from content.
- Keep incomplete lifecycle evidence separate from deterministic attention signals.
- Support wide desktop and 1024-pixel laptop layouts.

---

### Task 1: Lock investigation behavior with failing tests

**Files:**
- Modify: `tests/test_meter.py`

**Interfaces:**
- Consumes: current `filterSubagentInventory` output rows.
- Produces: contracts for `groupSubagentSessions`, `buildSubagentRoleRows`, and the new workspace markup.

- [ ] Add a Node-backed test proving issue groups exclude quiet parents and rank attention before incomplete-only parents.
- [ ] Add a Node-backed test proving role rows preserve runtime/kind boundaries and calculate median, p95, incomplete rate, and attention rate.
- [ ] Add a dashboard contract test for Issues, Sessions, Roles, the workspace grid, and inspector.
- [ ] Run the focused tests and confirm the new assertions fail for missing behavior.

### Task 2: Implement the investigation workspace

**Files:**
- Modify: `page.html`

**Interfaces:**
- Consumes: `usage.inventory`, existing filters, existing `/logs` session inventory, and current role cohorts.
- Produces: `groupSubagentSessions(rows, issuesOnly)`, `buildSubagentRoleRows(rows)`, and view-specific renderers.

- [ ] Replace duplicated triage, summary, insight, inventory, and inline-detail markup with the compact command bar, internal view switcher, grouped results, and sticky inspector.
- [ ] Implement pure grouping and role-stat helpers.
- [ ] Render Issues and Sessions as parent groups with child rows.
- [ ] Render Roles as cohort comparison rows.
- [ ] Render the selected child in the sticky inspector and preserve parent navigation.
- [ ] Load the existing session inventory on the Subagents route and rerender when it arrives.
- [ ] Add wide and 1024-pixel responsive styles and hide the general today strip only on the Subagents route.
- [ ] Run the focused tests and embedded-JavaScript parse check until green.

### Task 3: Update user documentation and verify

**Files:**
- Modify: `specs/USER_GUIDE.md`
- Modify: `specs/plans/active.md`

**Interfaces:**
- Consumes: implemented workspace behavior.
- Produces: accurate user-facing workflow documentation and current local execution state.

- [ ] Update the Subagents guide for Issues, Sessions, Roles, grouped parent sessions, and the inspector.
- [ ] Run focused tests, the full suite, Python compile, JavaScript parse, and `git diff --check`.
- [ ] Install the exact source runtime, verify `/health` and `/menubar`, and confirm source/runtime parity.
- [ ] Inspect the live workspace at wide desktop and 1024-pixel laptop widths.
- [ ] Route the final unmodified tree to one independent tester and one project reviewer.
