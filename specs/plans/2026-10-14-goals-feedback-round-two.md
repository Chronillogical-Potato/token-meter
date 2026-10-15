# Goals: Pratik feedback, round two

Status: implemented in source, uncommitted, 2026-10-14. User-owned product
validation, installation, and independent gates remain pending. The design and
source inspections are not independent implementation gates.

## Objective and source

Complete the six requests in [Pratik's October 9 feedback](https://splunk.slack.com/archives/D0C1BGFKSSD/p1791548046714119):
separate Agent and Model selectors, token goals, more periods, explain missing
repositories, discoverable previous goals with duplication, and Hold current
level for every metric. Keep the simplified deterministic Goals experience.

Repository inspected: `FINOPS-7931-goals-development-phase-1`, commit
`2a88d7e425050986f4193ad834ae7eef6f89be77`. [PR #62](https://github.com/splunk/token-meter/pull/62)
had the same head when inspected during intake and was open. Its description
still described the superseded business-objective and Model Mix design.
These are point-in-time observations, not a continuing readiness claim.

Engineering and product boundaries: [Architecture](../ARCHITECTURE.md),
[Goals](../GOALS.md), [Design](../DESIGN.md), and [agent instructions](../AGENTS.md).

## Observed starting point (historical, before this round)

- `page.html` combines all agents, agents, and runtime-scoped models in Scope.
  Its period choices are week, month, and custom.
- `token_meter/services/goals.py` supports six metrics. Hold exists only for
  Spend and Cost per 1K pushed lines. Settings support all/agent/model scopes.
- Repository drivers require both cost and pushed-code evidence, sort by cost,
  and return at most eight. There is no target-performance filter. Pratik's
  missing Token Meter repository has not been reproduced or diagnosed.
- Expired/manually ended records already appear in Previous goals. Repeating
  goals roll forward and show six earlier periods. Duplication is absent.
- Daily normalized input includes cache reads and writes. Reasoning is a subset
  of output. Dated input plus output can measure tokens without double counting.
- Settings use locked atomic writes and the action-token-protected `/goals`
  endpoint. Native consumers format each metric explicitly.
- Model choices already include a safe runtime ID, but are restricted to recent
  paid usage or saved models and then limited to 15. Filtering that global
  shortlist by agent could leave valid observed models unselectable.
- The Git UI already classifies project evidence as Comparable, Spend only, Git
  only, and No period evidence. It has no arbitrary custom-window control.
- The dashboard uses App for runtime filters and Model for model identity, and
  `compactNumber()` already formats K/M/B. Pratik's Agent selector describes the
  same runtime axis as App elsewhere; it does not mean a subagent role.

## Proposed product decisions

These decisions were approved for implementation by the user's implementation
request and subsequent Continue. They are not additional requirements attributed
to Pratik.

| Question | Proposed behavior |
| --- | --- |
| Agent and model identity | Use the existing dashboard labels App and Model, with All apps and All models defaults. App implements Pratik's Agent scope and uses existing runtime display names. Filter the observed inventory before ranking/limiting. With App=All, model labels include their runtime; selecting one visibly sets its owning app. Identical names in different runtimes remain distinct. Keep internal scope.kind=agent unchanged. |
| Restrictions | Delivery cost fixes both selectors to All with an explanation. Frontier share allows an agent but fixes Model to All because one model is trivially 0% or 100%. |
| Periods | Today, This week, This month, Next 7 days, Next 30 days, Next 90 days, and Custom dates. Forward spans start today and end at start + duration - 1. Save Today and fixed spans as existing custom records; retain week/month for calendar repetition. Show actual dates before saving and on edit. |
| Period consistency | Use the existing 7/30/90 durations, calendar-day helpers, dropdown and date-field styles. Historical filters select past evidence; goal presets select a deadline, so retain explicit Next wording. On reopening a fixed-span record, show Custom dates with its actual saved dates rather than inferring or shifting a preset. |
| Hold | Add one Hold current level option to each metric. Output / $ holds at least; other metrics hold at most. Show At least/At most and the baseline value in its subtitle. Custom retains the existing alternative direction choices. Hold accepts a genuine zero baseline and is unavailable when evidence is absent. |
| Tokens | Label Tokens used. Sum normalized processed input plus output over the period, including cache in input once and reasoning in output once. Usage volume makes no productivity or quality claim. |
| Token targets | Cut 10%, Cut 20%, Hold, and Custom. Custom allows At most for a cap or At least for a milestone such as one billion tokens. Use the existing numeric target input in whole tokens, with a live K/M/B preview using compactNumber(); avoid adding a second unit selector. Store exact integers and show the exact count on inspection. |
| Previous goals | Put Previous goals beside New goal; show Current/Previous within the same workspace using the existing .seg button pattern. Expired records retain Met/Missed/No result; manually ended goals retain Ended. Repeating periods remain in detail. |
| Duplicate | Open an unsaved new form with metric, scope, comparator, absolute target, name, and repeat choice. Week/month refresh to their current calendar window; custom copies its duration starting today. Reset ID, creation/ended state, and repeat anchor, and initially select Custom target to prevent automatic rebasing. Save is explicit. |
| Historical values | Continue deriving history from current evidence/pricing, as documented today; explain recalculation. This round does not promise immutable snapshots or unlimited archive retention. |

Preserve `#goals`, `#efficiency-goals`, goal detail routes, and existing progress
on Spend, Git, and native surfaces. Keep Goals in Efficiency and budgets in Settings.

## UI and architecture consistency contract

- Keep the existing form flow: App + Model, Metric, Period, Target, optional
  Name. Use `.filterSelect`, existing field styles, `.tbtn`, `.seg`, `.chip`,
  `.emptyState`, `.tbl`, and design tokens. Do not create a Goals theme or migrate
  unrelated legacy styling in this round.
- Keep metric labels, units, comparator wording, and evidence/status terminology
  identical on form previews, cards, detail, and existing native consumers.
  Every projected value goes through metric formatting, not `money()`.
  Use App/All apps/By app for visible runtime scope consistently with Sessions,
  Models, Efficiency, and Git; retain internal agent names and scope keys.
- Goal create/edit/duplicate forms own their explicit scope. Parent Efficiency,
  Spend, or Git history filters must not silently change a saved goal or its
  measurement. Existing Set a goal links retain their metric preset behavior.
- Maintain list selection and return focus when opening details, editing,
  cancelling, or saving. Avoid new hash routes/local-storage preferences unless
  a current route cannot represent the behavior. Preserve existing deep links.
- Server projections own totals, targets, status, confidence, and driver basis.
  JavaScript formats and navigates; it never independently measures usage.
- Repository measurements reuse the published Git candidates, labels, ledger,
  availability, and explicit-window query. No rescans, new filesystem discovery,
  ledger writes, or duplicate repository-matching layer from a Goals request.
- Reuse goal settings and evidence/native caches. The additional UI controls do
  not add raw-trace reads, a new scheduler, or a new settings store.

## Feedback coverage

| Pratik's request | Slice | Observable result |
| --- | --- | --- |
| Separate Agent and Model, All defaults | 2 | Separate App/Model selectors using dashboard terminology, runtime-safe identity, valid observed models reachable. |
| Tokens including billion-scale usage | 5 | Whole-token targets and K/M/B display on every existing goal surface. |
| More periods consistent with other pages | 4 | Familiar durations and date controls with explicit deadlines. |
| Missing Token Meter repository | 1 | Investigated membership, same-window totals, visible inclusion/exclusion/truncation reasons. |
| Previous goals, final status, duplicate | 3 | Header access, evidence-aware outcomes, new unsaved duplicate without changing the original. |
| Hold for all metrics | 2 and 5 | One consistent baseline preset for every metric, including zero where valid. |

His positive feedback about setting goals from multiple pages and seeing progress
on those pages is a preservation criterion across all five slices.

## Implementation slices

The user authorized implementation of the reviewed plan, then directed work to
continue. Implement its slices sequentially under that approval; report progress
and seek approval for scope changes. One writer owns the worktree.

### 1. Repository evidence and missing-repository explanation

Files: `token_meter/services/goals.py`, goal Git adapter in `token_meter/app.py`,
`page.html`, focused goal/Git tests. Change `token_meter/services/git_delivery.py`
only if reproduction establishes a shared-service defect.

1. Trace published candidates, canonical repository/worktree identities, dated spend,
   successful-push history, scan freshness, and the goal window. Compare Goals
   with Git over identical dates and evidence revisions.
2. Reproduce with synthetic repository fixtures. Distinguish discovery problems,
   missing cost, missing pushes, stale evidence, and display truncation. Do not
   persist real traces, reporter data, or private paths.
3. Repair the smallest confirmed cause. Add bounded coverage explanations and
   a disclosure in goal detail using Git's existing evidence categories. Retain
   the top-eight preview and report omitted counts. The disclosure explains the
   exact goal window; an Open Git link uses existing navigation and does not
   claim to transfer an unsupported custom range. Use safe labels/opaque IDs.
4. Include all eligible repositories in measurement even when the preview is
   truncated. Explain known exclusions without fabricating undiscovered repos.

Acceptance:

- Eligible repositories meeting the target are not filtered out.
- Goal and Git totals reconcile for the same eligible repositories/window,
  subject to Goals' existing 50-line validity threshold.
- A ninth repository contributes to totals; preview truncation is identified.
- Reuse Comparable, Spend only, Git only, and No period evidence labels, while
  explaining the actual underlying availability. Measured zero pushed lines
  differs from unavailable push history; preserve the Git denominator/cost rules
  rather than inventing a new eligibility filter.
- Missing cost, missing pushes, stale history, and no data are distinguishable;
  added/deleted lines and spend coverage remain visible.
- An unreproduced reporter symptom remains explicitly unverified; do not claim
  a diagnosed fix merely because coverage explanations were added.

### 2. Separate Agent/Model controls and complete Hold options

Files: `page.html`, `token_meter/services/goals.py`, `tests/test_goals.py`,
`specs/GOALS.md`.

1. Replace Scope with App/Model selects using existing field components.
   Translate valid state into existing all/agent/model records; no scope schema
   migration is needed.
2. Reuse the runtime ID already supplied by model choices. Filter the cached
   observed inventory before applying presentation bounds; include token-observed
   models without prices/recent spend and saved choices. If the shortlist omits
   a model, provide a bounded model-name lookup through the existing `/goals`
   read path rather than increasing every response indefinitely. Keep labels
   consistent with runtime/model selectors and disclose shortlist limits.
3. Restore selectors when editing. Agent changes clear incompatible models;
   metric changes visibly enforce restrictions and refresh the preview.
4. Add one Hold option per metric using existing target-option metadata. Show
   its comparator in the subtitle; alternative directions stay in Custom.
   Validate fixed-direction metrics and the new Hold option server-side without
   retroactively rejecting otherwise valid existing custom goals.

Acceptance:

- Defaults, agent filtering, incompatible-model reset, and saved-goal editing
  work. Matching model names across runtimes never combine history.
- A model outside the globally ranked first 15, or with unavailable pricing,
  remains reachable after app filtering/lookup. Selecting from All visibly
  synchronizes the App control; it must not silently contradict the scope.
- Existing records preserve IDs, targets, and repeat anchors on load/save.
  Unknown model evidence remains unavailable.
- Fixed-direction metrics reject wrong comparators, including forged requests.
- Hold appears with a usable baseline. Missing baselines disable automatic Hold
  with an explanation; Custom remains available. Valid zero baselines work.
- Baseline selection distinguishes a measured zero from no observations and does
  not replace a valid zero with a positive fallback. Zero Hold works independently
  of percentage/relative-improvement options that require a positive baseline.
- Focus order, labels, previews, and errors work at 1440 and 1024 pixels.

### 3. Previous goals and duplication

Files: `page.html`, `tests/test_goals.py`, `specs/GOALS.md`; change the goal engine
only if validation requires it.

1. Add Previous goals beside New goal and switch lists inside the current Goals
   workspace using `.seg` buttons with explicit pressed state, an accessible
   empty state, and return to Current. Preserve that selection across detail,
   form Cancel, and Back; after saving a new duplicate, show its Current card.
2. Add Duplicate to previous cards/detail using the existing create/save flow
   and proposed copy semantics. Initialize the draft's saved numeric target
   explicitly: `openGoalForm()` currently preserves it only for edits with an
   ID. Never submit the source ID as an edit or let preview pick a new target.
3. Retain the 50-goal limit and useful limit errors. Avoid new archival storage
   or background settings writes. Explain recurring history and recalculation.

Acceptance:

- The day after an inclusive deadline, a nonrepeating goal moves to Previous
  with its evidence-aware verdict; Ended is distinct from Missed.
- Calendar repeating goals stay Current after rollover and preserve their
  history anchor. Viewing history never writes settings.
- Duplicate then Cancel writes nothing; Save creates new ID/dates and leaves
  the original unchanged. Absolute targets do not silently rebase, even when a
  formerly selected relative option now yields a different number. Week/month
  copies use the current calendar window; custom copies keep their duration.
- An unavailable copied model requires reselection rather than expanding to All.
- Full stores reject new saves cleanly; budgets/unrelated settings survive.

### 4. Additional deadline presets

Files: `page.html`, `tests/test_goals.py`, `specs/GOALS.md`. Change goal-engine
validation only if the existing custom-date contract cannot cover a confirmed
case; no additional period identifiers or settings migration are planned.

1. Add UI shortcuts for Today and Next 7/30/90 days. Materialize dates with
   existing local-calendar helpers, anchored to server-supplied `GOALS.today`,
   then send `period=custom` to the existing preview/save flow. Calendar week
   and month continue to use their current backend rules.
2. Reuse `baseline_window()` for custom records: one preceding day or an
   equal-length preceding span. Retain fallback sources and their current labels.
3. Keep Repeat available only for calendar weeks/months. Custom shortcuts
   produce `repeat=false`, using the existing settings shape and validator.
4. Show the explicit inclusive dates for every preset. Reopening a custom record
   displays Custom dates with saved dates; it never reconstructs a moving preset.

Acceptance:

- Preview, baseline, save, card/detail, and native deadline share inclusive
  dates. Saved fixed spans do not move when the clock advances.
- Month/year boundaries, leap dates, local-calendar/DST transitions, and future
  starts work; JS must avoid UTC-midnight shifts.
- Existing week/month/custom records survive unchanged and normalization stays
  idempotent. Existing invalid-date/period protections apply; fixed shortcuts
  cannot accidentally repeat or change a saved anchor.
- Spend baselines scale to the target span; ratio baselines aggregate whole-span
  numerators/denominators rather than averaging daily ratios.

### 5. Tokens across browser and existing native consumers

Files: `token_meter/services/goals.py`, `token_meter/services/goal_coaching.py`,
`page.html`, `menubar/TokenMeterMenuBar.swift`, `menubar/token_meter_tray.py`,
`tests/test_goals.py`, applicable native tests, `specs/GOALS.md`, `README.md`.
Change daily aggregation only if existing coverage fields prove insufficient.

1. Add explicit token collection/finishing; avoid unknown-metric fallthrough to
   Frontier share. Use dated input plus output, token-coverage flags, and
   undated-execution checks.
2. Count executions with available tokens and unavailable pricing. Retain
   estimated provenance and partial totals; missing evidence is never zero.
   Use input-and-output coverage, not `token_covered_executions` alone: that
   existing counter covers output only. Do not exclude a whole session's usable
   daily evidence merely because another execution has a coverage gap.
3. Scale baseline and pace for cumulative Tokens as for Spend. Project only
   cumulative metrics; retain existing ratio measurement. Add minimal metric
   metadata for cumulative behavior so the two metrics share baseline/pacing
   rules. Keep all existing ratio/status paths unchanged.
4. Validate exact integer targets above one billion through the existing
   JSON-safe token limit. Reject fractions, negative/nonfinite/boolean/unsafe
   custom targets. Keep observed sums integer-valued; round relative/normalized
   preset targets to whole tokens in one documented backend rule before preview
   or save. Reuse the existing numeric input and `compactNumber()` display, plus
   a formatted exact-count hint. K/M/B display never rounds the saved count.
5. Add token-based driver shares, trends, and contributor ranking. Retain Spend
   as guardrail. Introduce an explicit driver/contributor basis so token detail
   says share of tokens, while existing spend breakdowns/coaching keep their
   original cost shares. Token drivers must also include unpriced executions.
   Reuse the existing no-tip coaching state; no new coaching rules are required.
6. Extend Swift/Linux formatting so tokens use K/M/B rather than money or
   percent. Keep summaries bounded and cached. Inspect Windows consumers for
   compatibility; obtain Windows evidence before making Windows claims.
7. Route card pace, progress descriptions, projected detail tiles, baseline and
   contributor values through `goalValue()`/native metric formatters. Several
   current projection labels call `money()` directly and would mislabel Tokens.

Acceptance:

- Scope/window totals match existing normalized tokens; cache/reasoning count
  once, including cache-heavy and reasoning-heavy cases.
- Token goals work without prices and disclose incomplete/estimated data.
  Confirmed zero is distinct from absent evidence.
- Billion/multi-billion targets round-trip exactly; compact previews preserve
  counts; targets above the JSON-safe bound fail validation. There is one input,
  its integer value is visible, and compact rounding cannot silently alter it.
- Pacing, baselines, trends, contributors, duplication, and final verdicts share
  one definition. Known cumulative usage above an At most cap can be Missed
  before deadline, as Spend is; incomplete final evidence remains No result.
- Browser/macOS/Linux consumers format correctly. Live claims require target-host
  evidence. Native polling adds no raw-trace reads or duplicate measurement.
- Token model/agent shares, contributor weights, and total use the same covered
  population. Existing cost-based coaching inputs remain cost-based; unpriced
  token evidence does not disappear from the explanation of a token goal.

## Design review findings and disposition

This review inspected the plan against feedback and source behavior; it did not
run tests, reproduce the reporter's data, or certify a product change.

| Finding | Source evidence | Disposition in this plan |
| --- | --- | --- |
| New period identifiers would add validation/migration work for behavior already supported by custom dates. | `period_window()`, `baseline_window()`, and `_valid_period()` already support bounded inclusive custom windows. | Fixed shortcuts serialize to custom; calendar-repeat records stay unchanged. |
| Another Hold comparator and token-unit selector would make the simple form heavier. | `TARGET_OPTIONS` supports comparator metadata; Custom already has direction/input fields; `compactNumber()` handles K/M/B. | One Hold preset, alternative direction through Custom, one numeric token input with preview. |
| Agent wording would conflict with App filters and subagent roles. | Sessions filters and Models/Efficiency/Git tables already call the runtime App. | App/Model split; preserve internal agent scope and explain its mapping to Pratik's request. |
| A globally limited, spend-only model list can hide the requested choice or an unpriced token model. | `_model_choices()` filters recent spend before taking 15; it already supplies runtime identity. | Filter observed inventory first, reuse identity, allow bounded lookup, include unpriced/pinned choices. |
| A matching arbitrary-window Git link is not supported; availability also differs from positive lines. | Git range dropdown lacks Custom; query rows report measured push coverage separately from changed lines. | Show same-window coverage in goal detail, reuse Git categories and rules, retain ordinary Open Git navigation. |
| Duplication through the current form could lose the copied absolute target. | `openGoalForm()` populates saved numeric state only when preset.id exists. | Explicit duplicate draft with saved number, no source ID, and Custom target initially. |
| Generic token support could omit evidence or format it as money. | Daily token coverage counts output only; drivers skip unpriced sessions; cards/detail use money() for projections. | Require I/O coverage, token-based covered populations, separate driver basis, and metric-aware formatting on every surface. |

All six feedback items have an implementation slice and observable acceptance
criteria. The source implementation covers those slices; the reporter's missing
repository diagnosis and acceptance verification remain unverified.

## Validation and workflow

Implementation is not eligible for the low-risk fast path. It changes behavior,
record validation, and browser/native consumers. Risks include persistence,
shared helpers, privacy boundaries, native menus, and cross-platform behavior.
The combined change requires one independent tester and two reviewers under
project policy: requirements/regressions and privacy/settings/runtime/platform.

The user's standing preference reserves test execution and commits to the user.
This plan does not override it. Add focused tests matching neighboring style;
reuse the existing day/session/goal fixtures rather than adding new scaffolding.
Provide these checks for user execution or separately authorized verification:

- Focused Goals tests; Git regressions when the shared service changes.
- Embedded-JS parsing, design-system contract, and browser checks at 1440/1024
  pixels: empty/populated/error/detail/history/duplicate states, keyboard use,
  long labels, and preserved routes. Snapshot diff is needed only for a shared
  component or stylesheet migration; avoid broad styling changes.
- Relevant Python syntax and full unit/contract suite for final integration.
- Swift compile, deterministic smoke, and live menu-bar check for native changes.
  Obtain Linux evidence separately and state Windows limitations.
- After installation is authorized: installer, `/health`, `/menubar`, both
  LaunchAgent states, automatic start, and source/runtime manifest parity.
- Scoped diff/privacy inspection and `git diff --check`. Settings tests cover
  protected actions, atomic writes, repeat/read/write migration, comparator
  validation, and isolation from budgets.

Bind independent results to a user-created immutable commit. Any later tracked
change invalidates passing evidence; rerun required gates against the new head.
Specialist transfers use the task-envelope/result
shape in `.agents/workflow/handoff.schema.json`. Record every failed/unrun gate.

## Delivery and scope

- Recheck branch/worktree/upstream before implementation. Preserve current Goals
  and unrelated edits; do not change branches, merge upstream, or update pricing
  incidentally. Resolve any required integration work as an explicit slice.
- Preserve local-only operation, measurement/coaching boundaries, opaque keys,
  sanitized labels, and bounded projections. Scope excludes business objectives,
  task-quality inference, new navigation, MCP goal writes, raw session content,
  and hosted services.
- Update Goals docs per slice and keep README concise. Change Architecture only
  for changed boundaries. Runtime files remain manifest-covered.
- Prepare an accurate PR description after implementation, with final behavior
  and exact validation status. GitHub editing, Slack, commit, push, merge, release,
  and installation require their applicable authorization.
- Final handoff includes changed files, acceptance coverage, observed/inferred
  repository diagnosis, exact checks, runtime state, review dispositions, and
  every unverified item.

## Progress

- [x] Read feedback and inspect PR/local head.
- [x] Map implementation/consumers and draft decisions/acceptance criteria.
- [x] Review all feedback for architecture reuse, UI consistency, and unnecessary
  work; incorporate the findings into this revised plan.
- [x] Obtain design/implementation approval and subsequent direction to continue.
- [x] Implement slices 1 through 5 in source with progress updates.
- [ ] Complete user-owned validation and independent gates.
- [ ] Prepare delivery wording and obtain external-action authority.

## Implementation handoff

- Changed source: `token_meter/services/goals.py`, goal adapters/routes/cache in
  `token_meter/app.py`, `page.html`, and both existing Swift/Linux goal formatters.
  Updated `tests/test_goals.py`, `specs/GOALS.md`, and README. Existing runtime
  manifest coverage includes every changed runtime file; no new runtime file.
- Repository detail explains every published project's evidence category and
  top-eight omission. Queries use the same watcher-owned candidates as Git;
  cached results refresh stale status without rescanning. No reporter-specific
  root cause has been established.
- App/Model controls use bounded observed-model lookup. Presets add Hold,
  preserving real zero baselines. Custom-date shortcuts, history selection,
  unsaved duplication, and whole-token goals use the existing settings shape.
- Token totals preserve normalized cache/reasoning accounting, I/O coverage,
  unpriced usage, cumulative pacing, and metric-specific driver/contributor
  labels. Compact previews do not change the saved integer target.
- Static evidence: Python source/tests parsed with `ast.parse`; embedded JS
  parsed with `new Function`; Swift compiled to a temporary binary; whitespace
  inspection passed. These checks did not execute the product or unit tests.
- Pending: focused/full unit tests, design-system contract, 1440/1024 browser
  checks, native smoke/live checks, Linux/Windows host evidence, installation and
  health/native/runtime parity, and immutable-commit independent reviews.
- Delivery state: local and uncommitted. No installation, push, GitHub edit,
  Slack write, merge, or release performed.
