# Claude and Codex Subagent Observability Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add lineage-correct Claude and Codex subagent drill-down, transparent needs-attention signals, and Sessions -> All subagent statistics without changing existing accounting totals or privacy boundaries.

**Architecture:** Each runtime adapter emits private, content-free `_agent_records` beside its existing corrected session summary. A new runtime-neutral domain module validates those records, builds bounded agent groups, and calculates evidence-qualified signals and cohort statistics. Application composition exposes explicit browser-only projections; `page.html` renders the selected-session and all-session experiences while MCP, native, and telemetry contracts remain unchanged.

**Tech Stack:** Python 3 standard library, `unittest`, dependency-free HTML/CSS/JavaScript, Node.js for behavioral JavaScript tests, and the existing Token Meter installer/runtime manifest.

**Spec:** `specs/2026-09-22-subagent-observability-design.md`

## Global Constraints

- Preserve current session IDs, routes, deep links, deletion behavior, budgets, stored preferences, and global accounting totals.
- Keep identical model names scoped by runtime.
- Never expose prompts, responses, reasoning, tool arguments/results, raw rows, paths, `agent_path`, base instructions, credentials, or private physical IDs.
- Preserve unavailable evidence; numeric zero is valid only when measured.
- Keep Codex cost labeled as a public API-equivalent estimate.
- Keep Claude as one top-level session and Codex child sessions independently selectable.
- Bound visible trees to 100 rows while calculating totals over the complete resolved group.
- Explain every needs-attention signal and never claim Token Meter proved a loop.
- Do not add automatic agent mutation, a new top-level page, or MCP/native/telemetry schema changes.
- Keep one tracked-file writer. The commit commands below are checkpoints and require separate user authorization before execution.
- Keep the pre-existing Pi documentation baseline failure out of scope.

---

### Task 1: Runtime-Neutral Agent Group Domain

**Files:**
- Create: `token_meter/domain/agents.py`
- Create: `tests/domain/test_agents.py`
- Modify: `token_meter/domain/__init__.py`

**Interfaces:**
- Consumes: internal summary rows containing zero or more `_agent_records` dictionaries.
- Produces: `build_agent_groups(session_rows, *, now=None, max_agents=100) -> tuple[dict, ...]`.
- Produces: `find_agent_group(groups, session_id) -> dict | None`.
- Produces: `aggregate_agent_usage(groups) -> dict`.
- Input records use `id`, `session_id`, `parent_id`, `runtime`, `kind`, `depth`, `label`, `role`, `model`, `start_ts`, `end_ts`, `mtime`, `active`, `cost`, `cost_available`, `cost_approx`, `tokens`, `input_tokens`, `output_tokens`, `executions`, `attempts`, `retries`, and `failed_attempts`.

- [ ] **Step 1: Write failing group, availability, cycle, privacy, and bound tests**

```python
def test_complete_totals_survive_visible_tree_bound(self):
    rows = [{"_agent_records": [
        agent("root", None, cost=1.0, tokens=100),
        agent("child", "root", cost=2.0, tokens=200, kind="spawned"),
    ]}]
    group = build_agent_groups(rows, max_agents=1)[0]
    self.assertEqual(group["totals"]["agents"], 2)
    self.assertEqual(group["totals"]["tokens"], 300)
    self.assertEqual(group["totals"]["cost"], 3.0)
    self.assertEqual(group["hidden_agents"], 1)
```

Use literal expectations to prove unavailable cost remains `None`, cycles are excluded, unknown keys and paths are dropped, runtime/model cohorts remain separate, and empty evidence does not create a group.

- [ ] **Step 2: Run the focused test and confirm RED**

Run: `python3 -m unittest discover -s tests/domain -p 'test_agents.py' -v`

Expected: import failure for `token_meter.domain.agents`.

- [ ] **Step 3: Implement positive normalization and tree resolution**

```python
MAX_AGENT_ROWS = 100
AGENT_KINDS = frozenset(("root", "spawned", "internal"))

def build_agent_groups(session_rows, *, now=None, max_agents=MAX_AGENT_ROWS):
    records = _normalized_records(session_rows)
    return tuple(
        _project_group(root_id, _resolved_descendants(root_id, records), max_agents)
        for root_id in _root_ids(records)
    )

def find_agent_group(groups, session_id):
    key = str(session_id or "")
    return next((group for group in groups if key in group["_session_ids"]), None)

def aggregate_agent_usage(groups):
    return _aggregate_groups(tuple(groups or ()))
```

Keep `_session_ids` internal and remove it in the public projection. Reject booleans and non-finite/negative numeric evidence rather than coercing it.

- [ ] **Step 4: Add deterministic server signals**

Implement exact thresholds: active concentration at covered cost `>= 1.00` and share `>= 0.50`; peer outlier with at least four comparable children, covered cost `>= 0.50`, and cost `>= 3x` peer median; retry pressure at three retries/failed attempts among the latest five executions. Disable cost signals for partial/unavailable evidence.

- [ ] **Step 5: Run the focused test and mutation check**

Run the Step 2 command. Verify tests fail if cycle rejection is removed, cost availability is ignored, or a threshold moves across its boundary.

- [ ] **Step 6: Prepare the checkpoint without committing**

Inspect the three Task 1 files. After explicit approval only:

```bash
git add token_meter/domain/agents.py token_meter/domain/__init__.py tests/domain/test_agents.py
git commit -m "feat: add subagent group domain"
```

### Task 2: Codex Spawn Metadata and Corrected Records

**Files:**
- Modify: `token_meter/runtimes/codex.py`
- Modify: `tests/runtimes/test_codex_adapter.py`
- Modify: `tests/test_meter.py`

**Interfaces:**
- Consumes: the first valid `session_meta.payload` and corrected `_accounting_rows` output.
- Produces: private source keys `agent_kind`, `agent_nickname`, `agent_role`, `agent_depth`, and `agent_parent_session_id`.
- Produces: one `_agent_records` item on each Codex summary row.

- [ ] **Step 1: Write failing explicit-spawn tests**

Create a parent and child fixture whose child has `source.subagent.thread_spawn` with `parent_thread_id`, `depth`, nickname, role, and a private `agent_path`. Assert safe fields are retained, private fields are absent, the parent resolves to its established public session ID, and fork-only/cyclic/ambiguous children do not become visible spawned agents.

- [ ] **Step 2: Run Codex adapter tests and confirm RED**

Run: `python3 -m unittest discover -s tests/runtimes -p 'test_codex_adapter.py' -v`

Expected: the five agent metadata assertions fail.

- [ ] **Step 3: Parse only bounded structural metadata**

Recognize only object-valued `source.subagent.thread_spawn`. Sanitize nickname/role to 80 characters, reject controls, paths, URLs, and credential-like values, and accept integer depth only from 1 through 32. Never cache `agent_path`, base instructions, history, prompt, or the raw source object.

- [ ] **Step 4: Resolve public parent identity conservatively**

After `_record_by_physical_id` is built, map a unique cycle-free explicit spawn parent to its established public `id`. Missing, duplicate, self, cyclic, and fork-only relationships yield `agent_parent_session_id = None`.

- [ ] **Step 5: Attach one corrected agent record**

Build the record from the existing corrected summary row, not raw token rows. Carry availability, approximate-cost label, timing, execution, attempt, retry, and failure counts from existing summary evidence.

```python
row["_agent_records"] = [{
    "id": source["id"], "session_id": source["id"],
    "parent_id": source.get("agent_parent_session_id"),
    "runtime": "Codex", "kind": source.get("agent_kind") or "root",
    "depth": source.get("agent_depth") or 0,
    "label": source.get("agent_nickname") or "Subagent",
    "role": source.get("agent_role"),
    "cost": row.get("cost"),
    "cost_available": (row.get("availability") or {}).get("cost") is True,
    "tokens": row.get("tokens"), "executions": row.get("turns"),
}]
```

- [ ] **Step 6: Prove inherited usage stays removed**

Extend `CodexLineageAccountingTests` with a spawned child carrying a copied parent prefix. Assert the agent record equals the corrected child summary and not the raw prefix-inclusive total.

- [ ] **Step 7: Run focused Codex tests**

```bash
python3 -m unittest discover -s tests/runtimes -p 'test_codex_adapter.py' -v
python3 -m unittest tests.test_meter.CodexLineageAccountingTests -v
```

- [ ] **Step 8: Prepare the checkpoint without committing**

After explicit approval only:

```bash
git add token_meter/runtimes/codex.py tests/runtimes/test_codex_adapter.py tests/test_meter.py
git commit -m "feat: expose corrected Codex subagent records"
```

### Task 3: Claude Component Attribution and Reconciliation

**Files:**
- Modify: `token_meter/runtimes/claude.py`
- Modify: `tests/runtimes/test_claude_adapter.py`
- Modify: `tests/test_claude_cost_correctness.py`

**Interfaces:**
- Consumes: `_trace_paths` and the canonical logical-message stream.
- Produces: `ClaudeRuntimeAdapter.agent_components(source, *, timestamp_parser) -> tuple[dict, ...]`.
- Produces: `_agent_records` on summaries and `agent_records` on selected detailed state.

- [ ] **Step 1: Write failing ownership tests**

Build main, direct-child, and nested-child traces. Repeat one parent message in the child and add unique child messages. Assert repeated messages stay with the shallowest owner, unique child tokens/cost belong to the child, ID-less rows remain distinct, component totals reconcile, private paths/content are absent, and unavailable child pricing stays unavailable.

- [ ] **Step 2: Run Claude tests and confirm RED**

```bash
python3 -m unittest discover -s tests/runtimes -p 'test_claude_adapter.py' -v
python3 -m unittest tests.test_claude_cost_correctness.ClaudeGroupedDiscoveryTests -v
```

Expected: component assertions fail because summaries do not have `_agent_records`.

- [ ] **Step 3: Preserve private origin during canonicalization**

Add an internal grouped loader that carries a private component key beside each row without inserting path data into provider dictionaries. Order main first, then structural depth, then deterministic private key. Provider message IDs keep their shallowest first owner even when later copies improve usage; ID-less rows keep their physical owner.

- [ ] **Step 4: Extract one content-free usage-fact calculator**

Reuse the same normalized usage, effective-date price, billing-dimension, and cost-coverage logic for aggregate and component accumulation. Return model, timestamp, numeric usage, availability, and estimated cost only.

- [ ] **Step 5: Build opaque records and enforce reconciliation**

Hash a versioned namespace, owning public session ID, and private component key for child IDs. Derive parent/depth from directory ancestry. Label records `Main session`, `Agent 1`, and so on; never derive a role from content. Require exact token reconciliation and cost equality within `1e-9` when cost-covered. On mismatch, omit the breakdown and add fixed warning `agent_breakdown_unavailable`.

- [ ] **Step 6: Attach one shared result to summary and state**

Cache component calculation with the existing source revision. Add records to `summarize_legacy` and `recompute_legacy` without changing aggregate totals.

- [ ] **Step 7: Run focused Claude tests**

Run the Step 2 commands and confirm every existing grouped-discovery total remains unchanged.

- [ ] **Step 8: Prepare the checkpoint without committing**

After explicit approval only:

```bash
git add token_meter/runtimes/claude.py tests/runtimes/test_claude_adapter.py tests/test_claude_cost_correctness.py
git commit -m "feat: attribute Claude usage to subagents"
```

### Task 4: Application Composition and Browser Projection

**Files:**
- Modify: `token_meter/app.py`
- Modify: `token_meter/projections.py`
- Modify: `tests/contracts/test_public_projections.py`
- Modify: `tests/integration/test_application_composition.py`
- Modify: `tests/test_meter.py`

**Interfaces:**
- Consumes: `_agent_records` and Task 1 domain functions.
- Produces: selected-state `agent_group`, cross-session `agent_usage`, and `/sessions` aggregate metadata.
- Preserves: unchanged MCP, menubar, telemetry, spend, model, daily, budget, and deletion output.

- [ ] **Step 1: Write failing composition/privacy tests**

Assert complete internal rows create `agent_usage`, selected sessions receive only their group, projections omit internal membership/private fields, and adding `_agent_records` leaves MCP and menubar fixture output byte-for-byte unchanged.

- [ ] **Step 2: Run composition tests and confirm RED**

```bash
python3 -m unittest tests.integration.test_application_composition -v
python3 -m unittest tests.contracts.test_public_projections -v
```

- [ ] **Step 3: Compose groups before public row slicing**

In `cross_session`, build groups from all `internal_rows` before the 60-row preview. Store internal groups under `_xsess["agent_groups"]`; attach only `aggregate_agent_usage(groups)` to public cross-session data. Clear derived state whenever summaries or membership invalidate.

- [ ] **Step 4: Attach selected group only to browser state**

Use `find_agent_group` with `state["source"]["id"]`. Do not add this field to `menubar_state`, MCP projection, telemetry, or normalized generic projections.

- [ ] **Step 5: Add explicit positive projections**

Create `agent_group_projection` and `agent_usage_projection` in `token_meter/projections.py`. Copy only documented scalar/list keys and drop unknown keys. Remove `_session_ids` before serialization.

- [ ] **Step 6: Preserve complete `/sessions` behavior**

Return projected `agent_usage` with the existing complete lightweight inventory. Do not append raw groups to session rows.

- [ ] **Step 7: Run focused compatibility tests**

Run Step 2 plus `python3 -m unittest tests.test_mcp_queries tests.test_mcp_server -v`.

- [ ] **Step 8: Prepare the checkpoint without committing**

After explicit approval only:

```bash
git add token_meter/app.py token_meter/projections.py tests/contracts/test_public_projections.py tests/integration/test_application_composition.py tests/test_meter.py
git commit -m "feat: compose privacy-safe agent groups"
```

### Task 5: Selected-Session Agent Activity UI

**Files:**
- Modify: `page.html`
- Modify: `tests/test_meter.py`

**Interfaces:**
- Consumes: `CURRENT.agent_group` and browser-local session caps.
- Produces: `agentAttentionReasons(group, previousSnapshot, cap)` and `renderAgentActivity(state)`.
- Uses: existing `selectSession(id)` for Codex and inline expansion for Claude.

- [ ] **Step 1: Write failing Node-backed behavior tests**

Extract pure helpers from embedded JavaScript. Assert unavailable cost renders `--`, cap crossing adds `Cap exceeded`, two active refresh increases totaling at least `$0.25` add `Observed live growth`, reload has no growth history, depth is available to assistive text, labels are escaped, Codex rows navigate by public session ID, and Claude components expand inline.

- [ ] **Step 2: Run the exact new unittest and confirm RED**

Run: `python3 -m unittest tests.test_meter.SubagentDashboardTests.test_selected_agent_activity_is_evidence_qualified -v`

- [ ] **Step 3: Add semantic markup and responsive styles**

Add `session-agent-activity`, `agent-group-summary`, `agent-tree`, and `agent-attention-detail` after the run overview. Hide the module without resolved child context. Use keyboard-operable rows, visible focus, explicit depth text, and a 1024-pixel single-column layout.

- [ ] **Step 4: Implement pure presentation and browser-only signals**

Merge immutable server signals with cap/live-growth reasons in pure helpers. Keep snapshots in an in-memory `Map`; do not persist or send them. Badge text is `Needs attention`, never `Runaway`.

- [ ] **Step 5: Wire rendering and navigation**

Call `renderAgentActivity(s)` from `renderSession`. Navigate Codex rows via `selectSession`; update only inline child detail for Claude. Reset snapshots when the root changes.

- [ ] **Step 6: Run UI tests and JavaScript parsing**

```bash
python3 -m unittest tests.test_meter.SubagentDashboardTests -v
node -e "const fs=require('fs');const h=fs.readFileSync('page.html','utf8');const m=h.match(/<script>([\\s\\S]*)<\\/script>/);new Function(m[1]);console.log('js ok')"
```

- [ ] **Step 7: Prepare the checkpoint without committing**

After explicit approval only:

```bash
git add page.html tests/test_meter.py
git commit -m "feat: add session subagent drill-down"
```

### Task 6: Sessions -> All Subagent Statistics

**Files:**
- Modify: `page.html`
- Modify: `tests/test_meter.py`

**Interfaces:**
- Consumes: `xsession.agent_usage` plus existing runtime/date filters.
- Produces: `renderAgentUsage(usage)`.

- [ ] **Step 1: Write failing aggregate UI tests**

Prove runtime/model/depth cohorts stay separate, internal helpers are separate from spawned agents, anonymous Claude agents get no invented role, partial coverage remains visible, and rendering consumes complete-scope aggregates rather than visible session rows.

- [ ] **Step 2: Run `SubagentDashboardTests` and confirm RED**

Run: `python3 -m unittest tests.test_meter.SubagentDashboardTests -v`

- [ ] **Step 3: Add the Subagent usage section**

Inside Sessions -> All, render parent sessions, agent runs, covered cost, agent spend share, tokens, median/p95 agent cost, output/$, attention count, and a sortable cohort table. Show coverage beside affected measures.

- [ ] **Step 4: Apply only supportable filters**

Use server-provided runtime/date dimensions. When text search is active, show `Subagent statistics are unavailable for this text filter.` instead of calculating from visible rows. Project filtering is implemented by Task 6A using complete server-side scopes.

- [ ] **Step 5: Run UI tests and JavaScript parsing**

Run the Task 5 Step 6 commands.

- [ ] **Step 6: Prepare the checkpoint without committing**

After explicit approval only:

```bash
git add page.html tests/test_meter.py
git commit -m "feat: add subagent usage statistics"
```

### Task 6A: Shared Codex Identity and Project-Scoped Statistics Amendment

**Files:**
- Modify: `token_meter/runtimes/codex.py`
- Modify: `token_meter/domain/agents.py`
- Modify: `token_meter/app.py`
- Modify: `token_meter/projections.py`
- Modify: `page.html`
- Modify: `tests/runtimes/test_codex_adapter.py`
- Modify: `tests/domain/test_agents.py`
- Modify: `tests/contracts/test_public_projections.py`
- Modify: `tests/test_meter.py`

**Interfaces:**
- Consumes: private Codex physical trace IDs, public logical session IDs, root project keys, and corrected `_agent_records` summaries.
- Produces: hashed `agent_id`/`agent_parent_id`, optional unique navigation session IDs, one agent-only summary per physical Codex agent, and exact project/runtime/window usage scopes.
- Preserves: the existing canonical source set and every global accounting consumer.

- [ ] **Step 1: Write failing shared-session Codex adapter tests**

Create two structurally identical parent traces with the same physical and public IDs plus distinct spawned child traces that share the parent's public session ID. Assert the children receive distinct hashed agent IDs, resolve to one hashed parent ID, expose no raw physical ID, and have no misleading navigation session ID. Assert accounting-prefix ambiguity still retains usage.

- [ ] **Step 2: Run the Codex adapter tests and confirm RED**

Run: `python3 -m unittest tests.runtimes.test_codex_adapter.CodexRuntimeAdapterTests.test_duplicate_physical_parent_with_shared_public_session_builds_distinct_agent_identity -v`

Expected: agent identity and relationship assertions fail because records still use public session IDs and duplicate physical parents are discarded.

- [ ] **Step 3: Implement adapter-owned agent identity**

Derive versioned SHA-256 agent IDs from private physical trace IDs. Keep the existing unique-only accounting parent index unchanged. Build a separate agent relationship index that accepts duplicate physical records only when logical ID, parent identity, kind, and project agree, then selects one record by canonical flag, activity time, signature time, and path. Resolve cycles through that index. Publish public session navigation only when it uniquely identifies the physical child.

- [ ] **Step 4: Write failing composition and project-scope tests**

Assert agent-only source selection collapses duplicate physical parents while keeping distinct shared-session children, global session cost/tokens stay byte-for-byte unchanged, root project membership is retained internally, and `token-meter`/`luna-3` project scopes return only their complete agent groups for runtime/time combinations.

- [ ] **Step 5: Run domain, composition, projection, and Node-backed UI tests and confirm RED**

```bash
python3 -m unittest tests.domain.test_agents.AgentGroupDomainTests.test_usage_statistics_support_project_runtime_and_time_scopes -v
python3 -m unittest tests.test_meter.LiveCrossSessionRefreshTests.test_cross_session_uses_physical_agents_without_changing_accounting_totals -v
python3 -m unittest tests.contracts.test_public_projections.PublicProjectionTests.test_agent_usage_projection_allowlists_bounded_project_scopes -v
python3 -m unittest tests.test_meter.DashboardLayoutTests.test_subagent_usage_scope_supports_project_filters_and_blocks_text_search -v
```

- [ ] **Step 6: Implement agent-only source selection and exact project scopes**

Keep `canonical_aggregation_sources()` and `internal_rows` unchanged. Add a separate deterministic agent-source selector, reuse cached summaries, and pass only those rows to `build_agent_groups()`. Carry the root source's already-public project filter key as internal group metadata. Extend `aggregate_agent_usage()` scopes with a project field, projecting at most 480 deterministic scopes plus explicit truncation metadata.

- [ ] **Step 7: Select exact project scopes in the browser**

Change `selectSubagentUsageScope()` to match project, runtime, and time while blocking only text search. A supported scope with zero agents renders the existing no-match state; a scope omitted by the server's bound remains unavailable. Never derive statistics from visible rows.

- [ ] **Step 8: Run the focused amendment suite**

Run Steps 2 and 5 plus all Codex adapter, agent domain, public projection, application composition, and Subagent Dashboard tests. Parse embedded JavaScript and run `git diff --check`.

### Task 7: Documentation and Proportional Developer Verification

**Files:**
- Modify: `README.md`
- Modify: `specs/USER_GUIDE.md`
- Modify: `specs/ARCHITECTURE.md`
- Modify: `specs/plans/active.md`

**Interfaces:**
- Documents: hierarchy, estimates, coverage, anonymous Claude roles, attention limitations, and no automatic stopping.
- Verifies: focused/full source behavior, browser behavior, packaging, installed runtime, and parity.

- [ ] **Step 1: Update user and architecture documentation**

Add one README product-tour paragraph, a User Guide section, and the adapter/domain/browser boundary to Architecture. State that costs are estimates, needs-attention is investigative evidence, Claude roles stay anonymous without safe metadata, and Token Meter does not stop agents.

- [ ] **Step 2: Run focused feature tests**

```bash
python3 -m unittest discover -s tests/domain -p 'test_agents.py' -v
python3 -m unittest discover -s tests/runtimes -p 'test_claude_adapter.py' -v
python3 -m unittest discover -s tests/runtimes -p 'test_codex_adapter.py' -v
python3 -m unittest tests.test_claude_cost_correctness.ClaudeGroupedDiscoveryTests tests.test_meter.CodexLineageAccountingTests tests.test_meter.SubagentDashboardTests -v
python3 -m unittest tests.contracts.test_public_projections tests.integration.test_application_composition tests.test_mcp_queries tests.test_mcp_server -v
```

- [ ] **Step 3: Run static and packaging gates**

```bash
PYTHONPYCACHEPREFIX=/private/tmp/token-meter-pycache python3 -m py_compile meter.py token_meter_mcp.py $(find token_meter -type f -name '*.py' -print)
node -e "const fs=require('fs');const h=fs.readFileSync('page.html','utf8');const m=h.match(/<script>([\\s\\S]*)<\\/script>/);new Function(m[1]);console.log('js ok')"
bash -n scripts/install scripts/install-linux scripts/install-launch-agent scripts/install-systemd-user scripts/run-menubar scripts/run-token-meter-mcp scripts/start-token-meter scripts/uninstall-launch-agent scripts/uninstall-systemd-user scripts/update scripts/update-linux
swiftc menubar/TokenMeterMenuBar.swift -o /private/tmp/token-meter-menubar
TOKEN_METER_MENUBAR_SMOKE=1 /private/tmp/token-meter-menubar
git diff --check
```

- [ ] **Step 4: Run the complete suite**

Run: `python3 -m unittest discover -s tests -v`

No new failure is acceptable. If the only failure remains the known Pi README phrase mismatch, report it as baseline rather than fixing it in this feature.

- [ ] **Step 5: Install and verify live runtime**

Run `./scripts/install`, then verify `/health`, `/menubar`, both LaunchAgents, automatic start, the installer-reported uninstall command, runtime-manifest parity, and that the native payload contains no agent-group data.

- [ ] **Step 6: Browser-check both supported widths**

At 1440x900 and 1024x768, verify Claude breakdown, Codex navigation/breadcrumbs, unavailable cost, attention explanations, Sessions -> All cohorts, keyboard behavior, and absence of clipping, raw IDs, or paths.

- [ ] **Step 7: Update active evidence and request commit authorization**

Record exact checks in ignored `specs/plans/active.md`. Present the scoped diff and evidence. Explain that high-risk independent gates require an immutable commit; do not commit until explicitly approved.

- [ ] **Step 8: Commit only after approval**

```bash
git add README.md page.html specs/2026-09-22-subagent-observability-design.md specs/USER_GUIDE.md specs/ARCHITECTURE.md specs/plans/2026-09-22-subagent-observability.md token_meter/domain/__init__.py token_meter/domain/agents.py token_meter/app.py token_meter/projections.py token_meter/runtimes/claude.py token_meter/runtimes/codex.py tests/domain/test_agents.py tests/contracts/test_public_projections.py tests/integration/test_application_composition.py tests/runtimes/test_claude_adapter.py tests/runtimes/test_codex_adapter.py tests/test_claude_cost_correctness.py tests/test_meter.py
git commit -m "feat: add Claude and Codex subagent observability"
```

- [ ] **Step 9: Run independent immutable-head gates**

Obtain one independent tester result and two project reviewer results with distinct requirements/correctness and privacy/consumer lenses. Any tracked-file edit invalidates all three. Fix accepted findings through a new red/green cycle and rerun every required gate against the new immutable head.
