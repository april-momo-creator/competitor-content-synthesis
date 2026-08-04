---
name: competitor-content-synthesis
description: Analyze an existing competitor or social-content candidate pool and turn it into evidence-backed priority samples, per-content breakdowns, winning and losing patterns, opportunity gaps, and a curated reference pool. Use when the user already has content links, exports, research tables, screenshots, or candidate records and asks to explain why content performed, identify repeatable hooks or formats, compare owned/UGC/creator/community content, find unmet content opportunities, curate references, or prepare inputs for short-form video, slideshow, UGC, creator briefs, or content tests. Do not use it to discover competitors or collect the initial candidate pool from scratch.
---

# Competitor Content Synthesis

## Scope

Transform an existing candidate pool into decisions for content production and testing. Keep upstream competitor discovery separate.

Cover this chain:

1. Validate and normalize the input.
2. Select a balanced priority sample.
3. Analyze individual content.
4. Synthesize winning, losing, and emerging patterns.
5. Identify evidence-backed opportunity gaps.
6. Curate a reusable reference pool.
7. Produce only the deliverables the user needs.

Do not invent missing platform metrics, comments, audience reactions, product capabilities, or causal explanations.

## Check Prerequisites

Require enough context to support the requested decision:

- Product context: positioning, target users, use cases, and validated or hypothesized differentiators.
- Competitor context: named competitors or sources, preferably labeled direct, indirect, or aspirational.
- Content candidate pool: links or records with platform and observable content evidence.

If the candidate pool is missing, ask for it or run an upstream discovery workflow such as `competitor-content-discovery` when available. If only product context or competitor layering is missing, request or reconstruct the smallest missing artifact before synthesis. Never disguise discovery as synthesis.

Read [references/input-contract.md](references/input-contract.md) whenever input completeness, field mapping, evidence labels, or missing data is in question.

## Route References

Load only the references required for the request:

| Task | Read |
|---|---|
| Normalize CSV/JSON exports, map fields, deduplicate records | `references/input-contract.md`, `references/platform-metrics.md` |
| Select or rank candidates | `references/platform-metrics.md`, `references/content-analysis.md` |
| Deep-analyze content or slideshows | `references/content-analysis.md` |
| Find winning, losing, or emerging patterns | `references/pattern-synthesis.md` |
| Identify content whitespace or test opportunities | `references/opportunity-gap.md` |
| Curate a final reference pool | `references/reference-pool.md` |
| Produce files or strict tables | `references/output-contracts.md` |
| See a compact end-to-end example | `references/synthetic-example.md` |

## Run the Workflow

### 1. Validate and normalize

Confirm the decision question, time window, platforms, target market, product truth, and available metrics. Preserve the original URL and record `observed_at` for every live observation.

For structured CSV or JSON inputs, prefer:

```text
python scripts/normalize_content_pool.py --input INPUT --output normalized.csv
python scripts/rank_content_candidates.py --input normalized.csv --output ranked.csv
```

Treat script scores as triage aids, not strategic conclusions.

### 2. Select a balanced sample

Do not analyze only the highest-viewed posts. Include:

- Positive outliers relative to the same account and platform.
- Low-follower breakouts.
- High-intent comment examples.
- Typical baseline content.
- Underperformers with comparable context.
- Relevant direct, indirect, and aspirational sources when available.

Use platform-native and within-account comparisons before cross-account comparisons.

### 3. Analyze individual content

Separate observation from interpretation. Record the hook, angle, structure, proof, product exposure, CTA, visible audience response, transferability, and risks. For slideshows or sequences, assign a role to every frame.

### 4. Synthesize patterns

Call a pattern `repeatable` only when at least three independent examples across at least two accounts support it. Call weaker but plausible signals `emerging`. Require a fair baseline or negative evidence before calling a pattern `losing`.

State counterexamples and scope. Do not turn correlation into causation.

### 5. Identify opportunity gaps

Require an intersection of:

- Observable user or market evidence.
- A meaningful omission, weak expression, or saturated convention in the competitor set.
- Product relevance and a truthful proof path.
- A testable content execution.

Reject attractive ideas that depend on unsupported claims or cannot be tested with available resources.

### 6. Curate the reference pool

Keep references because they answer a production question, not because they look impressive. Explain what transfers, what does not, which persona and stage they serve, and what risk must be managed.

Link to sources. Do not copy complete third-party scripts, captions, image sets, or other copyrighted creative into the output.

### 7. Deliver

Match the user's language. Use compact Markdown for synthesis and CSV for row-level assets. Keep verified facts, inferences, and validation needs visibly separate.

Default deliverables for a full run:

1. `content-analysis.md` or `.csv`
2. `pattern-synthesis.md`
3. `opportunity-gap.md`
4. `reference-pool.csv`

Do not add a campaign plan, creator brief, production script, or monitoring workflow unless the user asks for it.

## Evidence Rules

- Mark claims `verified`, `inferred`, or `needs validation`.
- Preserve source URL, platform, publication date when visible, and observation date.
- Use canonical or redacted URLs in anything intended for public sharing; never publish credential-like query parameters.
- Treat screenshots and user-provided exports as evidence with stated provenance.
- Treat view counts, follower counts, and comments as time-bound snapshots.
- Mark inaccessible or hidden data as unavailable; never estimate it silently.
- Prefer multiple independent examples over one viral outlier.
- Keep product capabilities and claims tied to user-provided or current official sources.

## Quality Gates

Before finalizing, verify:

- Every selected item has a traceable source or provenance note.
- Every repeatable pattern meets the evidence threshold or is downgraded to emerging.
- Every losing pattern has a valid comparison basis.
- Every opportunity gap names its supporting evidence, product fit, and first test.
- Every reference records a reuse rationale and a boundary against copying.
- Missing data and access limitations appear in the final output.
- The output answers the decision question instead of merely summarizing content.

## Stop Conditions

Stop when new evidence no longer changes the ranked patterns, opportunity priorities, or reference categories. As a default full-run target, analyze 20–50 priority items and retain 10–25 references, adapting the volume to the available pool and decision stakes. Do not force fixed quotas when the evidence is thin.
