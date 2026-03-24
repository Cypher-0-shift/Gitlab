import unittest
from datetime import datetime, timedelta, timezone


# ─── Helpers mirroring standup_flow logic ────────────────────────────────────

def is_stale(updated_at_iso: str, threshold_days: int = 3) -> bool:
    """An issue is stale if it hasn't been updated in > threshold_days."""
    updated = datetime.fromisoformat(updated_at_iso.replace("Z", "+00:00"))
    age = (datetime.now(timezone.utc) - updated).days
    return age > threshold_days

def blocker_age_bucket(days: int) -> str:
    if days <= 2:
        return "🟡 Blocked 1-2 days"
    elif days <= 5:
        return f"🟠 STALE — blocked {days} days"
    else:
        return f"🔴 CRITICAL — blocked {days} days, escalate"

def velocity_trend(this_week: int, last_week: int) -> str:
    if last_week == 0:
        return "→ Velocity stable"
    if this_week > last_week * 1.2:
        return "📈 Velocity up"
    if this_week < last_week * 0.8:
        return "📉 Velocity down"
    return "→ Velocity stable"

def sprint_burndown_status(total_open: int, closed_this_week: int) -> str:
    if total_open > 30 and closed_this_week < 3:
        return "🚨 Sprint at risk"
    if closed_this_week > 8:
        return "📈 Strong velocity"
    return "OK"

def sprint_load_status(total_open: int) -> str:
    if total_open > 55:
        return "🚨 Overloaded"
    if total_open > 30:
        return "⚠️ Heavy"
    return "OK"

def security_debt_urgency(oldest_age_hours: int) -> str:
    if oldest_age_hours > 48:
        return "CRITICAL"
    if oldest_age_hours > 24:
        return "URGENT"
    return "OK"

def build_team_roster(issues: list, mrs: list, agent_user: str) -> list:
    """Collect unique usernames from issue assignees + MR authors, exclude bot."""
    users = set()
    for i in issues:
        if i.get("assignee"):
            users.add(i["assignee"])
    for mr in mrs:
        if mr.get("author"):
            users.add(mr["author"])
    users.discard(agent_user)
    return sorted(users)

def resolve_trigger_iid(goal: str, fallback_issues: list) -> int | None:
    """Extract issue IID from goal text.
    In standup_flow Phase 0 the agent searches for a 'Daily Standup Digest' issue
    (creating one if absent) rather than falling back to the first open issue.
    This helper models the goal-text extraction part of that logic.
    """
    import re
    match = re.search(r"#(\d+)", goal)
    if match:
        return int(match.group(1))
    # Phase 0 creates/finds a dedicated issue — represented here by
    # searching fallback_issues for the digest issue by title.
    digest = next(
        (i for i in fallback_issues if "Standup Digest" in i.get("title", "")),
        None
    )
    if digest:
        return digest["iid"]
    return None

def has_label(issue: dict, label: str) -> bool:
    return label in issue.get("labels", [])

def digest_section_for_member(username: str, issues: list, mrs: list) -> dict:
    """Build per-member digest data."""
    assigned = [i for i in issues if i.get("assignee") == username]
    authored_mrs = [m for m in mrs if m.get("author") == username]
    return {
        "focus": [i for i in assigned if has_label(i, "security::review-required") or
                  has_label(i, "compliance::failed")] or
                 [i for i in assigned if has_label(i, "blocked")] or
                 sorted(assigned, key=lambda x: x.get("updated_at", ""))[:1],
        "stale": [i for i in assigned if i.get("stale")],
        "action_required": [m for m in authored_mrs if
                            has_label(m, "security::review-required") or
                            has_label(m, "compliance::failed") or
                            has_label(m, "deployment::ready")],
    }


# ─── Tests ───────────────────────────────────────────────────────────────────

class TestStaleDetection(unittest.TestCase):
    def _make_iso(self, days_ago):
        dt = datetime.now(timezone.utc) - timedelta(days=days_ago)
        return dt.isoformat()

    def test_not_stale_at_2_days(self):
        self.assertFalse(is_stale(self._make_iso(2)))

    def test_not_stale_at_3_days_exactly(self):
        # threshold is STRICTLY greater than 3
        self.assertFalse(is_stale(self._make_iso(3)))

    def test_stale_at_4_days(self):
        self.assertTrue(is_stale(self._make_iso(4)))

    def test_stale_at_10_days(self):
        self.assertTrue(is_stale(self._make_iso(10)))

    def test_not_stale_today(self):
        self.assertFalse(is_stale(self._make_iso(0)))


class TestBlockerAgeBucket(unittest.TestCase):
    def test_1_day_is_yellow(self):
        self.assertIn("🟡", blocker_age_bucket(1))

    def test_2_days_is_yellow(self):
        self.assertIn("🟡", blocker_age_bucket(2))

    def test_3_days_is_orange(self):
        self.assertIn("🟠", blocker_age_bucket(3))

    def test_5_days_is_orange(self):
        self.assertIn("🟠", blocker_age_bucket(5))

    def test_6_days_is_red_critical(self):
        self.assertIn("🔴", blocker_age_bucket(6))

    def test_14_days_is_red_critical(self):
        result = blocker_age_bucket(14)
        self.assertIn("🔴", result)
        self.assertIn("escalate", result)

    def test_orange_contains_day_count(self):
        result = blocker_age_bucket(4)
        self.assertIn("4", result)

    def test_sort_order_critical_before_stale(self):
        buckets = [blocker_age_bucket(d) for d in [1, 3, 7]]
        criticals = [b for b in buckets if "🔴" in b]
        self.assertEqual(len(criticals), 1)


class TestVelocityTrend(unittest.TestCase):
    def test_up_when_20_percent_more(self):
        self.assertIn("📈", velocity_trend(13, 10))

    def test_down_when_20_percent_less(self):
        self.assertIn("📉", velocity_trend(7, 10))

    def test_stable_at_equal(self):
        self.assertIn("stable", velocity_trend(10, 10))

    def test_stable_at_10_percent_more(self):
        self.assertIn("stable", velocity_trend(11, 10))

    def test_stable_at_10_percent_less(self):
        self.assertIn("stable", velocity_trend(9, 10))

    def test_zero_last_week_is_stable(self):
        # No division error, defaults to stable
        self.assertIn("stable", velocity_trend(5, 0))

    def test_exact_20_percent_threshold(self):
        # 12 vs 10 = exactly 1.2x — NOT strictly greater, so stable
        self.assertIn("stable", velocity_trend(12, 10))


class TestSprintBurndown(unittest.TestCase):
    def test_at_risk_when_overloaded_and_slow(self):
        self.assertIn("🚨", sprint_burndown_status(35, 2))

    def test_strong_velocity_when_closing_fast(self):
        self.assertIn("📈", sprint_burndown_status(20, 9))

    def test_ok_when_low_open_even_if_slow(self):
        self.assertEqual("OK", sprint_burndown_status(20, 2))

    def test_ok_when_normal(self):
        self.assertEqual("OK", sprint_burndown_status(25, 5))

    def test_threshold_is_strictly_30(self):
        # 30 open, 2 closed — NOT >30, so OK
        self.assertEqual("OK", sprint_burndown_status(30, 2))

    def test_at_risk_at_31_open(self):
        self.assertIn("🚨", sprint_burndown_status(31, 2))


class TestSprintLoadStatus(unittest.TestCase):
    def test_ok_at_30(self):
        self.assertEqual("OK", sprint_load_status(30))

    def test_heavy_at_31(self):
        self.assertIn("⚠️", sprint_load_status(31))

    def test_heavy_at_55(self):
        self.assertIn("⚠️", sprint_load_status(55))

    def test_overloaded_at_56(self):
        self.assertIn("🚨", sprint_load_status(56))

    def test_ok_at_zero(self):
        self.assertEqual("OK", sprint_load_status(0))


class TestSecurityDebtUrgency(unittest.TestCase):
    def test_ok_under_24h(self):
        self.assertEqual("OK", security_debt_urgency(12))

    def test_urgent_at_25h(self):
        self.assertEqual("URGENT", security_debt_urgency(25))

    def test_critical_at_49h(self):
        self.assertEqual("CRITICAL", security_debt_urgency(49))

    def test_boundary_24h_is_ok(self):
        self.assertEqual("OK", security_debt_urgency(24))

    def test_boundary_48h_is_urgent(self):
        self.assertEqual("URGENT", security_debt_urgency(48))


class TestTeamRosterBuilding(unittest.TestCase):
    def test_extracts_assignees_from_issues(self):
        issues = [{"iid": 1, "assignee": "alice"}, {"iid": 2, "assignee": "bob"}]
        roster = build_team_roster(issues, [], "bot")
        self.assertIn("alice", roster)
        self.assertIn("bob", roster)

    def test_extracts_authors_from_mrs(self):
        mrs = [{"iid": 1, "author": "carol"}]
        roster = build_team_roster([], mrs, "bot")
        self.assertIn("carol", roster)

    def test_excludes_agent_user(self):
        issues = [{"iid": 1, "assignee": "bot"}, {"iid": 2, "assignee": "alice"}]
        roster = build_team_roster(issues, [], "bot")
        self.assertNotIn("bot", roster)

    def test_deduplicates_usernames(self):
        issues = [{"iid": 1, "assignee": "alice"}, {"iid": 2, "assignee": "alice"}]
        roster = build_team_roster(issues, [], "bot")
        self.assertEqual(roster.count("alice"), 1)

    def test_empty_returns_empty(self):
        self.assertEqual(build_team_roster([], [], "bot"), [])

    def test_unassigned_issues_not_added(self):
        issues = [{"iid": 1, "assignee": None}]
        roster = build_team_roster(issues, [], "bot")
        self.assertEqual(roster, [])


class TestTriggerIIDResolution(unittest.TestCase):
    def test_extracts_iid_from_goal_text(self):
        iid = resolve_trigger_iid("Generate standup for #42", [])
        self.assertEqual(iid, 42)

    def test_falls_back_to_digest_issue(self):
        # Phase 0 finds the dedicated "Daily Standup Digest" issue, not just any issue.
        issues = [{"iid": 7, "title": "Daily Standup Digest"}]
        iid = resolve_trigger_iid("Generate the daily standup digest", issues)
        self.assertEqual(iid, 7)

    def test_returns_none_if_no_digest_issue_and_no_iid(self):
        # No digest issue and no explicit IID → returns None (agent creates it)
        iid = resolve_trigger_iid("Generate the daily standup digest", [])
        self.assertIsNone(iid)

    def test_prefers_goal_iid_over_fallback(self):
        iid = resolve_trigger_iid("Standup for #99", [{"iid": 1, "title": "Daily Standup Digest"}])
        self.assertEqual(iid, 99)

    def test_schedule_goal_finds_digest_issue(self):
        # Scheduled run: no explicit IID, but digest issue exists
        iid = resolve_trigger_iid("Generate the daily standup digest for the team.", [{"iid": 12, "title": "Daily Standup Digest"}])
        self.assertEqual(iid, 12)


class TestLabelChecks(unittest.TestCase):
    def test_has_label_true(self):
        issue = {"labels": ["blocked", "backend"]}
        self.assertTrue(has_label(issue, "blocked"))

    def test_has_label_false(self):
        issue = {"labels": ["backend"]}
        self.assertFalse(has_label(issue, "blocked"))

    def test_empty_labels(self):
        issue = {"labels": []}
        self.assertFalse(has_label(issue, "blocked"))

    def test_missing_labels_key(self):
        issue = {}
        self.assertFalse(has_label(issue, "blocked"))


class TestDigestSectionBuilding(unittest.TestCase):
    BASE_ISSUE = {"iid": 1, "title": "Fix auth", "assignee": "alice",
                  "labels": [], "updated_at": "2024-01-01T00:00:00Z", "stale": False}

    def test_focus_contains_assigned_issue(self):
        result = digest_section_for_member("alice", [self.BASE_ISSUE], [])
        self.assertTrue(len(result["focus"]) > 0)

    def test_no_stale_items_when_fresh(self):
        issue = {**self.BASE_ISSUE, "stale": False}
        result = digest_section_for_member("alice", [issue], [])
        self.assertEqual(result["stale"], [])

    def test_stale_items_when_stale(self):
        issue = {**self.BASE_ISSUE, "stale": True}
        result = digest_section_for_member("alice", [issue], [])
        self.assertEqual(len(result["stale"]), 1)

    def test_action_required_for_sec_mr(self):
        mr = {"iid": 10, "author": "alice", "labels": ["security::review-required"]}
        result = digest_section_for_member("alice", [], [mr])
        self.assertEqual(len(result["action_required"]), 1)

    def test_no_action_for_clean_mr(self):
        mr = {"iid": 10, "author": "alice", "labels": []}
        result = digest_section_for_member("alice", [], [mr])
        self.assertEqual(result["action_required"], [])

    def test_security_label_prioritised_in_focus(self):
        normal = {**self.BASE_ISSUE, "iid": 1, "labels": []}
        sec = {**self.BASE_ISSUE, "iid": 2, "labels": ["security::review-required"]}
        result = digest_section_for_member("alice", [normal, sec], [])
        self.assertEqual(result["focus"][0]["iid"], 2)

    def test_member_with_no_assignments_has_empty_focus(self):
        result = digest_section_for_member("bob", [self.BASE_ISSUE], [])
        self.assertEqual(result["focus"], [])


class TestFlowYamlStructure(unittest.TestCase):
    """Validates flows/standup_flow.yml structure without executing it."""

    def setUp(self):
        import os
        import yaml
        flow_path = os.path.join(os.path.dirname(__file__), "../flows/standup_flow.yml")
        with open(flow_path, encoding='utf-8') as f:
            self.flow = yaml.safe_load(f)
        self.defn = self.flow["definition"]
        self.comp = self.defn["components"][0]
        self.prompt = self.defn["prompts"][0]

    def test_has_schedule_trigger(self):
        triggers = self.defn.get("triggers", [])
        types = [t["type"] for t in triggers]
        self.assertIn("scheduled", types)

    def test_schedule_cron_is_9am_weekdays(self):
        trigger = next(t for t in self.defn["triggers"] if t["type"] == "scheduled")
        self.assertEqual(trigger["cron"], "0 9 * * 1-5")

    def test_toolset_has_mr_search(self):
        self.assertIn("gitlab_merge_request_search", self.comp["toolset"])

    def test_toolset_has_issue_search(self):
        self.assertIn("gitlab_issue_search", self.comp["toolset"])

    def test_toolset_has_get_current_user(self):
        self.assertIn("get_current_user", self.comp["toolset"])

    def test_context_project_id_declared(self):
        self.assertIn("context:project_id", self.comp["inputs"])

    def test_timeout_sufficient(self):
        self.assertGreaterEqual(self.prompt["params"]["timeout"], 240)

    def test_prompt_has_phase0(self):
        system = self.prompt["prompt_template"]["system"]
        self.assertIn("PHASE 0", system)

    def test_prompt_instructs_trigger_iid_resolution(self):
        system = self.prompt["prompt_template"]["system"]
        self.assertIn("TRIGGER_IID", system)

    def test_prompt_instructs_velocity_calculation(self):
        system = self.prompt["prompt_template"]["system"]
        self.assertIn("CLOSED_THIS_WEEK", system)


if __name__ == "__main__":
    unittest.main()