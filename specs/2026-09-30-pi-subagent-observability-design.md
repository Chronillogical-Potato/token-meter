# Pi Subagent Observability

## Status

Implemented in pull request #61. This document is the design record and
implementation contract for adding Pi child-agent visibility to Token Meter. It extends the approved
`specs/2026-09-22-subagent-observability-design.md` contract, whose non-goals
excluded Pi, and follows the Cursor and OpenCode amendments that added the
other runtimes.

This change crosses provider parsing, privacy boundaries, and accounting
semantics, so the completed immutable head requires one independent tester and
two independent project reviewers with distinct requirements/correctness and
privacy/consumer lenses.

## Problem

Pi records child-agent work inside the parent session transcript. When a
session invokes the shipped `subagent` tool, each child process runs with
`--no-session`, so no child session file exists; the only record of the run is
the parent's `toolCall` and its `toolResult` message. The Pi adapter parses
assistant messages only, so:

- the child run is absent from Sessions -> Subagents and from the selected
  session's agent group;
- the child's tokens and cost are absent from every Pi total, budget, model
  statistic, and daily figure;
- nothing marks the missing spend, so it renders as a complete total rather
  than an unknown one.

This conflicts with the standing rule that unavailable evidence must not become
a measured zero.

## Observed Evidence

Verified against a live run of the shipped
`examples/extensions/subagent/index.ts` on 2026-09-30, with one user-level
agent in an isolated Pi config:

- Assistant content contains
  `{"type":"toolCall","id":"...","name":"subagent","arguments":{"agent":"probe","task":"Say pong"}}`.
- The matching transcript entry persists a `toolResult` message with
  `details: {mode, agentScope, projectAgentsDir, results[]}`. Each result has
  `agent`, `agentSource`, `exitCode`, `stopReason`, `model`, `usage`
  (`input`, `output`, `cacheRead`, `cacheWrite`, `cost`, `contextTokens`,
  `turns`), and also the child's `messages`, `task`, and `stderr`.
- The shipped example sets no top-level result `usage`. The Pi documentation
  (`docs/message-types.md`, `docs/extensions.md`) defines that field for tools
  that make nested model calls and states it contributes to full-session
  statistics; this design supports it as the authoritative accounting source.
- Pi writes no `usage` session entry for the child run.

`messages`, `task`, `stderr`, `errorMessage`, and result `content` are content
and are never read by the adapter.

## Decisions

1. **Structural detection.** Only a tool call whose normalized name is
   `subagent` with a matching `toolCallId` result is recognized. Unrelated
   nested-usage tools keep today's behavior and cannot invent agent records.
2. **Attribution.** Child runs come from `details.results[]`. The bounded
   fields are `agent`, `exitCode`, `stopReason`, `model`, and `usage`.
   Result list length is capped; missing or malformed entries are skipped
   rather than repaired. A non-empty `results` list with no valid entry and no
   usage is one unavailable run, not an absent child. A repeated tool-call id
   never replaces evidence already finished for that id.
3. **One accounting source.** When the tool result carries a top-level `usage`,
   it is authoritative. Per-result usage is attributed only when every result
   carries usage and the sums match the top-level figures exactly; otherwise a
   single aggregate run is recorded and the individual breakdown is withheld.
   When no top-level usage exists, the sum of per-result usage is the session's
   nested spend. This is the only path that can change historical Pi totals.
4. **Totals.** Nested child spend is added to the Pi session's token and cost
   totals, model statistics, and daily cost, and therefore to global totals,
   budgets, and the menu bar. It is not added to the parent's execution list,
   wait samples, or active-time intervals; child work is not a parent model
   call. Session pace diagnostics therefore keep the parent output
   denominator, so throughput coverage is unchanged for the parent's model
   calls, and child wall time is reported on the agent record.
5. **Root invariant.** A session with at least one child run emits one `root`
   agent record whose metrics exclude nested spend, so root plus children equal
   the session headline exactly.
6. **Availability.** A run with no usage evidence keeps its tokens and cost
   unavailable and makes the affected session coverage partial rather than
   folding an unknown into a complete total. A finite non-negative reported
   cost, including `0.0`, is measured and available. When the session-wide
   child-run cap drops any call or child, or children are dropped without an
   authoritative total, nested tokens, cache, and cost become unavailable and
   the session reports bounded history. A child token total includes cache
   buckets, so a child without both cache figures reports unavailable tokens.
7. **Identity.** Child agent IDs are versioned namespaced SHA-256 digests over
   the public session id, tool-call id, and result index. The root record uses
   the same construction over the session id. No path, raw physical id, task,
   prompt, or child message is encoded or projected.
8. **Roles.** The provider-reported `agent` name is the role. It is bounded to
   64 characters and must match `[A-Za-z][A-Za-z0-9_-]*`; paths, URLs,
   credentials, credential-shaped tokens, control characters, and arbitrary
   prose are rejected. Roles
   remain browser identity only, as for Claude, Codex, and OpenCode. A reported
   model value must not be path-shaped: hidden or traversal segments, home and
   directory roots, host-shaped namespaces, and model-file extensions are
   rejected. A whole-value hostname, IP address, or host:port; an `@` followed
   by an account or host rather than a version; and credential-shaped tokens
   (`sk-`, GitHub and Slack token prefixes, AWS access-key ids, JWTs) are also
   rejected. Provider namespaces such as `@cf/meta/...`, `opencode-go/...`, and
   `accounts/fireworks/models/...`, version suffixes such as `model@20250514`,
   and tags such as `llama3.1:8b` remain valid.
9. **Lifecycle.** A completed result is `complete` when `exitCode` is absent or
   zero and `stopReason` is not `error` or `aborted`; otherwise `incomplete`.
   A call with no result is `working` while recent and `incomplete` once stale.
   A finished call with an empty `results` list and no usage ran no child and
   emits nothing.
10. **Session versus agent liveness.** Pi persists a `stopReason` on assistant
    entries, and a root agent record derives its own completion from it. The
    session summary row keeps its pre-existing nonterminal value, so a Pi
    session without subagent calls does not change behavior; session-row
    liveness is out of scope for this change.

## Non-Goals

- Parsing or exposing child prompts, tasks, messages, stderr, or outputs.
- Supporting Pi `/fork`, `/clone`, or `parentSession` lineage in this change.
- Counting `usage` session entries of unknown `kind`; that remains a separate
  accounting question.
- Adding subagent support for Kiro or Hermes.
- Changing MCP, native, or telemetry payload schemas.
- Changing Claude, Codex, Cursor, or OpenCode agent behavior.

## Compatibility

Existing Pi session ids, routes, deletion, budgets, and stored preferences are
unchanged. Pi totals intentionally rise by previously unrecorded child spend
for sessions that used the subagent tool; sessions without subagent calls are
byte-for-byte unchanged. Menu-bar, MCP, and telemetry schemas do not change.
The dashboard order is unchanged, and the Subagents page consumes the existing
runtime-neutral inventory without new server routes.

## Test Strategy

Red-green-refactor. Focused fixtures must prove:

1. A single-result run adds exactly its reported tokens and cost to the session
   and emits one `spawned` record plus a `root` record.
2. Parallel results emit one record per child with each child's own metrics.
3. Root plus child metrics equal the session headline with no double counting.
4. A top-level result usage with reconciling per-result usage is counted once.
5. A top-level result usage with non-reconciling per-result usage yields one
   aggregate run and no invented split.
6. A run without usage reports unavailable tokens and cost, never zero.
7. A reported `cost: 0` is a measured zero with cost available.
8. A failed run keeps its role, marks `incomplete`, and leaks no error text.
9. A call with no result reports `incomplete`/`working` with unavailable spend.
10. Roles reject paths, URLs, credentials, control characters, and prose.
11. Task text, child messages, stderr, and content never reach the summary,
    selected state, browser projection, or MCP.
12. `canonical_agent_sources` selects Pi sources once, and the runtime-neutral
    agent group and Subagents inventory include Pi children with roles.

## Acceptance Criteria

- Sessions -> Subagents and the selected-session agent group show Pi child runs
  with role, model, tokens, cost, timing, and activity state.
- Pi session and global totals include child spend exactly once.
- A missing figure stays unavailable and coverage stays explicit.
- No prompt, task, child message, path, or private identity appears in any
  public projection.
- Existing routes, budgets, deep links, deletion, and stored preferences remain
  compatible; sessions without subagent calls do not change.
- Required source, test, browser, installation, parity, tester, and reviewer
  gates pass against the same immutable head.
