# Subagent Investigation Workspace

## Status

Approved in chat on 2026-09-24. This design refines the existing approved
Sessions -> Subagents explorer on `codex/subagent-observability`. Commits,
pushes, pull requests, and merges remain separately gated.

## Problem

The first explorer exposes the right evidence but presents it as a flat agent
inventory. The default view does not answer which parent session deserves
review, repeated summary cards compete for attention, parent-child context is
secondary, role analysis is buried, and expanding a row disrupts comparison.

## Design

Sessions -> Subagents becomes one investigation workspace with three internal
views:

- **Issues** is the default. It shows only parent sessions containing an
  incomplete child or a deterministic attention signal. Parent groups are
  ordered by review priority, then covered estimated child cost and recency.
- **Sessions** shows every matching parent group. Each group summarizes child
  count, incomplete and attention counts, covered estimated child cost, and
  latest activity before listing its matching children.
- **Roles** compares provider-reported roles. Each role keeps its runtime and
  kind boundary and shows runs, incomplete rate, attention rate, median and
  p95 covered estimated cost, tokens, and the most common observed model.

One compact command bar retains search, app, project, time, model, lifecycle,
signal, and sorting filters. A compact evidence strip replaces the separate
triage, summary, and zero-valued insight-card grids. Zero-valued attention
signals do not receive equal visual weight.

Selecting a child opens a sticky inspector beside the workspace rather than
inserting evidence into the list. The inspector shows exact identity, parent
context, content-free metrics, signal explanations, sibling position, and an
Open parent session action. At narrower supported desktop widths it remains a
second column as space permits and stacks below the list only when necessary.

Parent labels are joined in the browser from the existing `/logs` inventory.
The subagent projection remains content-free and unchanged. When the session
inventory is not yet ready, the UI uses a neutral parent-session label derived
from project and opaque identity rather than exposing new trace content.

The general Sessions "today" strip is hidden only while the Subagents route is
active so investigation controls and findings remain above the fold.

## Constraints

- Preserve `#sessions-subagents`, stored filters, existing accounting, and all
  current privacy and unavailable-evidence semantics.
- Provider roles remain primary identity; nicknames remain secondary.
- Incomplete remains a lifecycle state, not a diagnosis or attention signal.
- Attention copy remains deterministic and threshold-based.
- No prompt, response, reasoning, tool content, raw path, or provider account
  data enters the workspace.
- Support wide desktop and 1024-pixel laptop layouts.

## Validation

- Node-backed behavior tests cover parent grouping, issue ordering, and role
  cohort calculations.
- Dashboard source contracts cover the three views, sticky inspector, compact
  summary, and removal of the old duplicated card layout.
- Embedded JavaScript parsing, focused and full Python tests, `git diff
  --check`, installation, live endpoints, source/runtime parity, and browser
  checks at wide desktop and 1024 pixels are required.
