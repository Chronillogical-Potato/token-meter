# Dedicated Subagent Explorer Implementation Plan

**Goal:** Make cross-session subagent analysis a distinct, filterable Sessions
page; display provider-reported agent roles as the primary identity; distinguish
incomplete work from cost/retry attention signals; and replace ambiguous
Sessions coverage abbreviations with exact evidence wording.

**Architecture:** Extend the existing agent aggregate with a bounded public
inventory containing only content-free child-agent metadata. The Sessions
surface gains a third `#sessions-subagents` subroute that filters this inventory
in the browser and reuses the existing aggregate cohorts for comparison charts.
Runtime adapters remain responsible for activity classification, while the
shared domain and projection layers enforce status and privacy allowlists.

**Constraints:** Preserve global accounting totals, session identity, MCP,
native, and telemetry contracts. Never project trace paths, prompts, responses,
tool contents, raw provider rows, or private physical IDs. A truncated inventory
must be labeled and must not produce apparently complete filtered totals.

## Task 1: Specify Identity and Activity Semantics

**Files:**
- Modify: `specs/2026-09-22-subagent-observability-design.md`
- Modify: `tests/runtimes/test_codex_adapter.py`
- Modify: `tests/test_claude_cost_correctness.py`
- Modify: `tests/domain/test_agents.py`

- [x] Add failing tests proving stale nonterminal Claude and Codex agents are
  `incomplete`, while terminal agents remain `complete` and live agents remain
  `working`.
- [x] Add a failing presentation test proving a safe provider role such as
  `token_meter_reviewer` is primary and a nickname is only secondary.
- [x] Add `incomplete` to the shared allowlist and implement the adapter
  classifications without treating incompleteness as an attention signal.
- [x] Run the focused runtime and domain tests.

## Task 2: Add a Bounded Public Agent Inventory

**Files:**
- Modify: `token_meter/domain/agents.py`
- Modify: `token_meter/projections.py`
- Modify: `token_meter/app.py`
- Modify: `tests/domain/test_agents.py`
- Modify: `tests/contracts/test_public_projections.py`
- Modify: `tests/test_meter.py`

- [x] Add failing tests for a child-only inventory with stable root-session,
  project, runtime, model, role/nickname, activity, tokens, cost, timing, and
  allowlisted attention reasons.
- [x] Prove the inventory is deterministically bounded and reports total,
  visible, and truncated counts.
- [x] Prove private membership fields, physical IDs, paths, content, and unknown
  input keys cannot cross the projection.
- [x] Implement the aggregate and projection changes, then run focused domain,
  contract, composition, MCP, and native-payload compatibility tests.

## Task 3: Build Sessions -> Subagents

**Files:**
- Modify: `page.html`
- Modify: `tests/test_meter.py`

- [x] Add failing Node-backed tests for the third Sessions route, legacy hash
  preservation, role-first identity, multi-filter behavior, sorting, incomplete
  counts, attention-reason counts, and truncated-inventory withholding.
- [x] Add a dedicated `#sessions-subagents` panel with search, app, project,
  model, status, signal, time-range, and sort controls.
- [x] Add summary cards for child agents, parent sessions, cost coverage, and
  incomplete agents; add transparent insight cards for each attention rule.
- [x] Render a filterable child-agent table linking each row to its root
  session. Keep nicknames as fallback identity and show them secondarily only
  when a provider role exists.
- [x] Move the existing cohort comparison chart from Sessions -> All into the
  new page.
- [x] Verify keyboard operation, focus states, empty states, and layout at wide
  desktop and 1024-pixel laptop widths.

## Task 4: Replace Ambiguous Sessions Coverage Phrasing

**Files:**
- Modify: `page.html`
- Modify: `tests/test_meter.py`

- [x] Add failing behavior tests for exact coverage counts and long-form local
  estimate wording in Sessions -> All and Sessions -> Subagents.
- [x] Remove visible `partial`, `est`, and `incl. est` abbreviations from those
  two Sessions pages. Keep unavailable evidence unavailable and state exact
  covered/total counts in notes or labels.
- [x] Parse the embedded JavaScript and rerun the Sessions dashboard tests.

## Task 5: Verify the Amendment

- [x] Run all focused domain, adapter, projection, composition, MCP, and browser
  tests.
- [x] Run the full unit suite and compare any failure with the untouched base.
- [x] Run Python compilation, embedded-JavaScript parsing, shell syntax, Swift
  compilation/smoke, and `git diff --check`.
- [x] Install from this worktree, verify `/health`, `/menubar`, LaunchAgents,
  source/runtime parity, and the exact reported session.
- [x] Browser-check populated Token Meter and Luna-3 filters at wide desktop and
  1024-pixel laptop widths with no console errors or horizontal overflow.
- [x] Stop before commit, push, or pull request; those remain separately gated.

## Task 6: Refine the Investigation UX

**Files:**
- Modify: `page.html`
- Modify: `tests/test_meter.py`

- [x] Add failing behavior tests for triage presets, staged results, and the
  evidence inspector before changing the dashboard implementation.
- [x] Replace the dense two-row filter form with a triage-first header,
  progressive filters, and individually removable active-filter chips.
- [x] Make attention-signal insights interactive and preserve project, app,
  time, search, and model context when applying a triage preset.
- [x] Render 50 agents at a time and add an inline evidence inspector with a
  separate `Open parent session` action.
- [x] Move cohort comparisons behind a compact disclosure after the agent
  results so investigation remains the primary workflow.
- [x] Rerun focused tests, source gates, installed-runtime checks, and browser
  verification at wide desktop and 1024-pixel laptop widths.
