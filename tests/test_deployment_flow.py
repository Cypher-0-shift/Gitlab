import unittest

class TestPipelineStatusSignal(unittest.TestCase):
    def get_signal(self, status):
        if status == "success": return "PASS"
        if status == "failed": return "FAIL"
        return "WARN"
    def test_1(self): self.assertEqual(self.get_signal("success"), "PASS")
    def test_2(self): self.assertEqual(self.get_signal("failed"), "FAIL")
    def test_3(self): self.assertEqual(self.get_signal("running"), "WARN")
    def test_4(self): self.assertEqual(self.get_signal("pending"), "WARN")
    def test_5(self): self.assertEqual(self.get_signal("canceled"), "WARN")
    def test_6(self): self.assertNotEqual(self.get_signal("success"), "FAIL")

class TestTestPassRateSignal(unittest.TestCase):
    def get_signal(self, rate):
        if rate >= 98: return "PASS"
        if rate < 90: return "FAIL"
        return "WARN"
    def test_1(self): self.assertEqual(self.get_signal(100), "PASS")
    def test_2(self): self.assertEqual(self.get_signal(98), "PASS")
    def test_3(self): self.assertEqual(self.get_signal(97), "WARN")
    def test_4(self): self.assertEqual(self.get_signal(90), "WARN")
    def test_5(self): self.assertEqual(self.get_signal(89), "FAIL")
    def test_6(self): self.assertEqual(self.get_signal(0), "FAIL")
    def test_7(self): self.assertNotEqual(self.get_signal(98), "WARN")
    def test_8(self): self.assertNotEqual(self.get_signal(85), "PASS")

class TestMrConflictsSignal(unittest.TestCase):
    def get_signal(self, conflicts): return "FAIL" if conflicts else "PASS"
    def test_1(self): self.assertEqual(self.get_signal(True), "FAIL")
    def test_2(self): self.assertEqual(self.get_signal(False), "PASS")

class TestOpenCriticalsSignal(unittest.TestCase):
    def get_signal(self, count):
        if count >= 3: return "FAIL"
        if count > 0: return "WARN"
        return "PASS"
    def test_1(self): self.assertEqual(self.get_signal(3), "FAIL")
    def test_2(self): self.assertEqual(self.get_signal(4), "FAIL")
    def test_3(self): self.assertEqual(self.get_signal(1), "WARN")
    def test_4(self): self.assertEqual(self.get_signal(2), "WARN")
    def test_5(self): self.assertEqual(self.get_signal(0), "PASS")

class TestSecurityLabelSignal(unittest.TestCase):
    def get_signal(self, label): return "FAIL" if label == "security::review-required" else "PASS"
    def test_1(self): self.assertEqual(self.get_signal("security::review-required"), "FAIL")
    def test_2(self): self.assertEqual(self.get_signal("security::approved"), "PASS")
    def test_3(self): self.assertEqual(self.get_signal("none"), "PASS")
    def test_4(self): self.assertNotEqual(self.get_signal("security::approved"), "FAIL")
    def test_5(self): self.assertTrue(self.get_signal("other") == "PASS")
    def test_6(self): self.assertFalse(self.get_signal("security::review-required") == "PASS")

class TestComplianceLabelSignal(unittest.TestCase):
    def get_signal(self, label): return "FAIL" if label == "compliance::failed" else "PASS"
    def test_1(self): self.assertEqual(self.get_signal("compliance::failed"), "FAIL")
    def test_2(self): self.assertEqual(self.get_signal("compliance::pass"), "PASS")
    def test_3(self): self.assertNotEqual(self.get_signal("compliance::failed"), "PASS")

class TestVerdictComputation(unittest.TestCase):
    """Tests verdict strings that match deployment_flow.yml Phase 4 output."""
    def compute(self, signals):
        if "FAIL" in signals: return "NO-GO"
        if "WARN" in signals: return "PROCEED WITH CAUTION"
        return "GO"

    def test_any_fail_is_no_go(self):
        self.assertEqual(self.compute(["PASS", "FAIL"]), "NO-GO")

    def test_warn_only_is_proceed_with_caution(self):
        self.assertEqual(self.compute(["PASS", "WARN"]), "PROCEED WITH CAUTION")

    def test_all_pass_is_go(self):
        self.assertEqual(self.compute(["PASS", "PASS"]), "GO")

    def test_fail_overrides_warn(self):
        self.assertEqual(self.compute(["FAIL", "WARN"]), "NO-GO")

    def test_multiple_warns_is_caution(self):
        self.assertEqual(self.compute(["WARN", "WARN"]), "PROCEED WITH CAUTION")

    def test_single_pass_is_go(self):
        self.assertEqual(self.compute(["PASS"]), "GO")

    def test_no_go_is_not_go(self):
        self.assertNotEqual(self.compute(["FAIL"]), "GO")


class TestDeploymentLabelAssignment(unittest.TestCase):
    """Tests label strings that match deployment_flow.yml Phase 5 Step 5.1."""
    def assign(self, verdict):
        if verdict == "GO": return "deployment::ready"
        if verdict == "NO-GO": return "deployment::blocked"
        return "deployment::caution"

    def test_go_maps_to_deployment_ready(self):
        self.assertEqual(self.assign("GO"), "deployment::ready")

    def test_no_go_maps_to_deployment_blocked(self):
        self.assertEqual(self.assign("NO-GO"), "deployment::blocked")

    def test_caution_maps_to_deployment_caution(self):
        self.assertEqual(self.assign("PROCEED WITH CAUTION"), "deployment::caution")

    def test_all_labels_use_deployment_namespace(self):
        for v in ["GO", "NO-GO", "PROCEED WITH CAUTION"]:
            self.assertTrue(self.assign(v).startswith("deployment::"))


class TestRollbackAdvisory(unittest.TestCase):
    """Tests rollback plan selection matching deployment_flow.yml Phase 4."""
    def needs_rollback_plan(self, verdict):
        # NO-GO and PROCEED WITH CAUTION both require rollback documentation
        return verdict in ["NO-GO", "PROCEED WITH CAUTION"]

    def test_no_go_requires_rollback(self):
        self.assertTrue(self.needs_rollback_plan("NO-GO"))

    def test_caution_requires_rollback(self):
        self.assertTrue(self.needs_rollback_plan("PROCEED WITH CAUTION"))

    def test_go_has_standard_rollback_only(self):
        self.assertFalse(self.needs_rollback_plan("GO"))

class TestProtectedBranchRouting(unittest.TestCase):
    def allow(self, branch, user_role): return branch != "main" or user_role == "maintainer"
    def test_1(self): self.assertTrue(self.allow("feature", "developer"))
    def test_2(self): self.assertFalse(self.allow("main", "developer"))
    def test_3(self): self.assertTrue(self.allow("main", "maintainer"))
    def test_4(self): self.assertTrue(self.allow("staging", "maintainer"))
    def test_5(self): self.assertFalse(self.allow("main", "guest"))
    def test_6(self): self.assertTrue(self.allow("test", "guest"))

class TestDeploymentReportFormat(unittest.TestCase):
    def format_report(self, v): return f"Verdict: {v}"
    def test_1(self): self.assertEqual(self.format_report("PASS"), "Verdict: PASS")
    def test_2(self): self.assertEqual(self.format_report("FAIL"), "Verdict: FAIL")
    def test_3(self): self.assertTrue("WARN" in self.format_report("WARN"))
    def test_4(self): self.assertFalse("PASS" in self.format_report("FAIL"))

class TestJobCategorisation(unittest.TestCase):
    def categorize(self, job): return "deploy" if "deploy" in job else "build"
    def test_1(self): self.assertEqual(self.categorize("deploy_prod"), "deploy")
    def test_2(self): self.assertEqual(self.categorize("build_prod"), "build")
    def test_3(self): self.assertEqual(self.categorize("deploy_staging"), "deploy")
    def test_4(self): self.assertEqual(self.categorize("test"), "build")
    def test_5(self): self.assertNotEqual(self.categorize("deploy_test"), "build")

if __name__ == "__main__":
    unittest.main()
