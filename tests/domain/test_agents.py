import time
import unittest

from token_meter.domain.agents import (
    aggregate_agent_usage,
    build_agent_groups,
    find_agent_group,
)


def agent(agent_id, *, parent_id=None, session_id=None, kind="spawned",
          runtime="codex", model="model-a", depth=1, cost=0.25,
          cost_available=True, tokens=100, tokens_available=True,
          activity_state="recent", role=None, **extra):
    row = {
        "id": agent_id,
        "parent_id": parent_id,
        "session_id": session_id,
        "kind": kind,
        "runtime": runtime,
        "client": runtime.title(),
        "model": model,
        "depth": depth,
        "cost": cost,
        "cost_available": cost_available,
        "tokens": tokens,
        "tokens_available": tokens_available,
        "activity_state": activity_state,
        "role": role,
        "label": extra.pop("label", ""),
        "started_at": extra.pop("started_at", 10),
        "ended_at": extra.pop("ended_at", 20),
        "last_activity_at": extra.pop("last_activity_at", 20),
        "executions": extra.pop("executions", 1),
        "attempts": extra.pop("attempts", 1),
        "retries": extra.pop("retries", 0),
        "failed_attempts": extra.pop("failed_attempts", 0),
        "tool_calls": extra.pop("tool_calls", 0),
        **extra,
    }
    return row


def session(session_id, *records, project=None):
    row = {"id": session_id, "_agent_records": list(records)}
    if project is not None:
        row["project"] = project
    return row


class AgentGroupDomainTests(unittest.TestCase):
    def test_builds_tree_and_selects_group_from_a_child_session(self):
        rows = [
            session("root-session", agent(
                "root", session_id="root-session", kind="root", depth=0,
                cost=0.5, tokens=200,
            )),
            session("child-session", agent(
                "child", parent_id="root", session_id="child-session",
                label="Researcher", role="research", cost=1.5, tokens=800,
            )),
            session("grandchild-session", agent(
                "grandchild", parent_id="child",
                session_id="grandchild-session", depth=2, cost=0.25,
                tokens=100,
            )),
        ]

        groups = build_agent_groups(rows, now=30)
        selected = find_agent_group(groups, "child-session")

        self.assertEqual(len(groups), 1)
        self.assertEqual(selected["root_session_id"], "root-session")
        self.assertEqual(selected["selected_agent_id"], "child")
        self.assertEqual(
            [(row["id"], row["parent_id"], row["depth"])
             for row in selected["agents"]],
            [("root", None, 0), ("child", "root", 1),
             ("grandchild", "child", 2)],
        )
        self.assertEqual(selected["totals"], {
            "agents": 3,
            "tokens": 1100,
            "known_tokens": 1100,
            "tokens_available": True,
            "cost": 2.25,
            "known_cost": 2.25,
            "cost_available": True,
        })
        self.assertAlmostEqual(selected["agents"][1]["group_cost_share"], 2 / 3)
        self.assertTrue(selected["agents"][1]["navigable"])

    def test_partial_cost_and_tokens_remain_unavailable_not_zero(self):
        groups = build_agent_groups([session(
            "root-session",
            agent("root", session_id="root-session", kind="root", depth=0,
                  cost=0.4, tokens=100),
            agent("child", parent_id="root", cost=0.6,
                  cost_available=False, tokens=50, tokens_available=False,
                  input_tokens=30, output_tokens=20),
        )])

        group = groups[0]
        self.assertIsNone(group["totals"]["cost"])
        self.assertEqual(group["totals"]["known_cost"], 1.0)
        self.assertFalse(group["totals"]["cost_available"])
        self.assertIsNone(group["totals"]["tokens"])
        self.assertEqual(group["totals"]["known_tokens"], 150)
        self.assertFalse(group["totals"]["tokens_available"])
        self.assertEqual(group["coverage"]["cost"], "partial")
        self.assertEqual(group["coverage"]["tokens"], "partial")
        self.assertIsNone(group["agents"][1]["cost"])
        self.assertIsNone(group["agents"][1]["tokens"])
        self.assertIsNone(group["agents"][1]["input_tokens"])
        self.assertIsNone(group["agents"][1]["output_tokens"])
        self.assertEqual(group["attention"], [])

        usage = aggregate_agent_usage(groups)
        self.assertEqual(usage["totals"]["group_cost_covered_sessions"], 0)
        self.assertEqual(usage["totals"]["parent_sessions"], 1)

    def test_excludes_unresolved_ambiguous_and_cyclic_relationships(self):
        groups = build_agent_groups([
            session(
                "root-session",
                agent("root", session_id="root-session", kind="root", depth=0),
                agent("valid", parent_id="root"),
                agent("missing", parent_id="not-present"),
                agent("cycle-a", parent_id="cycle-b", depth=2),
                agent("cycle-b", parent_id="cycle-a", depth=3),
            ),
            session("duplicate", agent(
                "valid", parent_id="somewhere-else", session_id="duplicate",
            )),
        ])

        self.assertEqual(len(groups), 0)

        groups = build_agent_groups([session(
            "root-session",
            agent("root", session_id="root-session", kind="root", depth=0),
            agent("valid", parent_id="root"),
            agent("missing", parent_id="not-present"),
            agent("cycle-a", parent_id="cycle-b", depth=2),
            agent("cycle-b", parent_id="cycle-a", depth=3),
        )])
        self.assertEqual([row["id"] for row in groups[0]["agents"]], [
            "root", "valid",
        ])
        self.assertEqual(groups[0]["coverage"]["relationships"], "partial")

    def test_visible_rows_are_bounded_but_totals_cover_all_descendants(self):
        records = [agent(
            "root", session_id="root-session", kind="root", depth=0,
            cost=1, tokens=100,
        )]
        records.extend(
            agent(f"child-{index:03}", parent_id="root", cost=1, tokens=100)
            for index in range(105)
        )

        group = build_agent_groups(
            [session("root-session", *records)], max_agents=100,
        )[0]

        self.assertEqual(len(group["agents"]), 100)
        self.assertEqual(group["hidden_agent_count"], 6)
        self.assertEqual(group["totals"]["agents"], 106)
        self.assertEqual(group["totals"]["tokens"], 10_600)
        self.assertEqual(group["totals"]["cost"], 106)
        self.assertEqual(group["child_totals"]["agents"], 105)
        self.assertEqual(group["child_totals"]["tokens"], 10_500)
        self.assertEqual(group["child_totals"]["cost"], 105)

    def test_attention_signals_are_deterministic_and_explain_thresholds(self):
        records = [agent(
            "root", session_id="root-session", kind="root", depth=0,
            cost=0.4, tokens=100,
        )]
        records.extend([
            agent("high", parent_id="root", cost=3.0, tokens=100,
                  activity_state="working", retries=3),
            agent("peer-a", parent_id="root", cost=0.1, tokens=100),
            agent("peer-b", parent_id="root", cost=0.2, tokens=100),
            agent("peer-c", parent_id="root", cost=0.2, tokens=100),
        ])

        group = build_agent_groups([session("root-session", *records)])[0]
        by_agent = {
            item["agent_id"]: item["reasons"] for item in group["attention"]
        }

        self.assertEqual(
            [reason["code"] for reason in by_agent["high"]],
            ["active_cost_concentration", "peer_cost_outlier", "retry_pressure"],
        )
        self.assertIn("$1.00", by_agent["high"][0]["explanation"])
        self.assertIn("50%", by_agent["high"][0]["explanation"])
        self.assertIn("3x", by_agent["high"][1]["explanation"])
        self.assertIn("3", by_agent["high"][2]["explanation"])
        self.assertEqual(group["agents"][1]["attention_level"], "needs_attention")

    def test_projection_is_allowlisted_and_drops_private_or_arbitrary_fields(self):
        groups = build_agent_groups([session(
            "root-session",
            agent("root", session_id="root-session", kind="root", depth=0),
            agent(
                "child", parent_id="root", label="  Named   Agent  ",
                role="  reviewer  ", agent_path="/private/agent.md",
                prompt="secret", tool_input={"secret": True},
                arbitrary_provider_string="not public",
            ),
        )])

        child = groups[0]["agents"][1]
        self.assertEqual(child["label"], "Named Agent")
        self.assertEqual(child["role"], "reviewer")
        for private_key in (
            "agent_path", "prompt", "tool_input", "arbitrary_provider_string",
            "path", "trace_path",
        ):
            self.assertNotIn(private_key, child)

    def test_cross_session_usage_counts_only_children_and_scopes_models(self):
        groups = build_agent_groups([
            session(
                "codex-root",
                agent("codex-root-agent", session_id="codex-root", kind="root",
                      depth=0, runtime="codex", model="shared", cost=1,
                      tokens=100),
                agent("codex-child", parent_id="codex-root-agent",
                      runtime="codex", model="shared", role="reviewer",
                      cost=2, tokens=200),
            ),
            session(
                "claude-root",
                agent("claude-root-agent", session_id="claude-root", kind="root",
                      depth=0, runtime="claude", model="shared", cost=3,
                      tokens=300),
                agent("claude-child", parent_id="claude-root-agent",
                      runtime="claude", model="shared", role=None, cost=4,
                      tokens=400),
            ),
        ])

        usage = aggregate_agent_usage(groups)

        self.assertEqual({
            key: usage["totals"][key] for key in (
                "agents", "tokens", "known_tokens", "tokens_available",
                "cost", "known_cost", "cost_available",
            )
        }, {
            "agents": 2,
            "tokens": 600,
            "known_tokens": 600,
            "tokens_available": True,
            "cost": 6.0,
            "known_cost": 6.0,
            "cost_available": True,
        })
        self.assertEqual(
            [(row["id"], row["agents"], row["cost"])
             for row in usage["models"]],
            [("shared::claude::spawned", 1, 4.0),
             ("shared::codex::spawned", 1, 2.0)],
        )
        self.assertEqual(usage["roles"], [{
            "id": "reviewer::codex::spawned",
            "role": "reviewer",
            "runtime": "codex",
            "kind": "spawned",
            "agents": 1,
            "tokens": 200,
            "known_tokens": 200,
            "tokens_available": True,
            "cost": 2.0,
            "known_cost": 2.0,
            "cost_available": True,
            "cost_covered_agents": 1,
            "token_covered_agents": 1,
            "input_tokens": 0,
            "known_input_tokens": 0,
            "output_tokens": 0,
            "known_output_tokens": 0,
            "cache_read_tokens": 0,
            "known_cache_read_tokens": 0,
            "cache_write_tokens": 0,
            "known_cache_write_tokens": 0,
            "reasoning_tokens": 0,
            "known_reasoning_tokens": 0,
            "executions": 1,
            "cost_per_agent": 2.0,
            "median_cost": 2.0,
            "p95_cost": 2.0,
            "output_per_dollar": 0.0,
            "complete_agents": 0,
            "incomplete_agents": 0,
            "working_agents": 0,
            "attention_agents": 0,
        }])

    def test_cross_session_usage_includes_bounded_content_free_inventory(self):
        groups = build_agent_groups([session(
            "root-session",
            agent(
                "root", session_id="root-session", kind="root", depth=0,
                cost=1, tokens=100, label="Root title",
            ),
            agent(
                "child", parent_id="root", runtime="codex",
                label="Heisenberg", role="token_meter_reviewer",
                activity_state="incomplete", cost=2, tokens=200,
                retries=3, last_activity_at=25,
                agent_path="/private/agent.md", prompt="secret prompt",
            ),
            project="~/Documents/github/token-meter",
        )], now=30)

        usage = aggregate_agent_usage(groups, now=30, max_inventory=1)

        self.assertEqual(usage["inventory_count"], 1)
        self.assertFalse(usage["inventory_truncated"])
        self.assertEqual(usage["inventory"], [{
            "id": "child",
            "root_session_id": "root-session",
            "project": "~/Documents/github/token-meter",
            "runtime": "codex",
            "client": "Codex",
            "kind": "spawned",
            "depth": 1,
            "label": "Heisenberg",
            "role": "token_meter_reviewer",
            "model": "model-a",
            "activity_state": "incomplete",
            "last_activity_at": 25.0,
            "tokens": 200,
            "tokens_available": True,
            "cost": 2.0,
            "cost_available": True,
            "elapsed_s": 10.0,
            "executions": 1,
            "attempts": 1,
            "retries": 3,
            "failed_attempts": 0,
            "tool_calls": 0,
            "attention": [{
                "code": "retry_pressure",
                "explanation": (
                    "Provider evidence reports at least 3 retries or failed "
                    "attempts in the available recent execution window."
                ),
            }],
        }])
        encoded = repr(usage["inventory"])
        self.assertNotIn("agent_path", encoded)
        self.assertNotIn("secret prompt", encoded)

        many_records = [agent(
            "many-root", session_id="many-root-session", kind="root", depth=0,
        )]
        many_records.extend(
            agent(
                f"child-{index:04}", parent_id="many-root",
                last_activity_at=index,
            )
            for index in range(4)
        )
        many_usage = aggregate_agent_usage(
            build_agent_groups([session("many-root-session", *many_records)]),
            max_inventory=2,
        )
        self.assertEqual(many_usage["inventory_count"], 4)
        self.assertEqual(len(many_usage["inventory"]), 2)
        self.assertTrue(many_usage["inventory_truncated"])
        self.assertEqual(
            [row["id"] for row in many_usage["inventory"]],
            ["child-0003", "child-0002"],
        )

    def test_usage_statistics_support_time_runtime_and_kind_scopes(self):
        now = 1_000_000
        groups = build_agent_groups([
            session(
                "codex-root",
                agent("codex-root-agent", session_id="codex-root", kind="root",
                      depth=0, runtime="codex", cost=1, tokens=100,
                      last_activity_at=now - 5),
                agent("spawned", parent_id="codex-root-agent",
                      runtime="codex", kind="spawned", model="shared",
                      role="researcher", cost=2, tokens=200,
                      input_tokens=120, output_tokens=80, retries=3,
                      last_activity_at=now - 10),
                agent("internal", parent_id="codex-root-agent",
                      runtime="codex", kind="internal", model="shared",
                      cost=4, tokens=400, input_tokens=250,
                      output_tokens=150, last_activity_at=now - 20),
            ),
            session(
                "claude-root",
                agent("claude-root-agent", session_id="claude-root", kind="root",
                      depth=0, runtime="claude", cost=3, tokens=300,
                      last_activity_at=now - 200_000),
                agent("claude-child", parent_id="claude-root-agent",
                      runtime="claude", kind="spawned", model="shared",
                      cost=6, tokens=600, input_tokens=400,
                      output_tokens=200, last_activity_at=now - 200_000),
            ),
        ], now=now)

        usage = aggregate_agent_usage(groups, now=now)
        totals = usage["totals"]

        self.assertEqual(totals["agents"], 3)
        self.assertEqual(totals["parent_sessions"], 2)
        self.assertEqual(totals["output_tokens"], 430)
        self.assertEqual(totals["median_cost"], 4.0)
        self.assertEqual(totals["p95_cost"], 6.0)
        self.assertAlmostEqual(totals["output_per_dollar"], 430 / 12)
        self.assertAlmostEqual(totals["agent_spend_share"], 12 / 16)
        self.assertEqual(totals["group_cost_coverage"], "estimated")
        self.assertEqual(totals["group_cost_covered_sessions"], 2)
        self.assertEqual(totals["attention_agents"], 1)
        self.assertEqual(
            [(row["runtime"], row["model"], row["kind"])
             for row in usage["models"]],
            [("claude", "shared", "spawned"),
             ("codex", "shared", "internal"),
             ("codex", "shared", "spawned")],
        )

        scopes = {
            (row["window"], row["runtime"]): row
            for row in usage["scopes"]
        }
        recent = scopes[("24h", "")]
        recent_codex = scopes[("24h", "codex")]
        recent_claude = scopes[("24h", "claude")]
        self.assertEqual(recent["totals"]["agents"], 2)
        self.assertEqual(recent["totals"]["parent_sessions"], 1)
        self.assertEqual(recent_codex["totals"]["cost"], 6.0)
        self.assertEqual(recent_claude["totals"]["agents"], 0)
        self.assertEqual(
            {row["kind"] for row in recent_codex["kinds"]},
            {"spawned", "internal"},
        )

    def test_usage_statistics_support_project_runtime_and_time_scopes(self):
        now = 1_000_000
        groups = build_agent_groups([
            session(
                "token-root",
                agent("token-root-agent", session_id="token-root", kind="root",
                      depth=0, runtime="claude", cost=1, tokens=100,
                      last_activity_at=now - 10),
                project="~/Documents/github/token-meter",
            ),
            session(
                "token-child",
                agent("token-child-agent", parent_id="token-root-agent",
                      runtime="claude", cost=2, tokens=200,
                      last_activity_at=now - 20),
                project="~/Documents/github/token-meter/.worktrees/child",
            ),
            session(
                "luna-root",
                agent("luna-root-agent", session_id="luna-root", kind="root",
                      depth=0, runtime="codex", cost=3, tokens=300,
                      last_activity_at=now - 200_000),
                project="~/Documents/github/luna-3",
            ),
            session(
                "luna-child",
                agent("luna-child-agent", parent_id="luna-root-agent",
                      runtime="codex", cost=4, tokens=400,
                      last_activity_at=now - 200_000),
                project="~/Documents/github/luna-3",
            ),
        ], now=now)

        usage = aggregate_agent_usage(groups, now=now)
        token_scopes = [
            row for row in usage["scopes"]
            if row.get("project") == "~/Documents/github/token-meter"
            and row["window"] == "24h" and row["runtime"] == "claude"
        ]
        luna_scopes = [
            row for row in usage["scopes"]
            if row.get("project") == "~/Documents/github/luna-3"
            and row["window"] == "7d" and row["runtime"] == "codex"
        ]

        self.assertEqual(groups[0].get("_project"), "~/Documents/github/luna-3")
        self.assertEqual(groups[1].get("_project"), "~/Documents/github/token-meter")
        self.assertEqual(len(token_scopes), 1)
        self.assertEqual(token_scopes[0]["totals"]["agents"], 1)
        self.assertEqual(token_scopes[0]["totals"]["cost"], 2.0)
        self.assertEqual(len(luna_scopes), 1)
        self.assertEqual(luna_scopes[0]["totals"]["agents"], 1)
        self.assertEqual(luna_scopes[0]["totals"]["cost"], 4.0)

    def test_role_economics_compares_equal_periods_and_groups_local_days(self):
        now = 2_000_000
        current_a = now - 60
        current_b = now - 86_460
        previous = now - 604_860
        older = now - 1_209_660
        records = [agent(
            "root", session_id="root-session", kind="root", depth=0,
            cost=1, tokens=100, last_activity_at=now,
        )]
        records.extend([
            agent(
                "current-a", parent_id="root", role="reviewer", cost=2,
                tokens=200, activity_state="complete",
                last_activity_at=current_a,
            ),
            agent(
                "current-b", parent_id="root", role="reviewer", cost=4,
                tokens=400, activity_state="incomplete", retries=3,
                last_activity_at=current_b,
            ),
            agent(
                "previous", parent_id="root", role="reviewer", cost=6,
                tokens=600, activity_state="complete",
                last_activity_at=previous,
            ),
            agent(
                "older", parent_id="root", role="reviewer", cost=8,
                tokens=800, activity_state="complete",
                last_activity_at=older,
            ),
            agent(
                "anonymous", parent_id="root", role=None, cost=99,
                tokens=9_900, last_activity_at=current_a,
            ),
        ])
        usage = aggregate_agent_usage(build_agent_groups([
            session("root-session", *records, project="/projects/token-meter"),
        ], now=now), now=now)

        scope = next(
            row for row in usage["scopes"]
            if row["project"] == "/projects/token-meter"
            and row["runtime"] == "codex" and row["window"] == "7d"
        )
        current_role = scope["roles"][0]
        previous_role = scope["comparison"]["roles"][0]
        self.assertEqual(
            (current_role["agents"], current_role["cost"],
             current_role["incomplete_agents"],
             current_role["attention_agents"]),
            (2, 6.0, 1, 1),
        )
        self.assertEqual(
            (previous_role["agents"], previous_role["cost"],
             previous_role["incomplete_agents"]),
            (1, 6.0, 0),
        )
        self.assertNotIn("comparison", next(
            row for row in usage["scopes"]
            if row["project"] == "/projects/token-meter"
            and row["runtime"] == "codex" and row["window"] == "all"
        ))

        self.assertEqual(usage["role_day_count"], 4)
        self.assertFalse(usage["role_days_truncated"])
        self.assertEqual(
            {row["day"] for row in usage["role_days"]},
            {
                time.strftime("%Y-%m-%d", time.localtime(timestamp))
                for timestamp in (current_a, current_b, previous, older)
            },
        )
        latest = next(
            row for row in usage["role_days"]
            if row["day"] == time.strftime(
                "%Y-%m-%d", time.localtime(current_a)
            )
        )
        self.assertEqual(latest["project"], "/projects/token-meter")
        self.assertEqual(latest["role"], "reviewer")
        self.assertNotEqual(latest["known_cost"], 99)

    def test_role_day_series_is_bounded_without_changing_exact_role_totals(self):
        now = 2_000_000
        records = [agent(
            "root", session_id="root-session", kind="root", depth=0,
            last_activity_at=now,
        )]
        records.extend(
            agent(
                f"child-{index}", parent_id="root", role="reviewer",
                cost=index + 1, tokens=100, last_activity_at=now - index * 86_400,
            )
            for index in range(4)
        )
        usage = aggregate_agent_usage(
            build_agent_groups([session("root-session", *records)], now=now),
            now=now, max_role_days=2,
        )

        self.assertEqual(usage["role_day_count"], 4)
        self.assertEqual(len(usage["role_days"]), 2)
        self.assertTrue(usage["role_days_truncated"])
        self.assertEqual(usage["roles"][0]["agents"], 4)
        self.assertEqual(usage["roles"][0]["cost"], 10.0)


if __name__ == "__main__":
    unittest.main()
