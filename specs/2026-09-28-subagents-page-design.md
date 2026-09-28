# Dedicated Subagents Page

## Purpose

Make repeated custom-agent runs easy to compare over time while keeping session-level investigation one click away. Cost per run is a spending proxy, not a quality or productivity score.

## Placement and navigation

Subagents becomes a primary dashboard page directly after Models, containing only Roles. Sessions retains Current sessions, All sessions, and a Subagents investigation tab with Sessions and Issues views. `#subagents` and `#sessions-subagents` are distinct canonical routes. The primary rail follows visible order for numbered keyboard shortcuts: Subagents is ⌥4, Efficiency ⌥5, Git ⌥6, Learn ⌥7, Tools ⌥8, and Settings ⌥9; Performance and Read remain unnumbered. A role's View runs action opens the latter route with exact role, app, and child-kind filters; Back restores the originating Roles view and filters. A child's Open parent session action also adds a browser-history entry.

## Information architecture

- Header: title, one-sentence purpose, and a compact count of named roles and runs.
- Filter rail: time range, app, project, and role search visible; model, status, signal, and sort remain in More filters. Filters are not duplicated inside results.
- Roles: three headline metrics (covered role spend, cost per covered run, named runs) followed by a concise ranked role list. Each role keeps its own daily chart and View runs action. Coverage and incomplete counts appear only where they qualify a value.
- Sessions → Subagents → Sessions: parent-session groups with spawned-run counts, relative child-cost color, and a matching-run model distribution scoped by app and model; child inspector on selection.
- Sessions → Subagents → Issues: incomplete runs and explicit cost/retry evidence, not a generic diagnosis.

No new backend data is required. The existing exact scoped role aggregates and bounded role-day series remain the source for role charts. Bounded inventory supplies drill-down and model distribution; when truncated, the breakdown is explicitly labeled visible-runs-only. Missing cost is not counted as zero.

## Cost and comparison rules

If 231 of 233 named-role runs have cost, display their known spend and divide by 231 for cost per covered run. Show `231 / 233 cost-covered` next to the numbers; do not imply the values include the other two runs. If zero runs have cost, show an unavailable value, never `$0`. A role with incomplete cost evidence follows the same covered-only rule. Prior-period change in spend or cost per run is shown only when both compared periods have complete cost coverage; run-count change may still be shown. Daily spend and cost/run charts are withheld on days whose cost evidence is incomplete, rather than plotting missing cost as zero.

The existing local API-rate estimate labeling stays visible once on the page. No prompt, response, reasoning, tool content, raw trace, or arbitrary provider string enters a new projection.

## Crispness and accessibility

Use one page-level explanation and terse headings: Roles in the primary page, Sessions and Issues in the investigation tab; Covered role spend, Cost / covered run, Named runs. Remove repeated descriptive sentences, generic attention badges, and duplicated counts. Keep numeric values visible next to color, meaningful accessible names, and an explicit cost-coverage note. Wide desktop and 1024-pixel laptop are supported; sub-1024 layouts are outside this product target.

## Validation

Regression tests exercise incomplete and zero cost coverage, comparison suppression, distinct routes, exact-role drill-down/Back, runtime-scoped model distribution, and preserved spawned-run counts. Parse embedded JavaScript and browser-check wide and 1024-pixel layouts with live sanitized local evidence. Independent tester and reviewer inspect the final diff. Installing over the concurrently used 8722 runtime is out of scope for this iteration.

## Alternatives

Keeping Roles nested under Sessions makes ongoing optimization hard to find. Moving the entire explorer to the new primary page wrongly relocates run investigation. The chosen split gives role economics a clear home and preserves Sessions as the place to inspect child runs and issues.
