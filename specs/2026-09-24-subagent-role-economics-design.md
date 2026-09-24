# Subagent Role Economics Design

## Goal

Make the Subagents → Roles view useful for reducing the spend of named custom
subagents over time without treating lower spend as proof of better outcomes.

## Chosen approach

Use a hybrid aggregate-and-drill-down design:

- Backend role cohorts provide exact current and prior-period metrics for the
  selected app, project, and time window.
- A bounded, content-free daily role series provides trend shape and volume.
- The existing inventory remains the drill-down source for individual runs.

This avoids deriving long-term totals from the bounded inventory. It also makes
coverage explicit: a spend or change value is shown only when every run in both
compared periods has cost evidence.

## Page structure

Roles remains the first Subagents tab. Its results area becomes a compact
role-economics workspace with three layers:

1. A three-metric strip for named-role spend, average cost per run, and spawned
   runs, with cost coverage kept in supporting copy.
2. A shared Spend, Cost/run, and Runs control that renders a distinct daily
   chart for every provider-reported role.
3. Compact role rows retaining run count, cost coverage, average/P95 cost,
   incomplete and review counts, and a View runs drill-down. That drill-down is
   a browser-history transition so Back restores the prior Roles state.

The existing App, Project, and Time range filters apply to the analytics.
Search, Model, Status, and Signal remain inventory-level filters. When any of
those filters is active, the page explains that trend analytics are unavailable
for that filter instead of silently mixing scopes.

## Data contract

`aggregate_agent_usage()` adds two content-free structures:

- Each non-`all` scope gets a `comparison` body for the immediately preceding
  equal-duration period.
- `role_days` groups named roles by local calendar day, project, runtime, kind,
  and provider-reported role. Each row includes the existing detailed totals
  plus activity-state counts and deterministic attention count.

The daily series is bounded and carries count/truncation metadata. If it is
truncated, exact trend calculations are withheld. Public projection continues
to use an explicit allowlist. No prompt, response, reasoning, tool content,
credential, account data, or raw trace field is added.

Provider-reported role identity is authoritative. Token Meter does not infer a
role from a nickname, prompt, file, project, or conversation.

## Comparison and insight rules

- Spend change requires complete cost coverage in both periods.
- Cost per run uses total covered cost divided by runs only when coverage is
  complete.
- Run-volume change is always arithmetic when both periods exist.
- P95/median is described as long-tail concentration, not as a diagnosis.
- Incomplete and deterministic attention rates are guardrails. They do not
  measure correctness or outcome quality.
- “Improved” means lower estimated cost per run for comparable role identity and
  period only. The page does not claim a prompt is better or work is successful.

For `Any time`, the page shows the full available trend without a comparison
delta. For 24h, 7d, 30d, and 90d, it compares the selected period to the
immediately preceding period of the same duration.

## Interaction

- Chart mode is persisted locally.
- Chart legend ranks the highest-spend named roles and groups the remainder as
  “Other roles”.
- Selecting “Inspect runs” for a role switches to Sessions with that role in the
  search field, preserving app, project, and time context.
- Unavailable values render as `--`; no missing value becomes zero.

## Error and empty states

- No named roles: explain that the provider did not expose role identity.
- Missing cost coverage: show run counts and coverage, but withhold spend and
  change.
- Daily-series truncation: show the role table and a bounded-data warning; hide
  exact trend and period insights.
- No prior period: say “No prior-period baseline” instead of showing zero change.

## Responsive design

Wide desktop uses a two-column trend/insight row. At 1024 pixels the insight
panel stacks below the chart and the role table remains horizontally scrollable.
Sub-1024 layouts are outside the supported product target.

## Testing

- Domain tests cover current/prior window boundaries, role-day grouping,
  coverage, attention counts, and truncation.
- Projection tests prove only allowlisted role-day and comparison fields leave
  the backend.
- Dashboard JavaScript tests cover period comparison math, unavailable coverage,
  chart rendering, fine-filter suspension, and role-to-session drill-down.
- Run embedded JavaScript parsing, focused Python tests, full unit discovery,
  `git diff --check`, installation, `/health`, `/menubar`, runtime parity, and
  browser checks at wide desktop and 1024 pixels.

## Alternatives considered

1. Inventory-only charts: rejected because the 1,000-row display bound can make
   totals and trends incomplete.
2. A new endpoint with arbitrary query dimensions: deferred because it expands
   the server API and privacy surface without being necessary for the first
   optimization loop.
3. The chosen hybrid: exact predefined period aggregates plus bounded daily
   trends and existing run drill-down.
