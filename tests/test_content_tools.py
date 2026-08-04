from __future__ import annotations

import csv
import json
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

import normalize_content_pool as normalize  # noqa: E402
import rank_content_candidates as rank  # noqa: E402


class NormalizeContentPoolTests(unittest.TestCase):
    def test_parse_number_supports_social_suffixes_and_missing_values(self) -> None:
        self.assertEqual(normalize.parse_number("12.5K"), 12_500)
        self.assertEqual(normalize.parse_number("1.2M"), 1_200_000)
        self.assertEqual(normalize.parse_number("2.5万"), 25_000)
        self.assertAlmostEqual(normalize.parse_number("3.5%"), 0.035)
        self.assertIsNone(normalize.parse_number("—"))
        self.assertIsNone(normalize.parse_number("not visible"))

    def test_canonicalize_url_removes_tracking_but_keeps_access_parameters(self) -> None:
        value = "https://Example.COM/post/123/?utm_source=test&page=2&session=private&share_id=drop#comments"
        self.assertEqual(
            normalize.canonicalize_url(value),
            "https://example.com/post/123?page=2",
        )

    def test_deduplication_prefers_latest_snapshot_and_fills_blanks(self) -> None:
        raw = [
            {
                "Channel": "IG Reels",
                "Post URL": "https://example.com/p/1?utm_source=old",
                "Observed At": "2026-01-01",
                "Views": "1K",
                "Hook": "A concrete problem",
                "Custom Field": "preserved",
            },
            {
                "Platform": "Instagram",
                "Content URL": "https://example.com/p/1",
                "Observed At": "2026-01-03",
                "Views": "1.5K",
                "Likes": "100",
            },
        ]
        records = normalize.normalize_records(raw)
        self.assertEqual(len(records), 1)
        record = records[0]
        self.assertEqual(record["views"], 1500)
        self.assertEqual(record["hook"], "A concrete problem")
        self.assertEqual(record["duplicate_count"], 2)
        self.assertEqual(record["source_record_indices"], "1;2")
        self.assertEqual(json.loads(record["extra_json"])["custom_field"], "preserved")

    def test_deduplication_does_not_mix_metrics_from_older_snapshot(self) -> None:
        raw = [
            {
                "platform": "TikTok",
                "content_url": "https://example.com/p/2",
                "observed_at": "2026-01-01",
                "followers": "900",
                "views": "1K",
            },
            {
                "platform": "TikTok",
                "content_url": "https://example.com/p/2",
                "observed_at": "2026-01-03",
                "views": "2K",
            },
        ]
        record = normalize.normalize_records(raw)[0]
        self.assertEqual(record["views"], 2000)
        self.assertEqual(record["followers"], "")
        self.assertIn("older_snapshot_followers_not_merged", record["normalization_warnings"])

    def test_missing_metric_stays_blank(self) -> None:
        record = normalize.normalize_records(
            [{"platform": "TikTok", "content_url": "https://example.com/1", "views": "hidden"}]
        )[0]
        self.assertEqual(record["views"], "")
        self.assertIn("unparsed_views", record["normalization_warnings"])


class RankContentCandidatesTests(unittest.TestCase):
    @staticmethod
    def make_record(index: int, views: int, risk: str = "low") -> dict[str, str]:
        return {
            "content_id": f"c{index}",
            "platform": "tiktok",
            "source_type": "creator",
            "account_name": "sample-account",
            "content_url": f"https://example.com/{index}",
            "observed_at": "2026-01-05",
            "followers": "100",
            "views": str(views),
            "likes": "10",
            "comments": "10",
            "saves": "2",
            "shares": "1",
            "intent_signal_count": "2",
            "hook": "A specific user moment",
            "content_angle": "problem first",
            "relevance_score": "5",
            "transferability_score": "4",
            "risk_level": risk,
        }

    def test_account_baseline_and_outlier_tier(self) -> None:
        records = [self.make_record(index, views) for index, views in enumerate([100, 100, 100, 100, 500], 1)]
        enriched = rank.enrich_records(records)
        outlier = next(item for item in enriched if item["content_id"] == "c5")
        self.assertEqual(outlier["account_sample_size"], 5)
        self.assertEqual(outlier["account_median_views"], "100")
        self.assertEqual(outlier["view_index"], "5")
        self.assertEqual(outlier["performance_tier"], "strong_outlier")
        self.assertEqual(outlier["score_performance"], "5")
        self.assertEqual(outlier["priority_confidence"], "high")

    def test_missing_strategic_evidence_does_not_become_zero_score(self) -> None:
        record = {
            "content_id": "missing",
            "platform": "unknown",
            "source_type": "unknown",
            "content_url": "https://example.com/missing",
            "risk_level": "unknown",
        }
        enriched = rank.enrich_records([record])[0]
        self.assertEqual(enriched["score_performance"], "")
        self.assertEqual(enriched["score_intent"], "")
        self.assertEqual(enriched["priority_score"], "")
        self.assertEqual(enriched["priority_confidence"], "low")
        self.assertIn("no_strategic_score_components", enriched["ranking_warnings"])

    def test_high_risk_applies_fifteen_point_penalty(self) -> None:
        low = self.make_record(1, 1_000, "low")
        high = self.make_record(2, 1_000, "high")
        low["account_name"] = "single-low"
        high["account_name"] = "single-high"
        enriched = {item["content_id"]: item for item in rank.enrich_records([low, high])}
        low_score = float(enriched["c1"]["priority_score"])
        high_score = float(enriched["c2"]["priority_score"])
        self.assertAlmostEqual(low_score - high_score, 15.0, places=2)

    def test_cli_round_trip_writes_ranked_csv(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            raw_path = root / "raw.json"
            normalized_path = root / "normalized.csv"
            ranked_path = root / "ranked.csv"
            raw_path.write_text(
                json.dumps(
                    [
                        {
                            "platform": "TikTok",
                            "url": "https://example.com/post/1?utm_campaign=test",
                            "account": "creator-a",
                            "observed_at": "2026-01-05",
                            "followers": "500",
                            "views": "5K",
                            "comments": "20",
                            "intent_comments": "4",
                            "hook": "A real user problem",
                            "angle": "problem first",
                            "relevance_score": "5",
                            "reuse_score": "4",
                            "risk": "low",
                        }
                    ]
                ),
                encoding="utf-8",
            )
            self.assertEqual(normalize.main(["--input", str(raw_path), "--output", str(normalized_path)]), 0)
            self.assertEqual(rank.main(["--input", str(normalized_path), "--output", str(ranked_path)]), 0)
            with ranked_path.open("r", encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]["canonical_url"], "https://example.com/post/1")
            self.assertTrue(rows[0]["priority_score"])
            self.assertIn(rows[0]["priority_confidence"], {"low", "medium", "high"})


if __name__ == "__main__":
    unittest.main()
