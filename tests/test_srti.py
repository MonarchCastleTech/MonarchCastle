from __future__ import annotations

import importlib.util
import sys
import unittest
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

import generate_pages


def load_pipeline():
    path = ROOT / "Sahel Region Threat Index (SRTI)" / "sahel_watch.py"
    spec = importlib.util.spec_from_file_location("sahel_watch", path)
    module = importlib.util.module_from_spec(spec)
    assert spec and spec.loader
    spec.loader.exec_module(module)
    return module


pipeline = load_pipeline()


class PipelineTests(unittest.TestCase):
    def test_country_terms_do_not_match_other_country_names(self):
        self.assertNotIn("niger", pipeline.region_match("violence reported in nigeria"))
        self.assertNotIn("mali", pipeline.region_match("somali piracy update"))
        self.assertEqual(pipeline.region_match("Mali and Niger security update"), ["mali", "niger"])

    def test_iso_timestamp_parser_preserves_utc(self):
        parsed = pipeline.parse_datetime("2026-08-30T10:15:00Z")
        self.assertEqual(parsed, datetime(2026, 8, 30, 10, 15, tzinfo=timezone.utc))

    def test_quality_gate_passes_only_with_transport_and_region_coverage(self):
        healthy = [
            {"status": "ok", "regions": ["mali"], "eligible_items": 1},
            {"status": "ok", "regions": ["niger"], "eligible_items": 1},
            {"status": "ok", "regions": [], "eligible_items": 1},
            {"status": "ok", "regions": [], "eligible_items": 0},
        ]
        self.assertTrue(pipeline.evaluate_quality_gate(healthy, 3)["passed"])
        self.assertFalse(pipeline.evaluate_quality_gate(healthy[:2], 3)["passed"])
        self.assertFalse(pipeline.evaluate_quality_gate(healthy, 0)["passed"])

    def test_unsafe_urls_are_discarded(self):
        self.assertEqual(pipeline.safe_http_url("javascript:alert(1)"), "")
        self.assertEqual(pipeline.safe_http_url("https://example.com/report"), "https://example.com/report")


class RenderTests(unittest.TestCase):
    def sample(self):
        timestamp = "2026-08-30T10:00:00+00:00"
        latest = {
            "schema_version": 2,
            "methodology_version": "2.0",
            "fetched_at": timestamp,
            "content_latest_at": timestamp,
            "window_hours": 72,
            "score": 22.5,
            "risk_level": "GUARDED",
            "components": {"conflict_intensity": 20.0, "civilian_risk": 27.0},
            "weights": {"conflict_intensity": 0.7143, "civilian_risk": 0.2857},
            "items_count": 1,
            "items_evaluated": 4,
            "sources": [{"name": "Source", "url": "https://example.com/feed", "status": "ok", "items": 4, "eligible_items": 3, "regions": ["mali"]}],
            "top_headlines": [{"title": "<script>alert(1)</script>", "link": "javascript:alert(1)", "source": "Source", "published_at": timestamp, "score": 1.2, "tags": ["civilian_risk"], "regions": ["mali"]}],
            "quality_gate": {"passed": True, "reachable_sources": 4, "total_sources": 4, "covered_regions": ["mali", "niger"], "dated_items": 3, "criteria": {"minimum_reachable_sources": 4, "minimum_target_countries": 2, "minimum_dated_items": 3}},
        }
        history = [
            {"timestamp": "2026-08-30T09:00:00+00:00", "score": 20.0},
            {"timestamp": timestamp, "score": 22.5},
        ]
        return latest, history

    def test_operator_page_escapes_feed_content_and_unsupported_links(self):
        latest, history = self.sample()
        markup = generate_pages.render_srti_operator_html(latest, history, "assets", "data")
        self.assertIn("&lt;script&gt;alert(1)&lt;/script&gt;", markup)
        self.assertNotIn("javascript:alert", markup)
        self.assertNotIn("Commercial Access", markup)
        self.assertNotIn("Sources Live", markup)
        self.assertIn("SRTI / PUBLIC OSINT MONITOR", markup)


if __name__ == "__main__":
    unittest.main()
