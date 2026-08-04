#!/usr/bin/env python3
"""Normalize and deduplicate competitor/social content candidate pools.

The script accepts a UTF-8 CSV file or a JSON array/object and writes a
canonical UTF-8 CSV. It never converts missing metrics to zero.
"""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit


CANONICAL_FIELDS = [
    "content_id",
    "platform",
    "source_type",
    "competitor_type",
    "brand",
    "account_name",
    "account_url",
    "content_url",
    "canonical_url",
    "published_at",
    "observed_at",
    "baseline_group",
    "followers",
    "views",
    "impressions",
    "reach",
    "likes",
    "comments",
    "saves",
    "shares",
    "title",
    "hook",
    "content_angle",
    "format",
    "product_exposure",
    "cta",
    "intent_signal_count",
    "negative_signal_count",
    "relevance_score",
    "transferability_score",
    "risk_level",
    "notes",
    "duplicate_count",
    "source_record_indices",
    "normalization_warnings",
    "extra_json",
]

NUMERIC_FIELDS = {
    "followers",
    "views",
    "impressions",
    "reach",
    "likes",
    "comments",
    "saves",
    "shares",
    "intent_signal_count",
    "negative_signal_count",
    "relevance_score",
    "transferability_score",
}

ALIASES = {
    "content_id": {"content_id", "id", "post_id", "video_id"},
    "platform": {"platform", "channel", "network"},
    "source_type": {"source_type", "publisher_type", "content_source_type"},
    "competitor_type": {"competitor_type", "competition_type", "competitor_class"},
    "brand": {"brand", "product", "competitor", "brand_name", "product_name"},
    "account_name": {"account_name", "account", "creator", "publisher", "username", "handle"},
    "account_url": {"account_url", "profile_url", "creator_url"},
    "content_url": {"content_url", "video_url", "post_url", "link", "url"},
    "published_at": {"published_at", "posted_at", "publish_date", "date", "post_date"},
    "observed_at": {"observed_at", "captured_at", "snapshot_date", "checked_at", "collected_at"},
    "baseline_group": {"baseline_group", "comparison_group", "cohort"},
    "followers": {"followers", "followers_count", "follower_count", "fans"},
    "views": {"views", "view_count", "plays", "play_count"},
    "impressions": {"impressions", "impression_count"},
    "reach": {"reach", "accounts_reached", "unique_reach"},
    "likes": {"likes", "like_count"},
    "comments": {"comments", "comment_count"},
    "saves": {"saves", "save_count", "bookmarks", "bookmark_count", "favorites"},
    "shares": {"shares", "share_count", "reposts", "repost_count"},
    "title": {"title", "caption", "description", "content_title"},
    "hook": {"hook", "opening", "first_line", "first_frame"},
    "content_angle": {"content_angle", "angle", "theme", "topic_angle"},
    "format": {"format", "content_format", "post_format"},
    "product_exposure": {"product_exposure", "product_placement", "ad_integration"},
    "cta": {"cta", "call_to_action"},
    "intent_signal_count": {"intent_signal_count", "intent_comments", "purchase_intent_count"},
    "negative_signal_count": {"negative_signal_count", "negative_comments", "objection_count"},
    "relevance_score": {"relevance_score", "fit_score", "product_relevance"},
    "transferability_score": {
        "transferability_score",
        "reuse_score",
        "portability_score",
        "adaptability_score",
    },
    "risk_level": {"risk_level", "risk", "creative_risk"},
    "notes": {"notes", "analysis_notes", "commentary"},
}

PLATFORM_ALIASES = {
    "tiktok": "tiktok",
    "tik_tok": "tiktok",
    "tt": "tiktok",
    "instagram": "instagram",
    "instagram_reels": "instagram",
    "ig": "instagram",
    "reels": "instagram",
    "youtube": "youtube",
    "youtube_shorts": "youtube",
    "yt": "youtube",
    "shorts": "youtube",
    "linkedin": "linkedin",
    "linked_in": "linkedin",
    "reddit": "reddit",
    "x": "x",
    "twitter": "x",
    "twitter_x": "x",
    "facebook": "facebook",
    "fb": "facebook",
}

SOURCE_TYPE_ALIASES = {
    "official": "owned",
    "official_account": "owned",
    "brand": "owned",
    "owned": "owned",
    "ugc": "ugc",
    "user_generated": "ugc",
    "user_generated_content": "ugc",
    "creator": "creator",
    "influencer": "creator",
    "kol": "creator",
    "koc": "creator",
    "community": "community",
    "forum": "community",
    "review": "review",
    "comparison": "review",
}

COMPETITOR_TYPE_ALIASES = {
    "direct": "direct",
    "direct_competitor": "direct",
    "indirect": "indirect",
    "indirect_competitor": "indirect",
    "aspirational": "aspirational",
    "aspiration": "aspirational",
    "reference": "aspirational",
}

RISK_ALIASES = {
    "low": "low",
    "medium": "medium",
    "med": "medium",
    "high": "high",
    "unknown": "unknown",
}

TRACKING_PARAMETERS = {
    "fbclid",
    "gclid",
    "igshid",
    "mc_cid",
    "mc_eid",
    "ref",
    "referrer",
    "share_id",
    "source",
}

SENSITIVE_PARAMETER_NAMES = {
    "access_token",
    "api_key",
    "apikey",
    "auth",
    "authorization",
    "key",
    "session",
    "session_id",
    "sessionid",
    "sig",
    "signature",
    "token",
}

SNAPSHOT_METRIC_FIELDS = {
    "followers",
    "views",
    "impressions",
    "reach",
    "likes",
    "comments",
    "saves",
    "shares",
    "intent_signal_count",
    "negative_signal_count",
}


def normalize_key(value: Any) -> str:
    text = str(value or "").strip().lower()
    text = re.sub(r"[^0-9a-zA-Z\u4e00-\u9fff]+", "_", text)
    return text.strip("_")


ALIAS_LOOKUP = {
    alias: canonical for canonical, aliases in ALIASES.items() for alias in aliases
}


def is_blank(value: Any) -> bool:
    return value is None or (isinstance(value, str) and not value.strip())


def parse_number(value: Any) -> int | float | None:
    """Parse common social metric strings without treating blanks as zero."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return value

    text = str(value).strip().replace(",", "").replace("，", "")
    text = text.replace("\u00a0", "").replace("\u202f", "").replace(" ", "")
    if not text or text.lower() in {"-", "—", "n/a", "na", "none", "null", "unknown"}:
        return None

    match = re.fullmatch(r"([+-]?(?:\d+(?:\.\d*)?|\.\d+))([kKmMbB万亿])?(%)?", text)
    if not match:
        return None

    number = float(match.group(1))
    suffix = match.group(2)
    multiplier = {
        None: 1,
        "k": 1_000,
        "K": 1_000,
        "m": 1_000_000,
        "M": 1_000_000,
        "b": 1_000_000_000,
        "B": 1_000_000_000,
        "万": 10_000,
        "亿": 100_000_000,
    }[suffix]
    number *= multiplier
    if match.group(3):
        number /= 100
    return int(number) if number.is_integer() else number


def canonicalize_url(value: Any) -> str:
    """Return a stable deduplication URL while preserving access URLs elsewhere."""
    if is_blank(value):
        return ""
    text = str(value).strip()
    try:
        parts = urlsplit(text)
    except ValueError:
        return text
    if not parts.scheme or not parts.netloc:
        return text

    kept_query: list[tuple[str, str]] = []
    for key, item_value in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if (
            lowered.startswith("utm_")
            or lowered in TRACKING_PARAMETERS
            or lowered in SENSITIVE_PARAMETER_NAMES
            or lowered.endswith("_token")
            or lowered.endswith("_key")
        ):
            continue
        kept_query.append((key, item_value))

    scheme = parts.scheme.lower()
    netloc = parts.netloc.lower()
    if scheme == "http" and netloc.endswith(":80"):
        netloc = netloc[:-3]
    if scheme == "https" and netloc.endswith(":443"):
        netloc = netloc[:-4]

    path = parts.path.rstrip("/") or "/"
    return urlunsplit((scheme, netloc, path, urlencode(sorted(kept_query)), ""))


def contains_sensitive_query_parameter(value: Any) -> bool:
    if is_blank(value):
        return False
    try:
        parts = urlsplit(str(value).strip())
    except ValueError:
        return False
    for key, _ in parse_qsl(parts.query, keep_blank_values=True):
        lowered = key.lower()
        if (
            lowered in SENSITIVE_PARAMETER_NAMES
            or lowered.endswith("_token")
            or lowered.endswith("_key")
        ):
            return True
    return False


def normalize_enum(value: Any, mapping: dict[str, str], default: str) -> str:
    if is_blank(value):
        return default
    key = normalize_key(value)
    return mapping.get(key, default)


def parse_iso_datetime(value: Any) -> datetime | None:
    if is_blank(value):
        return None
    text = str(value).strip().replace("Z", "+00:00")
    try:
        result = datetime.fromisoformat(text)
    except ValueError:
        return None
    if result.tzinfo is None:
        result = result.replace(tzinfo=timezone.utc)
    return result


def stable_content_id(record: dict[str, Any]) -> str:
    if not is_blank(record.get("content_id")):
        return str(record["content_id"]).strip()
    identity = record.get("canonical_url") or "|".join(
        str(record.get(field) or "")
        for field in ("platform", "account_name", "published_at", "title", "hook")
    )
    return "c_" + hashlib.sha256(identity.encode("utf-8")).hexdigest()[:16]


def load_records(path: Path) -> list[dict[str, Any]]:
    suffix = path.suffix.lower()
    if suffix == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    if suffix == ".json":
        with path.open("r", encoding="utf-8-sig") as handle:
            payload = json.load(handle)
        if isinstance(payload, list):
            records = payload
        elif isinstance(payload, dict):
            records = next(
                (payload[key] for key in ("records", "items", "data") if isinstance(payload.get(key), list)),
                None,
            )
            if records is None:
                raise ValueError("JSON object must contain a records, items, or data array.")
        else:
            raise ValueError("JSON input must be an array or an object containing an array.")
        if not all(isinstance(item, dict) for item in records):
            raise ValueError("Every JSON record must be an object.")
        return [dict(item) for item in records]
    raise ValueError("Input must use .csv or .json extension.")


def normalize_record(raw: dict[str, Any], index: int) -> dict[str, Any]:
    normalized_raw = {normalize_key(key): value for key, value in raw.items()}
    mapped: dict[str, Any] = {field: "" for field in CANONICAL_FIELDS}
    consumed: set[str] = set()
    warnings: list[str] = []

    for raw_key, value in normalized_raw.items():
        canonical = ALIAS_LOOKUP.get(raw_key)
        if canonical and is_blank(mapped.get(canonical)):
            mapped[canonical] = value
            consumed.add(raw_key)

    mapped["platform"] = normalize_enum(mapped["platform"], PLATFORM_ALIASES, "unknown")
    mapped["source_type"] = normalize_enum(mapped["source_type"], SOURCE_TYPE_ALIASES, "unknown")
    mapped["competitor_type"] = normalize_enum(
        mapped["competitor_type"], COMPETITOR_TYPE_ALIASES, "unknown"
    )
    mapped["risk_level"] = normalize_enum(mapped["risk_level"], RISK_ALIASES, "unknown")

    for field in NUMERIC_FIELDS:
        original = mapped.get(field)
        parsed = parse_number(original)
        if not is_blank(original) and parsed is None:
            warnings.append(f"unparsed_{field}")
        if field in {"relevance_score", "transferability_score"} and parsed is not None:
            if parsed < 0 or parsed > 5:
                warnings.append(f"out_of_range_{field}")
                parsed = None
        mapped[field] = "" if parsed is None else parsed

    mapped["content_url"] = str(mapped.get("content_url") or "").strip()
    mapped["canonical_url"] = canonicalize_url(mapped["content_url"])
    mapped["content_id"] = stable_content_id(mapped)
    mapped["duplicate_count"] = 1
    mapped["source_record_indices"] = str(index)

    if mapped["platform"] == "unknown":
        warnings.append("unknown_platform")
    if not mapped["content_url"]:
        warnings.append("missing_content_url")
    if mapped["content_url"] and not mapped["canonical_url"]:
        warnings.append("uncanonicalized_content_url")
    if contains_sensitive_query_parameter(mapped["content_url"]):
        warnings.append("content_url_contains_sensitive_query_parameter")
    if not mapped["observed_at"] and any(not is_blank(mapped.get(field)) for field in ("views", "likes", "comments")):
        warnings.append("metrics_without_observed_at")

    extras = {
        key: value
        for key, value in normalized_raw.items()
        if key not in consumed and key not in ALIAS_LOOKUP
    }
    mapped["normalization_warnings"] = ";".join(sorted(set(warnings)))
    mapped["extra_json"] = json.dumps(extras, ensure_ascii=False, sort_keys=True) if extras else ""
    return mapped


def dedupe_key(record: dict[str, Any]) -> str:
    if record.get("canonical_url"):
        return "url:" + str(record["canonical_url"])
    identity_parts = [
        str(record.get(field) or "").strip().lower()
        for field in ("platform", "account_name", "published_at", "title", "hook")
    ]
    if not any(identity_parts):
        return "source:" + str(record.get("source_record_indices") or id(record))
    identity = "|".join(identity_parts)
    return "fallback:" + hashlib.sha256(identity.encode("utf-8")).hexdigest()


def _newest_record(records: list[dict[str, Any]]) -> dict[str, Any]:
    def key(record: dict[str, Any]) -> tuple[int, datetime, int]:
        observed = parse_iso_datetime(record.get("observed_at"))
        index_text = str(record.get("source_record_indices") or "0").split(";")[0]
        index = int(index_text) if index_text.isdigit() else 0
        return (
            1 if observed is not None else 0,
            observed or datetime.min.replace(tzinfo=timezone.utc),
            index,
        )

    return max(records, key=key)


def _merge_json_objects(values: Iterable[Any]) -> str:
    merged: dict[str, Any] = {}
    for value in values:
        if is_blank(value):
            continue
        try:
            payload = json.loads(str(value))
        except json.JSONDecodeError:
            continue
        if isinstance(payload, dict):
            for key, item in payload.items():
                merged.setdefault(key, item)
    return json.dumps(merged, ensure_ascii=False, sort_keys=True) if merged else ""


def deduplicate_records(records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    groups: dict[str, list[dict[str, Any]]] = {}
    order: list[str] = []
    for record in records:
        key = dedupe_key(record)
        if key not in groups:
            groups[key] = []
            order.append(key)
        groups[key].append(record)

    result: list[dict[str, Any]] = []
    for key in order:
        group = groups[key]
        primary = dict(_newest_record(group))
        primary_observed_at = str(primary.get("observed_at") or "").strip()
        deferred_warnings: list[str] = []
        for record in group:
            if record is primary:
                continue
            for field in CANONICAL_FIELDS:
                if field in {"duplicate_count", "source_record_indices", "normalization_warnings", "extra_json"}:
                    continue
                if is_blank(primary.get(field)) and not is_blank(record.get(field)):
                    record_observed_at = str(record.get("observed_at") or "").strip()
                    if (
                        field in SNAPSHOT_METRIC_FIELDS
                        and primary_observed_at
                        and record_observed_at
                        and primary_observed_at != record_observed_at
                    ):
                        deferred_warnings.append(f"older_snapshot_{field}_not_merged")
                        continue
                    primary[field] = record[field]

        indices = sorted(
            {
                int(part)
                for record in group
                for part in str(record.get("source_record_indices") or "").split(";")
                if part.isdigit()
            }
        )
        warnings = sorted(
            {
                warning
                for record in group
                for warning in str(record.get("normalization_warnings") or "").split(";")
                if warning
            }
            | set(deferred_warnings)
        )
        primary["duplicate_count"] = len(group)
        primary["source_record_indices"] = ";".join(str(item) for item in indices)
        primary["normalization_warnings"] = ";".join(warnings)
        primary["extra_json"] = _merge_json_objects(record.get("extra_json") for record in group)
        primary["content_id"] = stable_content_id(primary)
        result.append(primary)
    return result


def normalize_records(raw_records: list[dict[str, Any]]) -> list[dict[str, Any]]:
    normalized = [normalize_record(record, index) for index, record in enumerate(raw_records, start=1)]
    return deduplicate_records(normalized)


def write_csv(path: Path, records: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=CANONICAL_FIELDS, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(records)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, type=Path, help="UTF-8 CSV or JSON candidate pool")
    parser.add_argument("--output", required=True, type=Path, help="Destination UTF-8 CSV")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    records = normalize_records(load_records(args.input))
    write_csv(args.output, records)
    print(
        json.dumps(
            {
                "input": str(args.input),
                "output": str(args.output),
                "normalized_records": len(records),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
