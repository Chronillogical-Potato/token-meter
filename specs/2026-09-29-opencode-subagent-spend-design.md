# OpenCode Subagent Spend Attribution

## Status

Proposed. This document is the design record and implementation contract for
adding OpenCode child-agent spend to Token Meter. It amends the non-goal in
`specs/2026-09-22-subagent-observability-design.md` that excluded OpenCode from
subagent support, and records the accounting decision that differs from the
Claude and Codex treatment.

Commits, pushes, and pull requests remain separately gated. Per
`.agents/workflow/review-policy.yaml` this change is **high-risk** because it
crosses `provider-parsing` and `pricing-semantics`; the completed immutable head
requires one independent tester and two independent project reviewers with
distinct requirements/correctness and privacy/consumer lenses.

## Problem

Token Meter excludes every OpenCode child session from discovery. The adapter
query at `token_meter/runtimes/opencode.py` selects
`FROM session s WHERE s.parent_id IS NULL`, so sessions carrying a `parent_id`
never become sources and therefore never reach any summary, aggregate, total,
budget, or menu-bar figure.

Measured on the development machine against the local OpenCode database:

| Measure | Root sessions | Child sessions |
|---|---|---|
| Sessions | 284 | 391 |
| Messages | 19,197 | 9,611 |
| Reported cost | $58.01 | $22.94 |
| Input tokens | 52,705,459 | 36,737,132 |

Roughly a third of all OpenCode token volume is absent from every reported
total. No coverage flag marks the gap, because the rows are never selected. This
conflicts with the standing rule in `specs/AGENTS.md` that unavailable evidence
must not become a measured zero; here unavailable evidence becomes an
unmeasured absence inside totals that still render as complete.

Separately, `canonical_agent_sources` in `token_meter/app.py` admits only the
`claude` and `codex` providers, so OpenCode cannot contribute child-agent
records even if the adapter produced them.

## Why OpenCode Differs From Claude And Codex

The existing implementation groups or corrects child work because the provider's
parent figure already contains it. OpenCode is the opposite, and this was
verified against real data rather than assumed.

- **Child cost is additive.** Parent cost is lower than the combined cost of its
  children in every measured group. The largest observed group reports $1.2799
  for the parent against $7.5174 across six children.
- **Message sets are disjoint.** A query for child message ids present in the
  parent session returns zero rows. There is no repeated logical message and so
  nothing to deduplicate.
- **Nesting is shallow.** A recursive grandchild query returned zero rows on
  the measured data, but the schema allows deeper chains, so the adapter
  resolves each session's root ancestor and depth with a bounded walk
  (`MAX_SESSION_ANCESTRY`, cycle-safe) instead of assuming depth 1.
- **No orphaned children.** Every non-null `parent_id` resolves to a live
  session.
- **No archived children** on the measured data. Archive semantics apply to a
  whole family: an archived session and every descendant are excluded together.

Because the parent does not include child spend, the Claude and Codex treatment
of excluding children from top-level discovery would leave OpenCode
accounting incorrect. OpenCode children are therefore restored as independent,
individually counted sessions.

## Decisions

1. **Children are counted in totals.** OpenCode child sessions are discovered
   and aggregated exactly like any other session, and their cost raises global
   totals. Totals must rise by the true child spend rather than stay at the
   current undercount.
2. **Children are filtered from the default session list.** 391 extra rows would
   swamp Sessions -> All. Child sessions are counted in totals and remain
   individually addressable, but are not listed by default.
3. **Children render under the parent card.** The All sessions parent row gains
   a child subsection listing its child runs inline, so the relationship stays
   legible without inflating the list.
4. **Free-tier cost is a measured zero.** 121 child sessions report tokens with
   `cost=0`, all on the `opencode/space-bunny-free` free tier. That zero is the
   real price, not missing evidence, and must never be converted to unavailable
   cost or back-filled with catalog pricing.
5. **One summary source per physical child.** Summaries are selected without
   changing accounting sources.

## Non-Goals

- Adding subagent support for Cursor, Kiro, Pi, or Hermes.
- Inferring an agent role from prompt text, message content, or a tool argument.
- Repairing a cycle or an over-deep chain heuristically; such a family is left
  unresolved and its sessions stay individually counted.
- Treating `message.data.parentID` as a session relationship. That field is a
  message-level reference: 26,901 messages carry it and none match a session id.
  Parent linkage comes only from `session.parent_id`.
- Replacing provider billing or quota windows with local estimates.
- Exposing `parent_id`, `directory`, `slug`, `path`, or any prompt, tool, or
  part content in a public projection.
- Changing the Claude, Codex, or Kiro agent-record paths.

## Identity And Attribution

Each OpenCode child session yields one `spawned` agent record. The public agent
ID is a versioned namespaced SHA-256 digest over the private physical session
id, mirroring `_opaque_agent_id` in `token_meter/runtimes/codex.py`. Parent
agent identity uses the same construction over the parent session id, so neither
the private session id nor the database path is exposed.

The child summary row carries the child session's own `cost`, `tokens_input`,
`tokens_output`, `tokens_reasoning`, `tokens_cache_read`, `tokens_cache_write`,
`time_created`, and `time_updated` values. Cost availability reuses the existing
`session_cost_available` rule, which treats a finite non-negative number,
including `0.0`, as available. That rule is correct for the free tier and must
not be tightened.

`role` is the bounded `session.agent` value, truncated to the domain limit of 64
characters. It is provider-reported structural metadata, never derived from
content. Where it is empty the record carries no role and the browser shows its
existing unreported-role treatment.

`kind` is `spawned` and `depth` is the resolved nesting depth (1 for a direct
child, 2 for a grandchild). A child whose parent session record is missing
produces no edge and remains a standalone counted session, which is the
conservative outcome the existing domain layer already implements.

`project` for a child resolves from the root ancestor's directory, not the
immediate parent's directory and not the child's own `agent` column. The adapter uses `agent` only as a last-resort project
fallback, and letting a child fall back to a project literally named
`gsd-planner` would be a defect. On the current data every session has a
non-empty `directory`, so the fallback does not trigger.

## Data Flow

1. The adapter query selects child sessions alongside roots, additionally
   selecting `parent_id` and `agent`. A lightweight ancestry query over every
   session (archived included) resolves each session's root, depth, and root
   directory. A session is excluded when it or any ancestor is archived, so an
   archived root removes its whole family from discovery and totals, matching
   pre-change behavior.
2. `discover` and `discover_legacy` emit one source per session, roots and
   children alike, carrying the parent reference privately.
3. `canonical_aggregation_sources` keeps each OpenCode session distinct, so
   cross-session aggregation consumes the child summaries.
4. The adapter attaches one `_agent_records` entry per child to its summary row.
5. `canonical_agent_sources` gains an OpenCode branch that selects exactly one
   summary per physical child, without altering accounting sources.
6. The existing runtime-neutral domain layer builds groups, totals, cohorts, and
   attention signals unchanged. The only domain addition is the runtime-neutral
   current-session fold described below.
7. The public projection adds only the bounded child fields the subsection
   renders: `is_child_session`, `child_agent_role`, `child_depth`, and
   `root_session_id` (present only when the root resolved; the root is itself a
   discovered, listed session). The raw `parent_id` is never published, so an
   unlisted or missing parent reference never leaves the server.
8. `page.html` filters child rows from the default list and renders a child
   subsection inside the parent card.

## Failure And Coverage Semantics

- A child whose parent is absent produces no agent edge and stays a counted
  standalone session.
- An unattributed child is disclosed, not silent. A child whose parent session
  record is missing from the local database is counted in global totals but has
  no group, so the Subagents rollup would otherwise look
  complete while excluding it. The loader reports the count and covered cost of
  those records, the browser states them on the Subagents page, and the All
  sessions row-count line separates runs shown under a parent card from runs
  with no parent session. Missing price on such a record stays unavailable and
  does not become a measured zero.
- A free-tier child reports a measured `$0.00` with cost available; it is never
  presented as unpriced.
- A child with unparseable token or cost columns keeps the session usable and
  reports cost unavailable rather than zero.
- `space-bunny-free` is absent from the built-in catalog. No fallback rate is
  invented for it.
- One adapter failure cannot suppress Claude, Codex, or Kiro agent statistics.
- Public errors and warnings contain no session id, path, or provider content.

## Additive Cost Assumption

Session totals assume a parent's `session.cost` excludes its children, so a
family's spend is the parent's reported cost plus each child's reported cost.
Token Meter never subtracts child cost from a parent: a parent may legitimately
report more than its remaining message-level cost (for example after reverted
messages), so that gap is not evidence of included child spend, and no OpenCode
build is known to report inclusive parent costs. Tests pin both the additive
total and a parent whose reported cost exceeds its own messages staying
unchanged. If OpenCode ever reports inclusive parent costs, this assumption must
be revisited with source evidence.

## Current Sessions And Session Caps

A child run is part of its root session's live work, not a separate current
session. `current_session_summaries` folds each child with a resolved root into
the root's row: cost, tokens, and executions are summed, and the newest child
activity becomes the row's activity, so a
root whose own messages are idle still appears current while a descendant
works. A child whose root row is absent (unresolved family, or a root with no
executions) stays its own row so its spend is never hidden. The same rule
applies to the watcher's live source, menu-bar recent sessions, implicit MCP
run selection, and the `/session` live flag. MCP `sessions` reports a root as
`current` while any of its child runs is current; each child keeps its own
state.

Folded cost and tokens sum only members whose metric is measured. The folded
metric is available when any member's is, and `cost_partial` marks a folded
cost that omits an unavailable member, so the card shows it as a lower bound
rather than a complete figure or a measured zero.

A child run has no separate cap. `session_budget_snapshot` reports the root's
cap for every family member, and its spend is the live session's spend plus the
cached spend of every other measured family member. Measured members count even
when the live session's own cost is unavailable, and `cost_partial` marks spend
that omits an unavailable member. Setting a cap from a child, through
HTTP or MCP, writes the root's override.

## Compatibility

Existing session ids, routes, deep links, budgets, and stored browser
preferences remain valid. Menu-bar, MCP, and telemetry payload schemas do not
change. Global OpenCode totals and session counts intentionally change, by
exactly the previously unmeasured child spend and child session count. The
dashboard order is unchanged.

## Test Strategy

Red-green-refactor. Focused fixtures must prove:

1. Child sessions are discovered and raise totals by exactly their own cost,
   and an archived root excludes its children and grandchildren.
2. Total equals root cost plus child cost, with no double counting, proven
   against a fixture whose parent cost is lower than its children's sum.
3. Each child produces one `spawned` agent record at its resolved depth whose cost and
   token fields equal its session row.
4. Parent agent identity is an opaque digest, never a raw session id.
5. A child with a missing parent stays a counted standalone session, creates
   no edge, and is the only source of unresolved disclosure.
5a. A grandchild resolves its root's project, depth 2, and root session id.
5b. Root, active child, and grandchild form one current session and one cap.
6. A free-tier child reporting tokens with `cost=0` reports a measured zero
   with cost available, and is never shown as unpriced.
7. `parent_id`, `directory`, `slug`, and prompt, tool, or part content never
   reach the browser, MCP, native, or telemetry projections.
8. Children are absent from the default All sessions list but present in totals,
   header stats, filter-aware row-count notes, search (by surfacing the root
   card), and the root card subsection, including nested runs.
9. Existing Claude, Codex, and Kiro agent-record contracts are unchanged.
10. OpenCode agent statistics appear in the Subagents page cohorts with correct
    runtime scoping.

## Acceptance Criteria

- OpenCode child sessions contribute to global totals with no double counting.
- The default All sessions list is unchanged in shape; children appear only
  under their parent card.
- Sessions -> Subagents reports OpenCode children with role, cost, tokens, and
  coverage, distinguishing measured free-tier zeros from unavailable cost.
- No private session identity, path, or provider content appears in any public
  projection.
- Existing routes, budgets, deep links, deletion, and stored preferences remain
  compatible, and existing runtimes' agent behavior is unchanged.
- Required source, browser, installation, runtime-parity, tester, and reviewer
  gates pass against the same immutable head.
