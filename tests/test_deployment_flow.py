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
    def get_signal(self, label): return "FAIL" if label == "compliance::fail" else "PASS"
    def test_1(self): self.assertEqual(self.get_signal("compliance::fail"), "FAIL")
    def test_2(self): self.assertEqual(self.get_signal("compliance::pass"), "PASS")
    def test_3(self): self.assertNotEqual(self.get_signal("compliance::fail"), "PASS")

class TestVerdictComputation(unittest.TestCase):
    def compute(self, signals):
        if "FAIL" in signals: return "ROLLBACK"
        if "WARN" in signals: return "REVIEW_REQUIRED"
        return "DEPLOY"
    def test_1(self): self.assertEqual(self.compute(["PASS", "FAIL"]), "ROLLBACK")
    def test_2(self): self.assertEqual(self.compute(["PASS", "WARN"]), "REVIEW_REQUIRED")
    def test_3(self): self.assertEqual(self.compute(["PASS", "PASS"]), "DEPLOY")
    def test_4(self): self.assertEqual(self.compute(["FAIL", "WARN"]), "ROLLBACK")
    def test_5(self): self.assertEqual(self.compute(["WARN", "WARN"]), "REVIEW_REQUIRED")
    def test_6(self): self.assertNotEqual(self.compute(["PASS"]), "ROLLBACK")
    def test_7(self): self.assertTrue(self.compute(["FAIL"]) == "ROLLBACK")

class TestDeploymentLabelAssignment(unittest.TestCase):
    def assign(self, verdict): return f"deploy::{verdict.lower()}"
    def test_1(self): self.assertEqual(self.assign("DEPLOY"), "deploy::deploy")
    def test_2(self): self.assertEqual(self.assign("ROLLBACK"), "deploy::rollback")
    def test_3(self): self.assertEqual(self.assign("REVIEW_REQUIRED"), "deploy::review_required")
    def test_4(self): self.assertTrue(self.assign("WAIT").startswith("deploy::"))

class TestRollbackAdvisory(unittest.TestCase):
    def advise(self, verdict): return verdict == "ROLLBACK"
    def test_1(self): self.assertTrue(self.advise("ROLLBACK"))
    def test_2(self): self.assertFalse(self.advise("DEPLOY"))
    def test_3(self): self.assertFalse(self.advise("REVIEW_REQUIRED"))

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
