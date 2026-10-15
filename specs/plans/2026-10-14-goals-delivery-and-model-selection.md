# Goals: delivery evidence, chart inspection, and multiple models

Date: 2026-10-14. Status: source implementation complete and uncommitted after
user approval. Runtime behavior and independent gates remain unverified.

## Objective

Address the four follow-up requests: show Lines pushed in delivery contributors,
inspect the to-date chart by hovering, select multiple models when creating a
goal, and explain whether All projects includes every repository.

Use the existing Goals engine, watcher-published Git evidence, dashboard design
system, and settings store. Preserve existing goals and prior work.

## Source findings and decisions

- Git evidence measures pushes by repository/day, without session attribution.
  Delivery contributors must therefore be repository rows. Other metrics retain
  their session contributors.
- Lines pushed means additions plus deletions, matching the current delivery
  denominator. Explain this beside the column; do not change the metric formula.
- All projects currently means eligible repositories discovered from local agent
  activity. It does not inventory every repository on disk. Discovery is capped
  at 50 repositories; the eight-row driver preview is a separate display limit.
- Eligibility requires spend evidence and measured Git coverage for the chosen
  period. Measured coverage with zero pushed lines differs from missing coverage.
  The aggregate rate needs at least 50 changed lines and positive covered spend.
- Current delivery session contributors can include spend outside the metric's
  eligible repository population. Correct that inconsistency with repository
  contributors derived from the same Git query as the headline.
- Reuse the existing Efficiency/Git chart inspection behavior and Models/Efficiency
  checkbox picker presentation. Goal model identity remains runtime plus model;
  effort variants must not become separate model selections.
- Delivery goals retain All apps / All models: pushes have no model attribution.
  Frontier-share goals retain their existing All models restriction in this round;
  changing the population for a frontier share needs a separate semantic decision.
  Other metrics support multiple observed models.

## Phase 1 — reconcile repository coverage

Inspect sanitized evidence for the reported period and compare the goal's Git
query with the Git surface and watcher snapshot. Establish whether two repositories
reflect discovery, period coverage, spend matching, baseline history, or display
truncation before naming a cause. Source inspection alone cannot establish this.

Use the same canonical repository mapping, published candidates, and cached
query window throughout. Audit worktree aliases and same-name repositories.
Fix a demonstrated matching or projection defect within those boundaries.
Do not scan disk from a goal request, reset the ledger, or raise discovery limits
as an unexplained workaround.

Expose a concise coverage summary and expandable repository evidence using the
existing disclosure: included count, discovered count, covered spend share,
period, freshness, and known limits. Explain that the headline includes every
eligible repository even when a preview shows fewer rows. Preserve distinguishing
safe repository suffixes; never expose paths. Display repository-specific reasons
only when supported by repository evidence; global scan limits stay global.

Acceptance:

- Every eligible repository contributes to the aggregate, beyond the preview limit.
- Missing evidence is distinguishable from measured zero.
- The displayed inclusion population reconciles with headline cost and lines.
- The explanation of the reported two repositories is evidence-backed, or clearly
  remains unresolved if the user's runtime evidence is unavailable.

## Phase 2 — add delivery repository contributors

In `token_meter/services/goals.py`, derive delivery contributors from the exact
eligible rows used by `_git_measure`, using the same cached query and period.
Return bounded safe repository labels, covered spend, changed lines, rate,
spend share, and total eligible count. Rank Biggest contributors by covered spend;
make that ranking basis explicit. Keep totals over the full population.

In `page.html`, render these columns with existing table styles:

Repository | Spend | Lines pushed | Cost per 1K pushed lines | Spend share

Reuse current currency/integer formatting and evidence labels. A row with zero
lines has an unavailable rate rather than a zero rate. Apply existing measurement
thresholds consistently and explain unavailable rates. Do not assign repository
lines to sessions or add a second session table in this round.

Acceptance: headline, repository contributors, drivers, and coverage disclosure
agree on period, repository identity, cost basis, and denominator. Other goal
metrics keep their existing contributor behavior.

## Phase 3 — inspect the goal to-date chart

Upgrade `goalTrendChart` for every goal detail using the established chart tooltip,
nearest-date pointer selection, inspection marker, and keyboard pattern. Show date,
cumulative-to-date metric value with its unit, and target. Missing dates show
No data; do not connect lines across missing evidence or invent interpolated values.
Retain cumulative calculations rather than averaging daily ratios.

Size the SVG viewBox to the rendered element and register it with `PIXEL_CHARTS`.
Observe the dynamically inserted detail chart after rendering, release the old
observer when detail is replaced, and repaint from cached detail data on resize.
Reuse design tokens and `.chartTip`; include focus, arrow keys, Home/End, and an
accessible inspection announcement. Preserve list sparklines and navigation.

Acceptance: pointer and keyboard inspection select the same data at desktop and
1024-pixel widths; one-point, missing-point, zero, and empty series behave clearly.
Resize does not fetch data or accumulate event handlers/observers.

## Phase 4 — support a bounded model selection

### Data contract and calculation

Keep legacy `all`, `agent`, and single `model` records readable. Add a `models`
scope with a canonical sorted, deduplicated list of opaque model keys, limited
to 32 selections. A single selected model can retain the existing `model` format;
an empty selection uses the existing All models scope for the chosen App.
No model names or paths become new persisted identifiers.

Thread the resolved selection through normalization, write validation, preview,
baseline, collection/cache keys, daily filtering, coverage, active counts, drivers,
contributors, history, duplication, and public/native projections. Sum each selected
model's evidence once, then calculate a ratio from summed numerators/denominators.
Do not sum or average model ratios. Runtime identity keeps identical model names
in different clients separate. Handle mixed-model sessions using model evidence,
not the entire session's spend or tokens.

Preserve a saved key whose evidence disappears. Show an unresolved selection and
No result instead of silently broadening the goal or calculating a partial selected
population. Validate malformed, unsupported, duplicate, and over-limit keys through
existing action-token-protected atomic settings writes. Reads remain idempotent.

Extend preview request parsing with an explicitly bounded model-key list; the
current single-value length limit is insufficient. Use canonical selection keys
in evidence caches and preview race handling. Preserve existing budgets, repeat
anchors, numeric targets, and compatibility routes.

### Picker and consumers

Replace the goal's single Model select with the existing checkbox picker pattern:
All models, selected-count caption, checked options, bounded observed-model search,
Escape/outside-click handling, and retained selection across search results.
Keep unpriced observed models available, with cost evidence remaining unavailable
where appropriate. Pin all selected keys outside the returned shortlist.

All apps permits selections across runtimes. Selecting a model does not silently
change App. A deliberate App change retains compatible picks, clears incompatible
picks, and explains the change inline before saving. Preview follows the visible
selection. Delivery and frontier restrictions are explained beside their controls.

Update macOS and Linux goal summaries to display a bounded N models caption for
the new scope; it must never fall back to All. Preserve legacy single-model captions.
Inspect other consumers; make target-host claims only with target-host evidence.

Acceptance: create, edit, preview, repeat, duplicate, and history agree on selection;
old goals require no manual migration; unknown selections never expand the scope.
For ratios, combined-model results use aggregate evidence. Tokens do not count
cache/reasoning twice. A mixed session never contributes unrelated model usage.

## Files and delivery order

Expected code: `token_meter/services/goals.py`, `token_meter/app.py`, `page.html`,
and existing macOS/Linux goal summary consumers. Extend focused cases in
`tests/test_goals.py` using its current structure. Update `specs/GOALS.md` and the
README Goals description. Change Git service code only for a demonstrated defect.
No pricing changes, new dependencies, new settings store, or top-level page.

Implement phases sequentially as complete reviewable slices. Coverage and delivery
contributors establish a consistent evidence population before chart presentation;
model selection follows with its persistence and consumer work in one slice.

## Validation and handoff

Test execution and commits remain user-owned. During implementation, prepare focused
regression cases and report static parsing/compilation separately from executed tests.

User validation should cover:

- More than eight eligible repos; duplicate basenames/worktrees; spend-only and
  Git-only evidence; measured zero; partial/stale history; discovery-limit disclosure.
- Repository totals and all-project rate reconciliation against the same window.
- Chart hover/focus, missing days, one point, targets, navigation and resize at
  wide desktop and 1024 pixels; existing design-system contract.
- Legacy scopes; cross-runtime same-name models; mixed-model sessions; selected
  models beyond shortlist; unpriced/disappeared models; malformed/over-limit input;
  summed ratio denominators; token coverage; edit/duplicate/repeat/history.
- macOS compilation, native smoke/live caption, Linux consumer behavior, and
  installation with health, menubar payload, and source/runtime parity when authorized.

The implementation follows the high-risk route because scope persistence, shared
calculations, and native consumers change: one independent tester and two project
reviewers with distinct correctness and consumer/privacy lenses against an immutable
user-created commit. All prior round's unrun gates remain pending. Report actual
results, unresolved findings, and unsupported target-host behavior before readiness.

## Implementation handoff

- User approved implementation. One coordinator wrote the scoped source changes,
  preserved previous work, and prepared focused regression cases without executing
  tests. No commits, installation, or external writes were performed.
- Delivery headline, drivers, contributors, and coverage share one eligible Git
  population. Contributors expose additions-plus-deletions lines and full totals;
  labels retain safe distinguishing suffixes. No Git service measurement changed.
- Goal detail charts support pointer and keyboard inspection, missing-value gaps,
  pixel viewBoxes, and dynamic resize/observer cleanup.
- Model selection supports up to 32 canonical opaque keys, legacy records, union
  calculations, scope-aware active counts and breakdowns, preserved unavailable
  saved selections, preview request bounds, and native count captions.
- Updated page, Goals service, app query adapter, coaching coverage wording,
  macOS/Linux summaries, focused Goals cases, Goals documentation, and README.
- Sanitized local HTTP diagnosis could not reach the local server (URLError).
  The reported two-repository omission remains unconfirmed. Source mapping uses
  published canonical roots and aliases; no demonstrated matching defect was found.
- Python AST and embedded-JavaScript syntax parsing passed. Swift compilation
  initially failed at the sandbox's default module-cache path; retrying with
  `-module-cache-path /private/tmp/token-meter-swift-cache` passed. No binary was run.
- Unit/contract tests, browser checks at both widths, native smoke/live behavior,
  Linux runtime behavior, installation/parity, and independent gates remain pending.
  Static source checks are not evidence of runtime readiness.
