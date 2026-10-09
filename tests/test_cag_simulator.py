"""
Comprehensive Regression Test Suite for CAG Sales Roleplay Simulator.
Tests cover:
1. Missing credentials handling and offline initialization.
2. Google API permission failures (HTTP 403 / PERMISSION_DENIED) and diagnostic parsing.
3. Offline fallback execution and multi-rule objection cross-referencing.
4. Provider-side vs Local In-Memory cache-status labeling.
5. Secret hygiene: ensuring no secrets/keys are exposed in diagnostics or metadata.
6. Sales manual token threshold verification for Google Context Caching.
"""

import os
import unittest
from unittest.mock import MagicMock, patch

import app
from app import (
    CAGCacheSnapshotManager,
    SimulatedCAGManager,
    DEFAULT_MODEL,
    MIN_CACHE_TOKENS,
    MANUAL_FILE_PATH,
    CACHE_DISPLAY_NAME,
)


class TestCAGSimulatorCredentialsAndPermissions(unittest.TestCase):
    """Tests for credential management, permission failures, and diagnostic categorization."""

    def test_missing_credentials_fallback(self):
        """When no API key is provided, live manager reports unconfigured and fallback works."""
        # Case 1: Explicit empty string
        manager_empty = CAGCacheSnapshotManager(api_key="")
        self.assertFalse(manager_empty.is_configured())
        self.assertIsNone(manager_empty.active_cache)

        with self.assertRaises(RuntimeError) as ctx:
            manager_empty.get_or_create_cache()
        self.assertIn("not configured", str(ctx.exception).lower())

        # Case 2: Clean environment with no env variables
        with patch.dict(os.environ, {}, clear=True):
            manager_no_env = CAGCacheSnapshotManager(api_key=None)
            self.assertFalse(manager_no_env.is_configured())

        # Local simulation engine operates independently
        sim = SimulatedCAGManager()
        meta = sim.get_cache_metadata()
        self.assertEqual(meta["mode"], "OFFLINE_SIMULATION")
        self.assertEqual(meta["status"], "LOCAL_IN_MEMORY")

    def test_permission_denied_http_403_diagnostic(self):
        """When Google API returns 403, error category is preserved and actionable steps provided."""
        manager = CAGCacheSnapshotManager(api_key="test-dummy-key")
        raw_error = Exception("403 PERMISSION_DENIED: {'error': {'code': 403, 'message': 'Your project has been denied access.'}}")

        diag = manager.parse_api_error(raw_error)

        # Category is preserved as PERMISSION_DENIED (HTTP 403)
        self.assertEqual(diag["category"], "PERMISSION_DENIED (HTTP 403)")
        self.assertTrue(diag["is_permission_error"])
        self.assertTrue(manager.is_restricted)
        self.assertFalse(manager.is_configured())

        # Actionable steps must be present
        steps = diag["steps"]
        self.assertGreaterEqual(len(steps), 3)
        steps_text = " ".join(steps).lower()
        self.assertIn("restrictions", steps_text)
        self.assertIn("generative language api", steps_text)
        self.assertIn("iam", steps_text)

        # Secret hygiene: raw key must never be leaked in diagnostic
        self.assertNotIn("test-dummy-key", diag["message"])
        self.assertNotIn("test-dummy-key", str(diag["steps"]))

    def test_not_found_http_404_diagnostic(self):
        """Verify 404 error parsing preserves NOT_FOUND category."""
        manager = CAGCacheSnapshotManager(api_key="test-dummy-key")
        raw_error = Exception("404 NOT_FOUND: model models/gemini-2.5-flash not found")
        diag = manager.parse_api_error(raw_error)

        self.assertEqual(diag["category"], "NOT_FOUND (HTTP 404)")
        self.assertFalse(diag["is_permission_error"])
        self.assertIn("gemini-3.8-flash", " ".join(diag["steps"]))

    def test_quota_exhausted_http_429_diagnostic(self):
        """Verify 429 quota exhaustion is properly mapped."""
        manager = CAGCacheSnapshotManager(api_key="test-dummy-key")
        raw_error = Exception("429 RESOURCE_EXHAUSTED: Quota exceeded for quota metric")
        diag = manager.parse_api_error(raw_error)

        self.assertEqual(diag["category"], "RESOURCE_EXHAUSTED (HTTP 429)")
        self.assertIn("quota", diag["message"].lower())


class TestCAGCacheStatusLabeling(unittest.TestCase):
    """Tests verifying clear distinction between provider cache and local in-memory processing."""

    def test_labeling_distinction(self):
        """Application strictly distinguishes Local In-Memory from Google Cloud Context Cache."""
        sim = SimulatedCAGManager()
        sim_meta = sim.get_cache_metadata()

        # Local must NEVER be labeled as provider-side persistent cache
        self.assertEqual(sim_meta["mode"], "OFFLINE_SIMULATION")
        self.assertEqual(sim_meta["status"], "LOCAL_IN_MEMORY")
        self.assertEqual(sim_meta["model"], "Local In-Memory Engine")
        self.assertIn("In-Memory", sim_meta["display_name"])

        # Live manager metadata reflects provider caching
        live = CAGCacheSnapshotManager(api_key="dummy")
        live.active_cache = MagicMock(name="cache-123")
        live.cache_id = "projects/123/locations/us/cachedContents/cag-001"
        live_meta = live.get_cache_metadata()

        self.assertEqual(live_meta["mode"], "LIVE_GOOGLE_CAG")
        self.assertEqual(live_meta["status"], "ACTIVE_PERSISTENT")
        self.assertEqual(live_meta["model"], DEFAULT_MODEL)

    def test_sync_cache_reindexing(self):
        """Local reload_cache successfully refreshes in-memory manual representation."""
        sim = SimulatedCAGManager()
        result = sim.reload_cache()
        self.assertGreaterEqual(result["cached_tokens"], MIN_CACHE_TOKENS)


class TestArthurObjectionCrossReferencing(unittest.TestCase):
    """Tests verifying Arthur Pendelton's deterministic cross-referencing against the manual."""

    def setUp(self):
        self.sim = SimulatedCAGManager()

    def test_monthly_starter_objection(self):
        history = [{"role": "user", "content": "You can buy our Starter tier for $49/mo on a month-to-month plan."}]
        reply, latency = self.sim.generate_response(history)
        self.assertGreater(latency, 0.0)
        self.assertIn("ApexLaunch", reply)
        self.assertIn("$588", reply)
        self.assertIn("NO monthly billing", reply)

    def test_native_payroll_objection(self):
        history = [{"role": "user", "content": "ApexERP includes free native payroll for all your warehouse staff."}]
        reply, latency = self.sim.generate_response(history)
        self.assertGreater(latency, 0.0)
        self.assertIn("NO NATIVE PAYROLL", reply)
        self.assertIn("Gusto", reply)
        self.assertIn("$4.00", reply)

    def test_waive_onboarding_objection(self):
        history = [{"role": "user", "content": "I will waive the $2,500 onboarding fee for the Pro tier today."}]
        reply, latency = self.sim.generate_response(history)
        self.assertGreater(latency, 0.0)
        self.assertIn("$2,500", reply)
        self.assertIn("mandatory", reply.lower())

    def test_unauthorized_discount_objection(self):
        history = [{"role": "user", "content": "I will give you a 35% discount off the Pro tier right now!"}]
        reply, latency = self.sim.generate_response(history)
        self.assertGreater(latency, 0.0)
        self.assertIn("35%", reply)
        self.assertIn("10% maximum discount", reply)
        self.assertIn("CFO", reply)


class TestSalesManualSpecification(unittest.TestCase):
    """Verifies knowledge base meets Google Context Caching requirements."""

    def test_manual_exists_and_exceeds_min_tokens(self):
        self.assertTrue(os.path.exists(MANUAL_FILE_PATH))
        with open(MANUAL_FILE_PATH, "r", encoding="utf-8") as f:
            content = f.read()

        # Token approximation (roughly 4 chars per token)
        approx_tokens = len(content) // 4
        self.assertGreater(approx_tokens, MIN_CACHE_TOKENS,
                           f"Manual has ~{approx_tokens} tokens; must exceed {MIN_CACHE_TOKENS} for Context Caching.")


if __name__ == "__main__":
    unittest.main()
