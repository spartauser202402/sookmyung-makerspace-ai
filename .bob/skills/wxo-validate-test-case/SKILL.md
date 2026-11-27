---
name: wxo-validate-test-case
description: Validates unified test case JSON files (tool_call steps plus assert_llm assertions, no summarize step) against a live WatsonX Orchestrate agent by directing the agent through the declared tool chain, preserving conversation context for dependencies, and classifying failures.
---

# Test Case Validation

Use this skill for every request that involves running, validating, or evaluating strict test case files against a WatsonX Orchestrate agent.

## Environment check (run first)

Before gathering context or starting the workflow, follow [Preflight environment check](references/preflight-env-check.md) to choose the project interpreter and run the shared check once for this request. Continue only on success, and use the same interpreter for subsequent Python commands.

The user may provide a path to a single unified test case `.json` file, or a directory containing unified test cases. A unified test case has `tool_call` steps and `assert_llm` assertions in `goal_details`, and a dependency graph in `goals`. It has no `summarize` step. This skill does not evaluate `assert_llm` assertions. It uses Bob Shell's Orchestrate MCP `chat_with_agent` tool. See [Evaluation Protocol](references/evaluation-protocol.md#strict-test-evaluation).

---

# Context Gathering (ALWAYS REQUIRED)

Before beginning, gather the following:

1. **Test path** — a single `.json` test case file or a directory containing test case files.
   - If not provided, ask the user for the path.
2. **Output directory** — where to write evaluation results.
   - Results are returned on stdout by default. Use `results/strict-eval-run` only when the user asks for durable result files.

All other configuration, including the Orchestrate connection, is read from the configured Bob/SDK environment. Do not ask for or confirm these values.

---

# Core Interaction Model

```text
User provides test path + optional config
    ↓
CONFIGURE — resolve test path and output dir
    ↓
EVALUATE — execute strict tool-chain protocol
    ↓
CLASSIFY — classify failed strict runs
    ↓
REPORT — run status + per-test failure table + aggregate summary
    ↓
REMEDIATE (if BAD_TEST_CASE detected) — offer to fix or regenerate bad test cases
```

Skip directly to the furthest stage justified by the user's request.

Examples:
- `"Validate my test cases"` → gather context, then CONFIGURE.
- `"Validate tests in ./evals/hr_agent against localhost:4321"` → CONFIGURE with provided values, skip asking.
- `"The eval already ran, here are the results"` → skip execution, go straight to CLASSIFY.

---

# Phase Classification

Determine the current phase before proceeding.

Possible phases:

- `CONFIGURE`
- `EVALUATE`
- `CLASSIFY`
- `REPORT`
- `REMEDIATE`

---

# CONFIGURE

## Trigger when
- The user wants to validate test cases but has not yet provided a test path.

During this phase:
1. Ask the user for the test path if it was not provided in their initial message.
2. Return results in the response by default. Write durable files only when the user requests them; use their output directory or `results/strict-eval-run` when none is specified.
3. Once the test path is known, move immediately to EVALUATE and read the direct strict evaluation protocol.

---

# EVALUATE

## Trigger when
- The test path is known and the configured MCP connection is available.

During this phase, read [Evaluation Protocol](references/evaluation-protocol.md) for detailed guidance on:
- Validating the `goals` graph before contacting the agent. Terminal tool steps point to `[]`, and `assert_llm` entries appear in `goal_details` only.
- Calling Bob Shell's Orchestrate MCP `chat_with_agent` tool with the test's `starting_sentence` and `include_reasoning=True`.
- Asking the target agent to execute each `goal_details` tool step with the expected arguments.
- Handling single file vs. directory input.
- Returning the sanitized strict-run result to stdout; write a file only when explicitly requested.

Do not wrap Bob Shell in another Bob Shell session. If the MCP tool is unavailable, stop and report the MCP configuration problem rather than silently switching validation modes.

The initial target-agent behavior must remain in the trace. Follow-up instructions may continue the run, but must not replace or erase an unexpected initial tool call.

---

# CLASSIFY

## Trigger when
- The evaluation run has completed and there are one or more failing test cases.
- The user shares a strict-run result directly.

During this phase, read [Failure Classification Protocol](references/failure-classification.md) for the failure taxonomy and report structure. Classify the sanitized strict result returned in the response, or `strict_result.json` when durable output was requested. No assertion metrics are produced.

For direct strict runs, use the same taxonomy with these mappings:
- Unexpected tool, missing call after the driver limit, skipped dependency, or invalid order → `AGENT_FAILURE`.
- SDK failure, timeout, unavailable agent, connection/authentication failure, or malformed tool response → `EXTERNAL_FAILURE`.
- Invalid graph or inconsistent strict fixture → `BAD_TEST_CASE / invalid_fixture`.
- A valid fixture using matching strategies other than `ignore` → report unsupported without a live run.
- Missing runtime entity required by a success scenario → `BAD_TEST_CASE / stale_data`. An expected not-found response in an intentional negative test is not a failure.
- Assertion inconsistencies may be flagged for separate semantic review; they do not change the tool-chain verdict. This skill does not score assertions.

---

# REPORT

## Trigger when
- Classification is complete.

Present results in this order:
1. **Strict-run table** — test case, run status, matched tool steps, and result path when a file was requested.
2. **Failure classification table** — one row per failing test: name, classification, confidence, reason.
3. **Aggregate summary block** — total failure counts per class.
4. If any `BAD_TEST_CASE` failures exist, proceed to REMEDIATE.

---

# REMEDIATE

## Trigger when
- One or more test cases were classified as `BAD_TEST_CASE`.

During this phase, read [Failure Classification Protocol — Bad Test Case Remediation](references/failure-classification.md#bad-test-case-remediation) for detailed guidance on:
- Listing the affected test file paths.
- Offering to re-open the `wxo-test-case-generation` skill to regenerate those tests with current data.
