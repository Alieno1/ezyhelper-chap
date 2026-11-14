"""Comprehensive Unit, Integration, Security, Edge-Case & Concurrency Test Suite for EzyHelpers CHAP.

Run from repository root:
    backend/.venv/bin/python -m unittest discover -s backend/tests -v
"""

import json
import os
import re
import sys
import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from unittest.mock import patch

# Isolate test suite onto a temporary SQLite database BEFORE importing backend modules
# so tests never touch or wipe the live Neon PostgreSQL database.
_TMP_DB = tempfile.NamedTemporaryFile(suffix=".sqlite", delete=False)
_TMP_DB.close()
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP_DB.name}"
os.environ["GEMINI_API_KEY"] = ""
os.environ["OPENROUTER_API_KEY"] = ""

BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

from fastapi.testclient import TestClient  # noqa: E402
from sqlalchemy import create_engine  # noqa: E402
from sqlalchemy.orm import sessionmaker  # noqa: E402

import agents  # noqa: E402
import database  # noqa: E402
import main  # noqa: E402
from models import Base  # noqa: E402

# Use a file-backed SQLite database with 30s busy timeout so each concurrent thread
# gets its own isolated connection while sharing the test database state.
TEST_ENGINE = create_engine(
    f"sqlite:///{_TMP_DB.name}",
    connect_args={"check_same_thread": False, "timeout": 30},
)
TestSessionLocal = sessionmaker(bind=TEST_ENGINE, autoflush=False, expire_on_commit=False)
Base.metadata.create_all(TEST_ENGINE)


def _override_get_db():
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


main.app.dependency_overrides[database.get_db] = _override_get_db
client = TestClient(main.app)


class Test01DeterministicParser(unittest.TestCase):
    """Unit tests for the rule-based regex & keyword extraction engine."""

    def test_all_10_curated_raw_profiles_parse_cleanly(self):
        for src, raw in agents.RAW_PROFILES:
            parsed = agents.deterministic_parse(raw, src)
            self.assertEqual(parsed["source_platform"], src)
            self.assertTrue(parsed["first_name"])
            self.assertRegex(parsed["mobile_number"], r"^\+91 \d{10}$")
            self.assertIn(parsed["gender"], ("Female", "Male"))
            self.assertIn(parsed["work_type"], ("Live In", "Full Time", "Part Time"))
            self.assertGreaterEqual(len(parsed["job_roles"]), 1)
            self.assertGreaterEqual(parsed["expected_salary_inr"], 10000)

    def test_rita_das_specific_attributes(self):
        src, raw = agents.RAW_PROFILES[0]
        p = agents.deterministic_parse(raw, src)
        self.assertEqual(p["first_name"], "Rita")
        self.assertEqual(p["last_name"], "Das")
        self.assertEqual(p["age"], 34)
        self.assertEqual(p["base_locality"], "Hsr Layout")
        self.assertEqual(p["base_city"], "Bangalore")
        self.assertIn("Cooking", p["job_roles"])
        self.assertIn("Housekeeping", p["job_roles"])
        self.assertIn("Bengali", p["languages_known"])
        self.assertIn("Sleep by 10:00 PM", p["special_preferences"])
        self.assertIn("Hygienic Environment", p["special_preferences"])
        self.assertNotIn("Non-Veg Cooking", p["tasks_donts"])

    def test_pure_veg_and_male_doctor_detection(self):
        # Sunita Devi: pure veg
        src_veg, raw_veg = agents.RAW_PROFILES[1]
        p_veg = agents.deterministic_parse(raw_veg, src_veg)
        self.assertIn("Non-Veg Cooking", p_veg["tasks_donts"])
        self.assertEqual(p_veg["work_type"], "Part Time")

        # Dr. Anil Kumar: male physiotherapist, honorific stripped
        src_doc, raw_doc = agents.RAW_PROFILES[6]
        p_doc = agents.deterministic_parse(raw_doc, src_doc)
        self.assertEqual(p_doc["first_name"], "Anil")
        self.assertEqual(p_doc["gender"], "Male")
        self.assertIn("Physiotherapist", p_doc["job_roles"])
        self.assertIn("Elderly Care", p_doc["job_roles"])

    def test_minimal_and_empty_bio_defaults(self):
        p = agents.deterministic_parse("", "Apna")
        self.assertEqual(p["first_name"], "Helper")
        self.assertEqual(p["mobile_number"], "+91 9000000000")
        self.assertEqual(p["job_roles"], ["Housekeeping"])
        self.assertEqual(p["languages_known"], ["Hindi"])
        self.assertEqual(p["expected_salary_inr"], 18000)


class Test02LLMParserAndNormalization(unittest.TestCase):
    """Unit tests for LLM overlay, fallback resilience, and enum normalization."""

    def test_fallback_when_no_api_keys(self):
        src, raw = agents.RAW_PROFILES[0]
        base = agents.deterministic_parse(raw, src)
        merged, provider = agents.gemini_parse(raw, src, base)
        self.assertEqual(provider, "deterministic")
        self.assertEqual(merged, base)

    def test_normalization_of_nonstandard_llm_outputs(self):
        src, raw = agents.RAW_PROFILES[0]
        base = agents.deterministic_parse(raw, src)
        fake_llm_json = json.dumps({
            "gender": "  female ",
            "work_type": "live in",
            "citizenship": "nepal",
            "app_language": "bengali",
            "job_roles": ["cooking", "DRIVER_INVALID", "baby care"],
            "mobile_number": "+91 0000000000",  # Must NOT override base mobile_number
        })

        class _FakeResp:
            def __enter__(self):
                return self

            def __exit__(self, *args):
                pass

            def read(self):
                return json.dumps({"choices": [{"message": {"content": f"```json\n{fake_llm_json}\n```"}}]}).encode()

        with patch.dict(os.environ, {"OPENROUTER_API_KEY": "test-key"}), \
                patch("urllib.request.urlopen", return_value=_FakeResp()):
            merged, provider = agents.gemini_parse("raw bio", "Apna", base)

        self.assertEqual(provider, "openrouter")
        self.assertEqual(merged["gender"], "Female")
        self.assertEqual(merged["work_type"], "Live In")
        self.assertEqual(merged["citizenship"], "Nepal")
        self.assertEqual(merged["app_language"], "Bengali")
        self.assertEqual(merged["job_roles"], ["Cooking", "Baby Care"])
        self.assertEqual(merged["mobile_number"], base["mobile_number"])


class Test03PipelineAndEndpoints(unittest.TestCase):
    """End-to-end integration tests for Manual and Autopilot pipeline modes."""

    def test_01_health_endpoint(self):
        r = client.get("/api/health")
        self.assertEqual(r.status_code, 200)
        body = r.json()
        self.assertEqual(body["status"], "ok")
        self.assertIn(body["database"], ("sqlite", "postgresql"))

    def test_02_manual_pipeline_creates_80_pct_profiles(self):
        r = client.post("/api/agent/run-sourcing-pipeline?autopilot=false")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data["stages"]), 4)
        self.assertEqual(len(data["helper_ids"]), 10)

        helpers = client.get("/api/helpers").json()
        self.assertEqual(len(helpers), 10)
        for h in helpers:
            self.assertEqual(h["profile_completion_pct"], 80)
            self.assertFalse(h["kyc_blue_tick"])
            self.assertEqual(h["fo_verification_status"], "Not_Assigned")

    def test_03_manual_kyc_and_fo_step_by_step(self):
        helpers = client.get("/api/helpers").json()
        blr_helper = next(h for h in helpers if h["base_city"] == "Bangalore")
        non_blr_helper = next(h for h in helpers if h["base_city"] != "Bangalore")

        # Verify KYC idempotency (calling 3 times keeps score <= 100)
        for _ in range(3):
            rk = client.post(f"/api/agent/verify-kyc/{blr_helper['helper_id']}")
            self.assertEqual(rk.status_code, 200)
            body = rk.json()
            self.assertTrue(body["kyc_blue_tick"])
            self.assertEqual(body["kyc_masked_id"], "[Aadhaar Redacted]")
            self.assertLessEqual(body["profile_quality_score"], 100)
            self.assertGreaterEqual(body["profile_completion_pct"], 95)

        # Assign Field Officer to Bangalore helper -> 200 OK
        rf = client.post(f"/api/agent/assign-field-officer/{blr_helper['helper_id']}")
        self.assertEqual(rf.status_code, 200)
        fbody = rf.json()
        self.assertEqual(fbody["fo_verification_status"], "Geo_Verified")
        self.assertEqual(fbody["fo_assigned_name"], "Client (FO - Bangalore South)")
        self.assertEqual(fbody["profile_completion_pct"], 100)
        self.assertEqual(fbody["onboarding_stage"], "FO_GEO_VERIFIED")

        # Calling verify-kyc after FO_GEO_VERIFIED must not downgrade onboarding_stage
        rk_after = client.post(f"/api/agent/verify-kyc/{blr_helper['helper_id']}").json()
        self.assertEqual(rk_after["onboarding_stage"], "FO_GEO_VERIFIED")

        # Assign Field Officer to non-Bangalore helper -> 400 Bad Request
        rf_bad = client.post(f"/api/agent/assign-field-officer/{non_blr_helper['helper_id']}")
        self.assertEqual(rf_bad.status_code, 400)
        self.assertIn("Bangalore", rf_bad.json()["detail"])

    def test_04_autopilot_pipeline_completes_all_6_stages(self):
        r = client.post("/api/agent/run-sourcing-pipeline?autopilot=true")
        self.assertEqual(r.status_code, 200)
        data = r.json()
        self.assertEqual(len(data["stages"]), 6)
        self.assertEqual(len(data["helper_ids"]), 10)

        # Campaign CAC math assertions
        c = client.get("/api/campaign").json()
        self.assertAlmostEqual(
            c["cost_per_raw_lead_inr"],
            c["subscription_spend_inr"] / c["profiles_scraped_count"],
        )
        self.assertAlmostEqual(
            c["cost_per_active_lead_inr"],
            c["subscription_spend_inr"] / c["whatsapp_active_yes_count"],
        )
        self.assertAlmostEqual(
            c["final_cac_per_onboarded_helper_inr"],
            c["subscription_spend_inr"] / c["bangalore_converted_count"],
        )

        helpers = client.get("/api/helpers").json()
        blr = [h for h in helpers if h["base_city"] == "Bangalore"]
        non_blr = [h for h in helpers if h["base_city"] != "Bangalore"]
        self.assertEqual(len(blr), 7)
        self.assertEqual(len(non_blr), 3)

        for h in helpers:
            self.assertTrue(h["kyc_blue_tick"])
            self.assertEqual(h["kyc_masked_id"], "[Aadhaar Redacted]")
            wa = client.get(f"/api/helpers/{h['helper_id']}/whatsapp")
            self.assertEqual(wa.status_code, 200)
            self.assertGreaterEqual(len(wa.json()), 5)

        for h in blr:
            self.assertEqual(h["fo_verification_status"], "Geo_Verified")
            self.assertEqual(h["fo_assigned_name"], "Client (FO - Bangalore South)")
            self.assertEqual(h["profile_completion_pct"], 100)

        for h in non_blr:
            self.assertIsNone(h["fo_assigned_name"])
            self.assertEqual(h["fo_verification_status"], "Not_Assigned")


class Test04PropensityMatcherAndEdgeCases(unittest.TestCase):
    """Tests for the 0-100% customer propensity matcher and input validation."""

    @classmethod
    def setUpClass(cls):
        client.post("/api/agent/run-sourcing-pipeline?autopilot=true")

    def test_bengali_nonveg_cook_hsr_ranks_rita_das_first(self):
        r = client.post("/api/agent/match-customer", json={
            "text": "Bengali family in HSR Layout looking for Full-Time Cook + Housekeeping, must cook fish/non-veg, sleep by 10 PM, hygienic, budget ₹25,000",
            "locality": "HSR Layout",
            "roles": ["Cooking", "Housekeeping"],
            "languages": ["Bengali"],
            "work_type": "Full Time",
            "budget_inr": 25000,
            "must_cook_nonveg": True,
            "sleep_by_10pm": True,
            "hygienic": True,
        })
        self.assertEqual(r.status_code, 200)
        results = r.json()
        self.assertEqual(len(results), 10)
        self.assertEqual(results[0]["name"], "Rita Das")
        self.assertGreaterEqual(results[0]["score"], 95)
        self.assertEqual(results[0]["recommendation"], "Strong match — shortlist now.")

        sunita = next(x for x in results if x["name"] == "Sunita Devi")
        self.assertTrue(any("Pure Veg" in t for t in sunita["tradeoffs"]))

    def test_invalid_inputs_rejected_with_422(self):
        invalid_payloads = [
            {},
            {"text": "ab"},
            {"text": "need cook", "roles": ["Driver"]},
            {"text": "need cook", "work_type": "Night Shift"},
            {"text": "need cook", "budget_inr": "twenty thousand"},
            {"text": "need cook", "budget_inr": 0},
            {"text": "need cook", "budget_inr": -5000},
        ]
        for body in invalid_payloads:
            with self.subTest(body=body):
                r = client.post("/api/agent/match-customer", json=body)
                self.assertEqual(r.status_code, 422)

    def test_extreme_and_adversarial_inputs_handled_safely(self):
        edge_payloads = [
            {"text": "need cook", "budget_inr": 10**9},
            {"text": "मुझे खाना बनाने वाली चाहिए HSR layout ₹20,000"},
            {"text": "🍛🧹👶" * 300},
            {"text": "cook non veg fish hsr layout " * 2000},
            {"text": "<script>alert('xss')</script> full time cook"},
            {"text": "need helper in Mars Colony, budget ₹18,000"},
        ]
        for body in edge_payloads:
            with self.subTest(text=body["text"][:30]):
                r = client.post("/api/agent/match-customer", json=body)
                self.assertEqual(r.status_code, 200)
                res = r.json()
                self.assertEqual(len(res), 10)
                self.assertTrue(all(0 <= x["score"] <= 100 for x in res))
                self.assertEqual(res, sorted(res, key=lambda x: x["score"], reverse=True))


class Test05SecurityComplianceAndConcurrency(unittest.TestCase):
    """UIDAI compliance, naming hygiene, SQL injection resilience & concurrency stress."""

    def test_no_raw_aadhaar_or_ankit_name_anywhere(self):
        client.post("/api/agent/run-sourcing-pipeline?autopilot=true")
        helpers = client.get("/api/helpers").json()
        blob = json.dumps(helpers)
        self.assertIsNone(re.search(r"\b\d{4}\s?\d{4}\s?\d{4}\b", blob))
        self.assertNotIn("ankit", blob.lower())

        for h in helpers:
            wa_text = client.get(f"/api/helpers/{h['helper_id']}/whatsapp").text
            self.assertNotIn("ankit", wa_text.lower())

    def test_404_and_sql_injection_safety(self):
        for bad_id in ("HLPRIN00000", "DOES_NOT_EXIST", "' OR 1=1 --", "'; DROP TABLE helpers; --"):
            self.assertEqual(client.get(f"/api/helpers/{bad_id}").status_code, 404)
            self.assertEqual(client.get(f"/api/helpers/{bad_id}/whatsapp").status_code, 404)
            self.assertEqual(client.post(f"/api/agent/verify-kyc/{bad_id}").status_code, 404)
            self.assertEqual(client.post(f"/api/agent/assign-field-officer/{bad_id}").status_code, 404)
        # Ensure all 10 helpers remain intact
        self.assertEqual(len(client.get("/api/helpers").json()), 10)

    def test_concurrent_pipeline_runs_and_parallel_reads(self):
        with ThreadPoolExecutor(max_workers=5) as ex:
            statuses = list(ex.map(
                lambda _: client.post("/api/agent/run-sourcing-pipeline?autopilot=true").status_code,
                range(5),
            ))
        self.assertEqual(statuses, [200, 200, 200, 200, 200])

        helpers = client.get("/api/helpers").json()
        self.assertEqual(len(helpers), 10)
        self.assertEqual(len({h["helper_id"] for h in helpers}), 10)
        self.assertEqual(len({h["mobile_number"] for h in helpers}), 10)

        with ThreadPoolExecutor(max_workers=10) as ex:
            read_statuses = list(ex.map(
                lambda _: client.get("/api/helpers").status_code,
                range(50),
            ))
        self.assertTrue(all(s == 200 for s in read_statuses))


if __name__ == "__main__":
    unittest.main(verbosity=2)
