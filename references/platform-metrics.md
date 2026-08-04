# Platform Metrics and Ranking

Use metrics to select evidence, not to manufacture certainty.

## Contents

- Comparison Order
- Observation Rules
- Derived Metrics
- Candidate Priority Score
- Confidence
- Known Biases

## Comparison Order

Compare in this order:

1. Same account, same platform, comparable time window.
2. Similar account size and source type on the same platform.
3. Same content format and objective on the same platform.
4. Cross-platform patterns only after normalizing the strategic question; never compare raw counts as if they were equivalent.

## Observation Rules

- Record `observed_at` for every metric snapshot.
- Prefer a consistent observation window.
- Note whether content is still accumulating distribution.
- Treat deleted, boosted, pinned, or paid content separately when known.
- Do not assume an outlier is organic when promotion status is unknown.

## Derived Metrics

### Account baseline

Compute the median views for the same `platform + account_name + baseline_group` only when at least five valid records are available. `baseline_group` may be blank; use it to separate materially different formats or campaign windows. Prefer 20–30 comparable posts when possible.

```text
view_index = content_views / account_median_views
```

Default descriptive tiers:

| View index | Tier |
|---:|---|
| `>= 5` | strong outlier |
| `>= 3` | outlier |
| `>= 1.5` | above baseline |
| `>= 0.75` | baseline range |
| `< 0.75` | below baseline |

Treat these as heuristics, not universal laws.

### Low-follower breakout

```text
views_followers_ratio = views / followers
```

Default descriptive tiers:

| Ratio | Tier |
|---:|---|
| `>= 10` | strong low-follower breakout |
| `>= 3` | low-follower breakout |
| `>= 1` | reached beyond the follower base |

Do not calculate when follower count is unavailable or zero.

### Visible engagement

```text
engagement_rate = (available likes + comments + saves + shares) / views
```

Record `engagement_components_count`. A rate built from likes and comments only is not equivalent to one that includes saves and shares.

### Intent signals

```text
intent_rate = intent_signal_count / comments
```

Count only comments that show a relevant action or decision signal, such as asking for the product, price, link, compatibility, workflow fit, trial, or purchase. Do not classify generic praise as intent.

## Candidate Priority Score

Use the ranking script only for triage. It combines available components and renormalizes their weights rather than treating missing data as zero.

| Component | Default weight | Source |
|---|---:|---|
| Performance evidence | 35 | View index or views/followers ratio |
| Intent evidence | 20 | Intent rate or limited intent count evidence |
| Product relevance | 20 | Manual 0–5 score |
| Transferability | 15 | Manual 0–5 score |
| Data completeness | 10 | Presence of decision-relevant fields |

Apply risk penalties after the weighted score:

- `low`: 0
- `medium`: 5 points
- `high`: 15 points
- `unknown`: no automatic penalty, but lower confidence

Never use priority score as proof that a creative will work.

## Confidence

Assign confidence from evidence coverage:

- `high`: performance evidence, intent or audience evidence, product relevance, transferability, and strong record completeness are available.
- `medium`: at least three decision components are available and the source is traceable.
- `low`: the score depends on one or two components, lacks manual fit judgments, or uses incomplete provenance.

## Known Biases

Flag these before interpreting results:

- Survivorship bias from collecting only popular posts.
- Recency bias from comparing mature posts with newly published posts.
- Paid-distribution bias.
- Account-size and audience-history effects.
- Platform-specific metric visibility.
- Reposts and duplicated creative.
- Cultural or language mismatch between the observed audience and target market.
- Selection bias caused by inaccessible or login-gated content.
