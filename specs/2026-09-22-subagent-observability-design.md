# Claude and Codex Subagent Observability

## Status

The in-chat design and this written record were approved on 2026-09-22. A
project-filter and shared-Codex-session identity amendment was approved on
2026-09-23 after live Luna-3 and Token Meter traces exposed gaps in the first
implementation. Implementation is authorized on the isolated
`codex/subagent-observability` branch. Commits, pushes, and pull requests remain
separately gated.

On 2026-09-23, a second approved amendment moved cross-session analysis from
Sessions -> All to a dedicated Sessions -> Subagents subroute. It also made
provider-reported roles the primary agent identity, added an explicit
`Incomplete` activity state for stale nonterminal traces, separated that state
from deterministic `Needs attention` signals, and replaced ambiguous Sessions
coverage abbreviations with exact evidence counts.

## Problem

A Claude or Codex session can start several child agents. Those agents may run
in parallel, nest other agents, or continue consuming tokens after their parent
appears quiet. Token Meter currently exposes some of this work only as a
coordination share, while provider-specific trace handling differs:

- Claude groups a main trace and its nested `subagents` traces into one logical
  session and deduplicates repeated logical messages.
- Codex discovers spawned rollouts as distinct physical traces, retains direct
  parent metadata, and removes only verified copied usage prefixes before
  accounting.

The dashboard does not turn either representation into a parent-to-child view.
A user therefore cannot start at a main session, see which agents contributed
its usage, compare their costs, or identify the child that deserves attention.
Cross-session views also cannot show whether a custom agent pattern is becoming
cheaper or more expensive over time.

## Goals

- Let a user open a Claude or Codex session and inspect its observable child
  agents as a hierarchy.
- Show each child's measured tokens, estimated cost, share of group spend,
  timing, activity, model, and evidence coverage without double counting.
- Surface transparent signals that help a user investigate possible runaway
  spend without claiming that Token Meter proved an agent was stuck.
- Add a dedicated Sessions -> Subagents route so users can filter child-agent
  activity and compare runtimes, models, depths, and safely available roles.
- Preserve today's global, session, daily, model, budget, menu-bar, and MCP
  accounting totals.
- Keep all parsing local, read-only, dependency-free, and within Token Meter's
  existing privacy boundary.

## Non-Goals

- Stop, pause, kill, message, or change a provider agent.
- Add a new top-level dashboard route.
- Expose prompts, responses, reasoning, tool arguments, tool results, raw trace
  rows, local paths, or provider configuration.
- Infer a Claude custom-agent name from prompt text or an agent tool argument.
- Treat every Codex fork, side chat, or internal review trace as a user-spawned
  subagent.
- Replace provider billing, subscription counters, or quota windows with local
  API-equivalent cost estimates.
- Define task-complexity classes or claim that a high-cost child is wasteful.
- Add subagent support for Cursor, OpenCode, Kiro, Pi, or Hermes in this change.

## Alternatives Considered

### Promote every child to a top-level session

This would give Claude and Codex the same visible source shape. It would also
change Claude discovery, deletion, cache invalidation, current-session cards,
and aggregate accounting. A nested Claude trace can repeat parent messages, so
naive promotion would reintroduce double counting. This approach is rejected.

### Infer relationships only in the browser

This would minimize server changes, but the browser does not have Claude trace
ownership or Codex physical lineage evidence. It could not allocate child cost
correctly, resolve cycles conservatively, or distinguish missing cost from a
measured zero. This approach is rejected.

### Add an adapter-owned relationship overlay

This is the selected approach. Runtime adapters retain responsibility for
provider identities, corrections, and child components. A runtime-neutral
domain layer accepts content-free agent records, resolves safe groups, and
produces bounded projections for the selected session and Sessions ->
Subagents.
Existing sessions and totals remain authoritative.

## Terminology and Identity

An **agent group** is one root session plus every safely resolved descendant.
It is a dashboard relationship, not a replacement billing session.

An **agent record** is a content-free component with:

- a public opaque agent ID;
- a public opaque parent ID when safely resolved;
- runtime and client;
- kind: `root`, `spawned`, or `internal`;
- depth when reported or safely derived;
- bounded display label and stable role only when the provider reports them as
  structural metadata;
- model/provider;
- start, end, last activity, and activity state inputs;
- input, output, cache, reasoning, and total-token evidence;
- estimated cost and availability;
- execution, attempt, retry, failed-attempt, and tool-call counts when
  available.

Opaque IDs must not encode trace paths. Raw physical IDs stay inside adapters
unless they are already the established public session ID. Claude child IDs
are derived with a namespaced hash over the owning public session identity and
private component identity. Codex agent IDs are likewise derived with a
versioned namespaced hash over the private physical trace identity. Public
session identity remains a separate optional navigation field: a child is
navigable only when its public session ID uniquely identifies that physical
trace.

`agent_path`, trace locators, prompts, task descriptions, tool inputs, and
arbitrary provider strings are never part of an agent record.

## Claude Attribution

Claude remains one discovered session. The adapter extends its grouped loader
to retain private source ownership while constructing the same canonical
logical-message stream used for existing totals.

Trace paths are ordered by structural depth: main trace first, then direct
children, then deeper descendants. For a message with a provider message ID,
the shallowest first owner receives the canonical message. Later copies or
updates can improve the canonical usage record but cannot create a second
charge or change ownership. ID-less records remain distinct, matching current
fail-safe accounting behavior.

The main component receives canonical messages owned by the main trace. Each
child receives only canonical messages first owned by that child's trace. The
sum of component token and cost evidence must reconcile with the existing
grouped session summary. If attribution cannot preserve that invariant, the
adapter omits the breakdown and returns an explicit coverage reason; it does
not publish a plausible-looking partial tree.

The nested directory structure supplies parent and depth. `agentId` may support
private component identity, but it is not treated as a reusable role or a
human-readable name. Claude rows that do not contain safe stable role metadata
are labeled `Agent 1`, `Agent 2`, and so on within the selected session. Those
labels are presentation ordinals, not persisted identity.

Claude child cost follows the same model resolution, effective-date pricing,
billing-dimension checks, and estimate labels as the owning session. A child
with unsupported billing evidence has unavailable cost even when its token
counts are measured.

## Codex Relationships

Codex keeps each physical rollout as its existing selectable session. The
adapter extends bounded `session_meta` parsing to classify explicit subagent
spawns and retain the following private structural fields when present:

- direct `parent_thread_id`;
- `source.subagent.thread_spawn.parent_thread_id`;
- reported depth;
- bounded agent nickname and role;
- whether the relationship is an explicit spawn or an internal child.

`agent_path`, base instructions, history, prompts, and source content are
discarded. Agent nickname and role are bounded and sanitized before browser
projection. They are excluded from MCP and telemetry unless those interfaces
receive a separate reviewed schema change.

Relationship resolution is conservative:

- a unique, cycle-free direct parent creates an edge;
- duplicate records for one physical parent may create one parent node only
  when their content-free identity metadata agrees; a deterministic canonical
  record supplies its metrics while accounting lineage remains fail-closed;
- explicit `thread_spawn` metadata creates a `spawned` child;
- a supported internal child marker may create an `internal` child;
- fork-only lineage remains accounting evidence and does not by itself create
  a visible subagent;
- missing, ambiguous, self-referential, or cyclic parentage creates no edge.

Existing inherited-prefix correction runs before child metrics are projected.
The agent overlay consumes one deterministic summary per physical agent,
including physical children that share a public desktop session ID. This
agent-only canonicalization does not alter the canonical source set used by
global session, cost, token, model, daily, budget, menu-bar, or MCP accounting.
The group total is the sum of the root and resolved descendants' corrected
agent summaries. No runtime-neutral code reopens Codex traces or performs a
second usage correction.

Opening a Codex child session keeps that session's existing cost semantics and
adds a breadcrumb to the root plus safely resolved siblings and descendants.
Opening a row in the tree navigates only when the child has a unique established
session route. Children that share their root's public session ID remain visible
inline and are not presented as misleading duplicate navigation targets.

## Shared Agent Group Contract

The domain layer receives already-corrected records and produces:

```json
{
  "root_session_id": "opaque-session-id",
  "selected_agent_id": "opaque-agent-id",
  "coverage": {
    "relationships": "complete",
    "tokens": "complete",
    "cost": "estimated"
  },
  "totals": {
    "agents": 3,
    "tokens": 125000,
    "cost": 4.82,
    "cost_available": true
  },
  "agents": [],
  "attention": []
}
```

The exact public projection is allowlisted. Numeric zero is emitted only for a
measured zero. When any included component lacks cost coverage, known spend and
coverage are kept distinct; missing cost is never folded into a complete total.
Existing `cost_approx` and pricing-basis labels remain authoritative.

The group contract is bounded to 100 visible agent records. If a deeper or
wider tree exceeds the limit, exact totals still cover the complete resolved
group, visible rows are deterministically truncated, and the response reports
the hidden record count. Cycles and unresolved relationships are excluded from
the group rather than repaired heuristically.

## Needs-Attention Signals

Token Meter cannot observe an agent's intent, so it does not label an agent
`runaway`. It emits a `Needs attention` level with one or more plain reasons.
Every reason names the evidence and threshold that triggered it.

Initial signals are:

- **Cap exceeded:** the selected browser's saved session cap is available and
  either the group or one child has exceeded it.
- **Active cost concentration:** a currently active child has at least $1 of
  covered estimated spend and accounts for at least 50% of covered group
  spend.
- **Peer cost outlier:** at least four comparable children exist and one child
  has at least $0.50 of covered spend and costs at least three times the peer
  median.
- **Retry pressure:** supported execution evidence reports at least three
  retries or failed attempts among the five latest executions.
- **Observed live growth:** while the panel remains open, two consecutive
  refreshes show an active child's covered estimated cost increasing and the
  observed increase reaches $0.25. This signal is ephemeral and resets on page
  reload.

These thresholds are deterministic product defaults, not statistical proof of
waste. Signals that depend on cost are disabled when cost is unavailable or
partial. Signals do not trigger notifications in the first release; the
existing session-budget notification remains unchanged.

## Selected-Session Experience

The existing selected Sessions route gains an `Agent activity` module after the
run overview. It appears only when the selected Claude or Codex session has an
observable child or is itself a resolved child.

The module contains:

- root breadcrumb and selected-agent context;
- group cost, child-agent cost, tokens, agent count, and evidence coverage;
- a depth-indented tree with status, model, tokens, cost, group share, elapsed
  time, and `Needs attention` badges;
- an explanation panel for the selected signal;
- Codex child navigation and Claude inline component expansion.

The root session's existing headline cost does not silently change. Claude's
headline remains the existing grouped total; the module explains its main and
child components. Codex's headline remains the selected physical session; the
module separately labels the agent-group rollup.

Keyboard navigation follows the existing session controls. Rows are buttons or
links with explicit accessible names, depth is not communicated by indentation
alone, and badges expose their complete reason in text. The module must work at
the supported wide-desktop and 1024-pixel laptop widths.

## Sessions -> Subagents Explorer

Sessions -> Subagents is a dedicated third Sessions subroute sourced from
complete cached session summaries rather than the bounded All Sessions table.
It contains:

- parent sessions with agents;
- observed agent runs;
- covered estimated agent cost and coverage;
- agent share of covered session spend;
- input, output, cache, and total tokens;
- median and 95th-percentile cost per agent when cost coverage is sufficient;
- output per dollar when both output and cost are available;
- count of agents with needs-attention signals.

The initial cohort table groups by runtime, model, and depth. A role grouping is
available only for a bounded provider-reported stable role. Claude anonymous
agent instances are not grouped into invented prompt identities. Internal
Codex helpers are separated from user-spawned agents so they do not distort
custom-agent comparisons.

The page filters a bounded, content-free child inventory by role or nickname,
runtime, project, model, lifecycle status, attention signal, and activity
window. It also retains exact precomputed runtime/project/window cohorts for
usage-pattern comparisons. Project membership is taken from the resolved root
session so a child remains attached to the project that initiated its agent
group. The server precomputes exact, bounded project/runtime/window scopes from
complete agent groups; the browser never recalculates statistics from the
60-row visible session preview. Provider-reported roles are
the primary identity when present; nicknames are secondary, then fallback.
`Incomplete` means a stale nonterminal provider trace, not an attention signal.
When the inventory is truncated, visible rows remain filterable but exact
filtered totals are withheld. Statistics retain runtime scoping for identical
model names, and exact coverage counts replace ambiguous suffixes.

## Data Flow and Components

1. Claude and Codex adapters parse private provider structure and produce
   corrected content-free agent components.
2. Session summarization caches those components with the same revision that
   invalidates the owning summary.
3. A runtime-neutral agent domain helper validates trees, bounds output,
   calculates complete-scope totals, cohorts, and evidence-driven signals.
4. Application composition keeps accounting sources unchanged, separately
   selects one agent-summary source per physical Codex agent, joins public
   session navigation only when unique, and attaches the selected group plus
   complete-scope aggregate statistics.
5. Public projections positively allowlist the browser fields. MCP, native,
   and telemetry payloads remain unchanged.
6. `page.html` renders the selected-session module and Sessions -> Subagents
   statistics, with the browser-only cap and live-growth signals added to the
   server-provided structural signals.

Expected implementation areas are `token_meter/runtimes/claude.py`,
`token_meter/runtimes/codex.py`, a focused runtime-neutral domain module,
`token_meter/app.py`, explicit public projections, `page.html`, and their
tests. Imported runtime files remain covered by `runtime-manifest.txt` through
the existing `token_meter/` tree entry.

## Failure and Coverage Semantics

- A missing or unreadable child trace keeps the owning session usable and
  marks relationship coverage partial.
- Claude component totals that fail reconciliation are omitted with a bounded
  warning; existing session totals remain authoritative.
- A missing, conflicting, or cyclic Codex parent leaves the child as a
  standalone session and excludes it from agent-group rollups. Duplicate
  physical parent records with matching structural identity collapse only in
  the agent overlay; they remain ambiguous for accounting lineage.
- Unsupported pricing produces unavailable child cost, not `$0.00`.
- Corrupt provider rows preserve safe evidence already parsed and mark the
  affected component partial.
- Unknown agent roles remain unnamed; no prompt-derived fallback is allowed.
- One adapter's failure cannot suppress the other runtime's agent statistics.
- Public errors and warnings contain no trace path, arbitrary exception text,
  or provider content.

## Compatibility

- Existing session IDs, routes, deep links, deletion behavior, budgets, and
  stored browser preferences remain valid.
- Existing global totals do not change.
- Claude remains one top-level session per canonical grouped source.
- Codex child sessions remain independently selectable and counted once.
- Menu-bar, MCP, telemetry, and native payload schemas do not change.
- The dashboard order remains Sessions -> Spend -> Models -> Efficiency -> Git
  -> Learn -> Tools -> Settings.

## Test Strategy

Implementation follows red-green-refactor. Focused fixtures must prove:

1. Claude main and nested traces allocate canonical messages exactly once.
2. Repeated parent messages in a Claude child do not increase child or group
   cost, while unique child work is attributed to that child.
3. Nested Claude children receive deterministic opaque IDs and correct depth
   without projecting paths or prompt/tool content.
4. Claude component tokens and covered cost reconcile exactly with the existing
   grouped session summary; reconciliation failure hides the breakdown.
5. Codex explicit spawned children link to unique direct parents, including a
   structurally consistent duplicated physical parent; fork-only, missing,
   conflicting, self-parent, and cyclic cases remain standalone.
6. Codex children that share a public session ID retain distinct hashed agent
   IDs, are counted once per physical trace, and do not become duplicate
   navigation targets.
7. Codex agent nickname, role, and depth are bounded; `agent_path`, base
   instructions, and provider content never reach public projections.
8. Codex child metrics use the already corrected accounting stream and do not
   restore inherited usage.
9. Unavailable child cost remains unavailable through group totals,
   statistics, UI formatting, and attention-signal calculation.
10. Each attention reason fires only at its documented boundary and remains off
   without sufficient evidence.
11. Complete-scope cohort statistics do not depend on the visible session-row
    limit and retain project/runtime/model scoping. Project-scoped Luna-3 and
    Token Meter fixtures return their observed agents; text search remains
    explicitly unavailable.
12. Existing session, daily, model, budget, menu-bar, MCP, telemetry, and
    deletion contracts remain unchanged.
13. The dashboard exposes usable keyboard and text equivalents and renders at
    wide-desktop and 1024-pixel laptop widths.

Focused adapter, domain, application, privacy, and UI-contract tests run before
the complete suite. Final verification also requires Python compilation,
embedded JavaScript parsing, `git diff --check`, installation, `/health`,
`/menubar`, both LaunchAgent states, staged-runtime parity, and browser checks
at both supported widths.

Because this change affects provider parsing, privacy boundaries, shared domain
logic, the browser, and installed runtime behavior, the completed immutable
head requires one independent tester and two independent project reviewers
with distinct requirements/correctness and privacy/consumer lenses.

## Acceptance Criteria

- Opening a Claude or Codex parent with observable children shows a reconciled
  hierarchy and per-child token, cost, model, timing, activity, and coverage.
- Opening a resolved Codex child shows its root context and can navigate among
  the established session routes.
- Claude child components sum to the existing grouped session totals without
  promoting children to top-level sessions.
- Codex group totals sum corrected root and descendant sessions without
  changing global accounting.
- Needs-attention badges explain their evidence and never present an inferred
  loop as fact.
- Sessions -> Subagents shows complete-scope statistics and useful cohorts
  for supported project/runtime/time filters without inventing Claude
  custom-agent names or deriving aggregates from visible rows.
- Unavailable evidence never becomes zero, and estimates stay labeled.
- No prohibited content, local path, private physical identity, or raw trace
  structure appears in public, MCP, native, or telemetry output.
- Existing routes, budgets, totals, deep links, deletion, and stored
  preferences remain compatible.
- Required source, browser, installation, runtime-parity, tester, and reviewer
  gates pass against the same immutable head.
