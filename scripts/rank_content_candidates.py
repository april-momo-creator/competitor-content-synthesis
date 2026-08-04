#!/usr/bin/env python3
"""Add transparent comparison metrics and evidence-aware priority scores."""

from __future__ import annotations

import argparse
import csv
import json
import statistics
from collections import defaultdict
from pathlib import Path
from typing import Any

from normalize_content_pool import parse_number


DERIVED_FIELDS = [
    "account_sample_size",
    "account_median_views",
    "view_index",
    "views_followers_ratio",
    "engagement_rate",
    "engagement_components_count",
    "intent_rate",
    "performance_tier",
    "score_performance",
    "score_intent",
    "score_relevance",
    "score_transferability",
    "score_completeness",
    "score_coverage",
    "risk_penalty",
    "priority_score",
    "priority_confidence",
    "ranking_warnings",
]

WEIGHTS = {
    "performance": 0.35,
    "intent": 0.20,
    "relevance": 0.20,
    "transferability": 0.15,
    "completeness": 0.10,
}

ESSENTIAL_FIELDS = (
    "platform",
    "content_url",
    "source_type",
    "account_name",
    "observed_at",
    "views",
    "hook",
    "content_angle",
    "risk_level",
)


def read_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        if not reader.fieldnames:
            raise ValueError("Input CSV has no header.")
        return list(reader.fieldnames), [dict(row) for row in reader]


def fmt(value: float | int | None, digits: int = 4) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return str(value)
    return f"{value:.{digits}f}".rstrip("0").rstrip(".")


def score_from_thresholds(value: float | None, thresholds: list[tuple[float, float]]) -> float | None:
    if value is None:
        return None
    for threshold, score in thresholds:
        if value >= threshold:
            return score
    return 1.0


def performance_score(view_index: float | None, ratio: float | None) -> float | None:
    scores = [
        score_from_thresholds(view_index, [(5, 5), (3, 4), (1.5, 3), (1, 2)]),
        score_from_thresholds(ratio, [(10, 5), (3, 4), (1, 3), (0.3, 2)]),
    ]
    available = [score for score in scores if score is not None]
    return max(available) if available else None


def intent_score(intent_count: float | None, comments: float | None) -> tuple[float | None, float | None]:
    if intent_count is None:
        return None, None
    if comments is not None and comments > 0:
        rate = intent_count / comments
        score = score_from_thresholds(rate, [(0.2, 5), (0.1, 4), (0.03, 3), (0.000001, 2)])
        return score if score is not None else 0.0, rate
    if intent_count > 0:
        return 2.0, None
    return 0.0, None


def performance_tier(view_index: float | None, ratio: float | None) -> str:
    if view_index is not None:
        if view_index >= 5:
            return "strong_outlier"
        if view_index >= 3:
            return "outlier"
        if view_index >= 1.5:
            return "above_baseline"
        if view_index >= 0.75:
            return "baseline_range"
        return "below_baseline"
    if ratio is not None:
        if ratio >= 10:
            return "strong_low_follower_breakout"
        if ratio >= 3:
            return "low_follower_breakout"
        if ratio >= 1:
            return "beyond_follower_base"
        return "no_account_baseline"
    return "insufficient_data"


def normalized_manual_score(value: Any) -> float | None:
    parsed = parse_number(value)
    if parsed is None or parsed < 0 or parsed > 5:
        return None
    return float(parsed)


def risk_penalty(value: Any) -> float:
    return {"low": 0.0, "medium": 5.0, "high": 15.0, "unknown": 0.0}.get(
        str(value or "unknown").strip().lower(), 0.0
    )


def data_completeness(record: dict[str, Any]) -> float:
    present = 0
    for field in ESSENTIAL_FIELDS:
        value = str(record.get(field) or "").strip()
        if not value:
            continue
        if field in {"platform", "source_type", "risk_level"} and value.lower() == "unknown":
            continue
        present += 1
    return present / len(ESSENTIAL_FIELDS)


def baseline_groups(records: list[dict[str, str]]) -> dict[tuple[str, str, str], list[float]]:
    groups: dict[tuple[str, str, str], list[float]] = defaultdict(list)
    for record in records:
        platform = str(record.get("platform") or "unknown").strip().lower()
        account = str(record.get("account_name") or "").strip().lower()
        baseline_group = str(record.get("baseline_group") or "").strip().lower()
        views = parse_number(record.get("views"))
        if account and views is not None and views >= 0:
            groups[(platform, account, baseline_group)].append(float(views))
    return groups


def enrich_records(records: list[dict[str, str]]) -> list[dict[str, Any]]:
    groups = baseline_groups(records)
    enriched: list[dict[str, Any]] = []

    for record in records:
        output: dict[str, Any] = dict(record)
        warnings: list[str] = []
        platform = str(record.get("platform") or "unknown").strip().lower()
        account = str(record.get("account_name") or "").strip().lower()
        baseline_group = str(record.get("baseline_group") or "").strip().lower()
        group = groups.get((platform, account, baseline_group), [])
        sample_size = len(group)
        median_views = statistics.median(group) if sample_size >= 5 else None

        views = parse_number(record.get("views"))
        followers = parse_number(record.get("followers"))
        likes = parse_number(record.get("likes"))
        comments = parse_number(record.get("comments"))
        saves = parse_number(record.get("saves"))
        shares = parse_number(record.get("shares"))
        intent_count = parse_number(record.get("intent_signal_count"))

        view_index = None
        if views is not None and median_views not in (None, 0):
            view_index = float(views) / float(median_views)
        elif sample_size and sample_size < 5:
            warnings.append("account_baseline_requires_5_records")

        ratio = None
        if views is not None and followers is not None and followers > 0:
            ratio = float(views) / float(followers)

        engagement_values = [item for item in (likes, comments, saves, shares) if item is not None]
        engagement_rate = None
        if views is not None and views > 0 and engagement_values:
            engagement_rate = sum(float(item) for item in engagement_values) / float(views)

        score_intent, intent_rate = intent_score(
            float(intent_count) if intent_count is not None else None,
            float(comments) if comments is not None else None,
        )
        score_performance = performance_score(view_index, ratio)
        score_relevance = normalized_manual_score(record.get("relevance_score"))
        score_transferability = normalized_manual_score(record.get("transferability_score"))
        completeness_ratio = data_completeness(record)
        score_completeness = completeness_ratio * 5

        component_scores = {
            "performance": score_performance,
            "intent": score_intent,
            "relevance": score_relevance,
            "transferability": score_transferability,
            "completeness": score_completeness,
        }
        available = {name: score for name, score in component_scores.items() if score is not None}
        strategic_count = sum(
            1 for name in ("performance", "intent", "relevance", "transferability") if name in available
        )
        coverage = sum(WEIGHTS[name] for name in available)

        priority: float | None = None
        penalty = risk_penalty(record.get("risk_level"))
        if strategic_count:
            weighted_average = sum(
                (float(score) / 5.0) * WEIGHTS[name] for name, score in available.items()
            ) / coverage
            evidence_adjustment = 0.6 + 0.4 * coverage
            priority = max(0.0, min(100.0, weighted_average * 100 * evidence_adjustment - penalty))
        else:
            warnings.append("no_strategic_score_components")

        risk_known = str(record.get("risk_level") or "unknown").strip().lower() in {
            "low",
            "medium",
            "high",
        }
        source_traceable = bool(str(record.get("content_url") or "").strip())
        if strategic_count >= 4 and completeness_ratio >= 0.75 and risk_known and source_traceable:
            confidence = "high"
        elif strategic_count >= 3 and completeness_ratio >= 0.5 and source_traceable:
            confidence = "medium"
        else:
            confidence = "low"

        if score_relevance is None:
            warnings.append("missing_relevance_score")
        if score_transferability is None:
            warnings.append("missing_transferability_score")
        if not risk_known:
            warnings.append("unknown_risk")

        output.update(
            {
                "account_sample_size": sample_size,
                "account_median_views": fmt(median_views),
                "view_index": fmt(view_index),
                "views_followers_ratio": fmt(ratio),
                "engagement_rate": fmt(engagement_rate, 6),
                "engagement_components_count": len(engagement_values),
                "intent_rate": fmt(intent_rate, 6),
                "performance_tier": performance_tier(view_index, ratio),
                "score_performance": fmt(score_performance, 2),
                "score_intent": fmt(score_intent, 2),
                "score_relevance": fmt(score_relevance, 2),
                "score_transferability": fmt(score_transferability, 2),
                "score_completeness": fmt(score_completeness, 2),
                "score_coverage": fmt(coverage, 2),
                "risk_penalty": fmt(penalty, 2),
                "priority_score": fmt(priority, 2),
                "priority_confidence": confidence,
                "ranking_warnings": ";".join(sorted(set(warnings))),
            }
        )
        enriched.append(output)

    return sorted(
        enriched,
        key=lambda row: (
            parse_number(row.get("priority_score")) is not None,
            float(parse_number(row.get("priority_score")) or -1),
        ),
        reverse=True,
    )


def write_csv(path: Path, fieldnames: list[str], records: list[dict[str, Any]]) -> None:
    output_fields = list(fieldnames) + [field for field in DERIVED_FIELDS if field not in fieldnames]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=output_fields, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="Normalized UTF-8 CSV")
    parser.add_argument("--output", required=True, type=Path, help="Ranked UTF-8 CSV")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    fieldnames, records = read_csv(args.input)
    enriched = enrich_records(records)
    write_csv(args.output, fieldnames, enriched)
    print(
        json.dumps(
            {
                "input": str(args.input),
                "output": str(args.output),
                "ranked_records": len(enriched),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
