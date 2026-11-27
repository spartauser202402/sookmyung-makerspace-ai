# Failure Classification Protocol

Classify failed directed MCP probing runs from their sanitized evidence. This workflow does not run a simulation, configure a separate judge provider, or score `assert_llm` assertions.

## Evidence

Use the test fixture together with the returned strict result. Read `strict_result.json` only when durable output was requested; otherwise use the result returned in the response.

| Source | Evidence |
|---|---|
| Test fixture | `agent`, `story`, `starting_sentence`, `goals`, `goal_details`, and explicit negative-test intent |
| Strict result | `status`, `classification`, `failure_reason`, `thread_id`, `step_results`, `tool_events`, `final_response` |

Use structured tool events, responses, and recorded MCP errors. Do not infer a tool failure solely from assistant text. Never request hidden reasoning or persist credentials, passwords, or raw unrestricted payloads.

## Classification Taxonomy

Assign one primary class to a failed run. A passed tool chain has no failure classification.

### `AGENT_FAILURE`

The connection worked and the fixture was valid, but the observed tool chain violated the declared graph:

- An unexpected registered tool or duplicate call occurred.
- A dependency was skipped or calls occurred in an invalid order.
- An expected call remained missing after the permitted driver turns.

Expected and observed argument values are recorded for context. With `ignore` matching, value differences are not failures. A missing initial call alone is not a failure when permitted follow-up instructions complete the chain. An unexpected initial call remains a failure even if later calls succeed.

### `EXTERNAL_FAILURE`

An unexpected infrastructure or service problem prevented a usable run:

- MCP/SDK error, timeout, unavailable agent, authentication or connection failure;
- missing thread ID, unusable structured tool events, or malformed/missing tool response;
- unexpected service error such as HTTP 5xx that prevents the intended scenario.

Use concrete recorded evidence. An expected domain rejection or not-found response in a negative scenario is not an external failure.

### `BAD_TEST_CASE / invalid_fixture`

The fixture has an invalid graph, malformed required fields, or unintentional contradictions that prevent a meaningful run. Detect structural problems before contacting the agent.

A valid fixture using a matching strategy other than `ignore` is unsupported by this workflow. Report that limitation without running it or silently changing the fixture; do not label it an agent failure.

### `BAD_TEST_CASE / stale_data`

A success scenario requires a runtime entity that the observed tool response shows is missing or no longer valid. Check the story and explicit negative-test intent first. A missing entity intentionally used to test graceful failure is not stale data.

### `BAD_TEST_CASE / underspecified_story`

The scenario lacks information needed to determine the intended tool chain or distinguish an expected negative outcome from an accidental fixture failure. Ask only for the missing test-defining information; do not guess that intent from an error alone.

## Assertion Concerns Are Separate

`assert_llm` entries are checked for structure but are not evaluated or scored by this skill. Do not classify a run using assertion scores or turn a successful tool chain into a failure because of a suspected assertion mismatch.

If the evidence suggests an assertion contradicts the intended story, report an unscored semantic review note. When generation is in progress, pass the evidence to its post-validation Story Review and Assertion Review. For standalone validation, offer a separate review without rewriting the existing test.

## Priority Rules

1. Reject structurally invalid fixtures before a live run. Report unsupported matching strategies separately.
2. Establish the scenario's intended outcome, including intentional negative conditions.
3. If unexpected infrastructure failure prevents assessment, use `EXTERNAL_FAILURE`.
4. If a success scenario requires missing runtime data, use `BAD_TEST_CASE / stale_data`. If intent cannot be established, clarify it rather than assuming stale data.
5. Otherwise classify evidenced graph violations as `AGENT_FAILURE`.

Preserve additional observed failures as diagnostic evidence even when one primary class takes precedence. Expected negative responses do not themselves fail a run; tool-chain requirements still apply.

## Running the Classification

Bob applies the taxonomy directly to each failed strict result. No separate configured judge is required. Return a concise evidence-based verdict:

```json
{
  "classification": "AGENT_FAILURE",
  "confidence": "high",
  "reason": "The agent called an undeclared registered tool before executing the requested chain."
}
```

Use `high`, `medium`, or `low` confidence. If evidence is insufficient to assign a class, report `CLASSIFICATION_UNAVAILABLE` with low confidence and explain what evidence is missing. This is a classification limitation, not another failure class; preserve the original run status and offer retry or manual review.

## Rendering the Report

Present:

1. A run table with test case, run status, matched tool steps, and result path only when a file was written.
2. A failure table with test case, classification, confidence, and concise evidence-based reason.
3. Aggregate counts for `AGENT_FAILURE`, `EXTERNAL_FAILURE`, and `BAD_TEST_CASE`, with subtype counts as needed. List unclassified failures separately so totals reconcile.
4. Any unscored assertion concerns as separate review notes.

Do not report assertion metrics. Omit failure tables when every run passed.

## Bad Test Case Remediation

List affected test file paths and the specific fixture problem.

- For `stale_data`, offer to replace the missing entity with valid data or preserve it as an intentional negative test.
- For `invalid_fixture`, distinguish accidental malformed data from an intentional rejection scenario before proposing a correction.
- For `underspecified_story`, ask for the missing test-defining information.

If the user requests a fix, activate `wxo-test-case-generation` with the existing agent and scenario context. For negative-test conversion, preserve the candidate, rewrite the story to state the intentional missing or invalid condition, update assertions to reflect the expected negative outcome, and repeat the format check and direct validation. Do not create a second candidate solely for conversion.

Do not rewrite a test during standalone validation without user authorization. If the user declines a proposed correction or conversion, preserve the test and report the unresolved issue.
