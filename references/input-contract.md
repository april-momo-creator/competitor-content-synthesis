# Input Contract

Use this contract to decide whether synthesis can begin and how to map structured data.

## Minimum Context

Require four inputs for a full run:

1. **Decision question** — for example, which hooks to test, why a competitor format works, or which gap should enter the next content sprint.
2. **Product truth** — positioning, target users, key use cases, and validated or explicitly hypothetical differentiators.
3. **Competitor context** — source name and, when known, direct/indirect/aspirational classification.
4. **Candidate content** — source links or user-provided records that can be inspected or analyzed.

Proceed with a partial request when the missing inputs do not affect the requested output. State the limitation.

## Canonical Record Fields

| Field | Type | Requirement | Meaning |
|---|---|---:|---|
| `content_id` | string | Generated if missing | Stable identifier derived from canonical URL or record identity |
| `platform` | enum | Required | `tiktok`, `instagram`, `youtube`, `linkedin`, `reddit`, `x`, `facebook`, `other`, `unknown` |
| `source_type` | enum | Recommended | `owned`, `ugc`, `creator`, `community`, `review`, `unknown` |
| `competitor_type` | enum | Optional | `direct`, `indirect`, `aspirational`, `unknown` |
| `brand` | string | Recommended | Product or competitor represented |
| `account_name` | string | Recommended | Publishing account |
| `account_url` | URL | Optional | Account profile URL |
| `content_url` | URL | Required when available | Original source URL; preserve query parameters needed to access it |
| `canonical_url` | URL | Generated | Deduplication form with common tracking parameters removed |
| `published_at` | ISO date/time or source text | Recommended | Publication time when visible |
| `observed_at` | ISO date/time | Required for live metrics | Date or time metrics were observed |
| `baseline_group` | string | Optional | User-defined cohort for comparable posts, such as format or campaign window |
| `followers` | number | Optional | Account follower count at observation time |
| `views` | number | Optional | Visible plays or views |
| `impressions` | number | Optional | Visible impressions; never merge into views |
| `reach` | number | Optional | Visible unique reach or accounts reached |
| `likes` | number | Optional | Visible likes |
| `comments` | number | Optional | Visible comment count |
| `saves` | number | Optional | Visible saves or bookmarks |
| `shares` | number | Optional | Visible share count |
| `title` | string | Optional | Visible title or short description |
| `hook` | string | Recommended for deep analysis | Opening text, spoken line, or first-frame idea |
| `content_angle` | string | Recommended | Strategic angle, not merely the topic |
| `format` | string | Recommended | Talking head, slideshow, tutorial, list, meme, review, etc. |
| `product_exposure` | string | Optional | Demo, mention, soft integration, hard sell, none |
| `cta` | string | Optional | Visible call to action |
| `intent_signal_count` | number | Optional | Count of comments showing tool, price, link, fit, or usage intent |
| `negative_signal_count` | number | Optional | Count of relevant objections or negative signals |
| `relevance_score` | 0–5 | Optional/manual | Fit with the product, audience, and decision question |
| `transferability_score` | 0–5 | Optional/manual | How readily the structure can be adapted without copying |
| `risk_level` | enum | Recommended | `low`, `medium`, `high`, `unknown` |
| `notes` | string | Optional | Source-specific observations |

## Accepted Aliases

Normalize common headings without discarding the original meaning:

- `video_url`, `post_url`, `link`, `url` → `content_url`
- `channel`, `network` → `platform`
- `account`, `creator`, `publisher`, `username` → `account_name`
- `followers_count`, `fans` → `followers`
- `plays`, `play_count`, `view_count` → `views`
- `like_count` → `likes`
- `comment_count` → `comments`
- `save_count`, `bookmarks` → `saves`
- `share_count`, `reposts` → `shares`
- `date`, `posted_at`, `publish_date` → `published_at`
- `captured_at`, `snapshot_date`, `checked_at` → `observed_at`
- `angle`, `theme` → `content_angle`
- `reuse_score`, `portability_score` → `transferability_score`

Preserve unmapped fields in `extra_json` when running the normalization script.

## Missing Data Rules

- Leave missing metrics blank. Do not coerce them to zero.
- Distinguish a visible zero from unavailable data.
- Do not infer comments, saves, or shares from engagement totals.
- Do not map impressions or reach into views.
- Do not infer follower counts from account labels such as micro or macro.
- Keep records with missing metrics when their qualitative evidence is valuable.
- Exclude records from a metric-specific comparison when the required denominator is missing.
- Record access failures and hidden metrics in `normalization_warnings` or the final limitations section.

## Duplicate Rules

Deduplicate by canonical URL first. If no usable URL exists, use a conservative combination of platform, account, publication time, and title or hook.

When duplicate snapshots exist:

1. Prefer the record with the most recent valid `observed_at`.
2. Fill only its blank fields from older records.
3. Do not combine metrics from different observation times into a synthetic snapshot.
4. Record `duplicate_count` and source record indices.

Do not fill a missing metric in the newest snapshot from an older observation date. Preserve the newest snapshot and record a warning instead.

## URL Safety

Preserve the original source URL for internal traceability, but use `canonical_url` for deduplication and public deliverables. The normalization script removes common tracking and credential-like query parameters from the canonical form and warns when the original URL appears to contain a token, key, signature, authorization value, or session identifier.

Before publishing research outputs, remove or redact tokenized source URLs. A share link that opens for the researcher may still expose account-bound access information.

## Evidence Labels

Apply labels at the claim level:

- `verified` — directly visible in a source or supplied artifact.
- `inferred` — a reasoned interpretation supported by cited observations.
- `needs validation` — plausible but not sufficiently supported, inaccessible, or dependent on internal data.
