# Synthetic Example

This example is fictional. Names, metrics, and URLs are invented to demonstrate method only.

## Context

`RelayNote` is a fictional tool that turns customer-support calls into searchable summaries and follow-up tasks. The decision question is: which short-form content angle should enter the first test sprint?

## Candidate observations

| ID | Source | Observation |
|---|---|---|
| C01 | `https://example.invalid/c01` | A small creator opens with a missed customer promise, shows the call-to-task workflow, and receives repeated compatibility questions. |
| C02 | `https://example.invalid/c02` | A second creator uses the same failure moment for a different support role and performs above the account baseline. |
| C03 | `https://example.invalid/c03` | An owned post uses a role-specific failure hook and a screen demonstration; comments ask whether the workflow exports to a ticketing system. |
| C04 | `https://example.invalid/c04` | A feature-list post starts with “AI call summaries” and remains near baseline. |
| C05 | `https://example.invalid/c05` | Another feature-first post has high production quality but little visible product-fit discussion. |
| C06 | `https://example.invalid/c06` | A community thread describes manually replaying calls to confirm promises made to customers. |

## Pattern card

```text
Pattern: Open with a role-specific consequence of missing a promise before naming the tool.
Class: repeatable winning pattern
Scope: short-form support-operations content
Support: C01, C02, C03 across three accounts
Counterexamples: C04 and C05 use feature-first hooks and remain near baseline
Interpretation: recognition of a costly failure may create stronger relevance than a category label
Transfer rule: dramatize a truthful missed-promise moment, then prove the recovery workflow
Boundary: do not claim that every missed promise is automatically prevented
Next test: failure-moment hook versus feature-first hook with the same demonstration
Evidence label: inferred
Confidence: medium
```

## Opportunity card

```text
Opportunity: Show the exact moment a support lead needs to verify and assign a promise made during a call.
Gap type: moment gap + workflow gap
User evidence: C06 workaround; compatibility questions on C01 and C03
Competitive opening: observed content names summarization but rarely demonstrates promise-to-task handoff
Product fit: RelayNote can demonstrate the workflow with a controlled sample call
First test: two hooks using the same workflow proof
Needs validation: retention and conversion require first-party analytics
```

## Reference decision

Retain C01 for hook and integration timing, C03 for proof structure, C06 for user language, and C04 as a negative feature-first comparison. Preserve links and analysis; do not copy their wording or visuals.
