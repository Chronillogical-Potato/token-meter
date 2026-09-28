# Subagent Role Economics Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add trustworthy period-over-period charts and optimization context to the Subagents Roles view.

**Architecture:** Extend the existing domain aggregate with prior-period role cohorts and bounded daily role totals, project them through the public allowlist, and render the analytics in the existing Roles tab. Keep individual-run drill-down on the current inventory.

**Tech Stack:** Python standard library, embedded dashboard HTML/CSS/JavaScript, `unittest`, Node.js syntax/behavior checks.

**Spec:** `specs/2026-09-24-subagent-role-economics-design.md`

## Global Constraints

- Provider-reported role names only; never infer identity from content.
- No prompts, responses, reasoning, tool contents, credentials, account data, or raw traces in public payloads.
- Missing or incomplete cost evidence renders as unavailable, never zero.
- Keep `page.html` dependency-free and preserve existing Sessions navigation and stored preferences.

---

### Task 1: Exact role-period and daily aggregates

**Files:**
- Modify: `token_meter/domain/agents.py`
- Test: `tests/domain/test_agents.py`

**Interfaces:**
- Produces `agent_usage.scopes[].comparison` and `agent_usage.role_days` with count/truncation metadata.

- [ ] Write domain tests for equal-duration prior periods, named-role day grouping, activity/attention counts, coverage, and truncation.
- [ ] Run the focused tests and verify the new assertions fail because the structures are absent.
- [ ] Implement the smallest content-free aggregation helpers and wire them into `aggregate_agent_usage()`.
- [ ] Run the focused tests and verify they pass.

### Task 2: Public projection contract

**Files:**
- Modify: `token_meter/projections.py`
- Test: `tests/contracts/test_public_projections.py`
- Test: `tests/test_meter.py`

**Interfaces:**
- Consumes the domain structures from Task 1.
- Produces explicitly allowlisted comparison and role-day fields in `xsession.agent_usage`.

- [ ] Add projection tests that require allowed aggregate fields and reject injected private fields.
- [ ] Run the focused tests and verify failure from the missing projection.
- [ ] Add bounded projection constants/helpers and project comparison plus daily rows.
- [ ] Run the focused contract and cross-session tests until green.

### Task 3: Roles analytics workspace

**Files:**
- Modify: `page.html`
- Test: `tests/test_meter.py`

**Interfaces:**
- Consumes projected `scopes[].comparison`, `role_days`, and existing inventory.
- Produces KPI, chart, insight, coverage, and role-to-session drill-down UI.

- [ ] Add dashboard behavior tests for comparison math, unavailable coverage, fine-filter suspension, chart output, and drill-down state.
- [ ] Run the focused dashboard tests and verify the missing helpers/UI fail.
- [ ] Add responsive CSS, Roles analytics markup/rendering helpers, chart mode persistence, and inspect-runs interaction.
- [ ] Parse the embedded JavaScript and run focused dashboard tests until green.

### Task 4: Documentation and verification

**Files:**
- Modify: `specs/ARCHITECTURE.md`
- Modify: `specs/USER_GUIDE.md`
- Modify: `README.md` only if the public feature summary needs an update.

**Interfaces:**
- Documents the content-free aggregate, coverage semantics, and optimization workflow.

- [ ] Update architecture and user guidance with exact limits and unavailable-value behavior.
- [ ] Run focused tests, full unit discovery, Python compilation, JavaScript parsing, and `git diff --check`.
- [ ] Commit the implementation, install the exact source runtime, verify `/health` and `/menubar`, confirm source/runtime parity, and visually check wide desktop plus 1024-pixel layouts.
- [ ] Route the immutable commit to one independent tester and one independent project reviewer.
