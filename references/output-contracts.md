# Output Contracts

Use Markdown for decisions and CSV for row-level assets. Return only the artifacts needed by the user's request.

## `content-analysis.csv`

Use this column order:

```text
content_id,platform,source_type,competitor_type,brand,account_name,content_url,published_at,observed_at,performance_tier,topic,content_angle,persona,user_moment,hook,structure,proof,product_exposure,cta,audience_response,transferable_element,non_transferable_element,risk_level,evidence_label,confidence,notes
```

## `pattern-synthesis.md`

```markdown
# Pattern Synthesis

## Decision question

## Evidence coverage
- Platforms:
- Accounts:
- Items analyzed:
- Observation window:
- Material limitations:

## Priority patterns
### P01 — [specific pattern statement]
- Class:
- Scope:
- Supporting content IDs:
- Counterexamples:
- Observed effect:
- Interpretation:
- Transfer rule:
- Boundary:
- Next test:
- Confidence:

## Contradictory or insufficient signals

## What not to conclude
```

## `opportunity-gap.md`

```markdown
# Opportunity Gap Map

## O01 — [opportunity statement]
- Gap type:
- Persona and user moment:
- User evidence:
- Competitive evidence:
- Product truth and proof:
- Proposed expression:
- First test:
- Success signal:
- Dependencies:
- Risks:
- Scores: user evidence / product fit / differentiation / testability / repeatability
- Total after risk penalty:
- Evidence label:
- Confidence:
```

## `reference-pool.csv`

Use this column order:

```text
reference_id,content_id,source_url,platform,source_type,competitor_type,persona,user_moment,pattern_tags,opportunity_tags,why_selected,transferable_element,do_not_copy,possible_adaptation,evidence_label,risk_level,observed_at
```

## Executive Summary

When the user asks for a concise report, lead with:

1. The decision question.
2. The three most defensible patterns.
3. The three highest-priority opportunities.
4. The first tests to run.
5. The most important limitation.

Do not lead with research volume or a long competitor list.
