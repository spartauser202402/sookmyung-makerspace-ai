# Evaluation Protocol

This reference defines the direct validation protocol for the unified test case. Bob Shell validates a generated test by using the Orchestrate MCP `chat_with_agent` tool to ask the target agent to execute the declared tools with the expected arguments. Do not perform an assertion-based dry-run.

The test JSON must contain one or more `tool_call` steps in `goal_details`, with their dependency graph in `goals`. It has no `summarize` step. It can also contain `assert_llm` entries in `goal_details`. This protocol does not evaluate `assert_llm` entries; it only confirms that they are well formed. All generated arguments use `ignore` matching: the expected values guide Bob's instructions, but are not compared against the values emitted by the target agent.

## Step 1 — Confirm input and output

Determine whether the user provided one strict `.json` file or a directory of strict files. Return the result on stdout unless the user supplied an output directory. Read connection settings from the configured Bob Shell/MCP environment and do not ask the user to repeat them.

## Strict Test Evaluation

Use this path for every generated strict test. Bob Shell's directed MCP conversation is the validation; it does not produce assertion metrics.

### 1. Load and validate the strict fixture

Read the strict JSON and run the existing format check before contacting the live agent:

```bash
python skills/wxo-test-case-generation/scripts/format_check.py \
  --path path/to/test-example-strict.json
```

Then validate the graph represented by `goals` and `goal_details` in memory. Confirm that assertions use valid `kind` and `scope` values and a non-empty `check`; omitted `scope` defaults to `conversation`:


1. Every `goal_details` entry that has a `name` appears exactly once in `goals`.
2. Every key and successor in `goals` names a declared `tool_call` step.
3. A terminal tool step (a step with no successors) points to `[]`. No step points to `summarize`, and no `summarize` step exists.
4. Every named step has `type: "tool_call"`, a `tool_name`, `args`, and `arg_matching` keys that match `args`.
5. Every `assert_llm` entry is present in `goal_details`, has no `name`, and is not listed in `goals`. It has only the fields `type`, `kind`, `scope`, and `check`.
6. The graph is acyclic.
7. Every argument has `ignore` matching. Handle other strategies as unsupported before contacting the agent, as described below.
8. Repeated calls use distinct step names such as `lookup_employee_1` and `lookup_employee_2`, while retaining the same `tool_name`.

If a structural check fails, stop before the live call and classify the fixture as `BAD_TEST_CASE / invalid_fixture`. An otherwise valid fixture using an unsupported matching strategy is not an agent failure; report it as unsupported without a live run.

### 2. Start the target-agent conversation

Use Bob Shell's Orchestrate MCP `chat_with_agent` capability:

```text
chat_with_agent({
  "agent_name": <test.agent>,
  "message": <test.starting_sentence>,
  "include_reasoning": True
})
```

Start a fresh conversation for every strict test. Save the returned `thread_id` and pass it to every follow-up call. Do not reuse a thread from another test.

Inspect the initial response before sending a driver instruction. If it already contains an expected tool call, match it normally. Otherwise, Bob sends a driver instruction for the next runnable `goal_details` step. Unexpected registered tool calls remain in the trace and make the run fail; they must not be replaced by a later successful call.

### 3. Normalize tool events

Extract structured tool-call and tool-response events from the `chat_with_agent` result. Do not persist private reasoning. Normalize each registered tool event to:

```json
{
  "sequence": 1,
  "step_name": "lookup_employee",
  "tool_name": "lookup_employee",
  "args": {"employee_id": "E1001"},
  "response": {"account_id": "ACCT-7K9X3M2N"},
  "call_id": "..."
}
```

Match responses by `call_id`, never by list position. Routing events such as `transfer_to_*` may be recorded for context but are not strict tool steps. Redact credentials, tokens, passwords, and other secret-bearing values before writing the run result.

If the SDK does not return a usable thread ID or structured tool events, classify the run as `EXTERNAL_FAILURE`; do not guess from unstructured assistant text.

### 4. Match calls against the dependency graph

Maintain a per-run state containing:

- completed step names;
- observed normalized events;
- the current `thread_id`;
- the final assistant response;
- the first failure, if any.

A step is runnable when all of its graph predecessors are complete. Match an observed registered tool call to one runnable step with the same `tool_name`; for repeated tool names, choose the earliest still-runnable step in `goal_details` order.

All tool-step arguments must use `ignore` matching in this workflow. Preserve expected and observed arguments and responses in the sanitized trace, but do not compare argument values or classify a value difference as an agent failure. If an existing fixture uses another strategy, stop before the live call and explain that it requires a different evaluator or an explicitly approved fixture update; do not silently convert it.

Independent sibling steps may complete in either order. A dependent step cannot match until its predecessors complete. An unexpected registered tool, duplicate call, skipped dependency, or invalid order is an `AGENT_FAILURE`; continue only when doing so can collect additional diagnostic events.

### 5. Drive missing steps through the same thread

After each response, send a follow-up using the saved `thread_id` for the next runnable step that has not yet been matched. Select the first runnable step in `goal_details` order and use a driver instruction equivalent to:

```text
Continue the same user task. For this evaluation step, call the <tool_name> tool now.
Use these expected arguments: <args>. The values are guidance for this
execution and are not value assertions. Use the preceding tool response when
the task requires it. Do not call an unrelated tool.
```

Include every expected argument in the instruction, including arguments with `ignore` matching. The preceding tool response remains available because all turns use the same thread. For chained calls, Bob must preserve the expected argument value in the instruction even when the value was derived from an earlier step.

Record both the original missing-call condition and the follow-up result. A follow-up cannot repair an already-recorded unexpected initial call.

Repeat until all tool steps are complete, the target agent returns an unrecoverable error, or the run reaches the configured conversation-turn limit. Use a limit of `2 * number_of_tool_steps + 2`; exceeding it is an `AGENT_FAILURE` unless the SDK itself timed out or failed.

### 6. Record the final response and write the result

After the final expected tool response, record the latest assistant text as `final_response`. This protocol does not judge the final response against a summary step. The `assert_llm` entries are not evaluated here; when invoked by the generation skill, its separate post-validation Story Review and Assertion Review use `final_response` and the tool events to refine them. Standalone validation does not rewrite the test or evaluate assertions.

Return the sanitized result as the final Bob Shell response. If the user requested durable output, also write one result file under the configured output directory:

```text
<output-dir>/<run-id>/strict_result.json
```

The result must contain:

```json
{
  "test_case_id": "...",
  "agent": "...",
  "status": "passed|failed|external_failure|invalid_fixture",
  "classification": null,
  "failure_reason": null,
  "thread_id": "...",
  "step_results": [],
  "tool_events": [],
  "final_response": "..."
}
```

Do not include hidden reasoning, bearer tokens, passwords, or unrestricted raw SDK payloads. Bob Shell may use `--format json` for one machine-readable response or `--format stream-json` when the caller needs live tool events.

When starting Bob Shell non-interactively, keep MCP enabled and request JSON output so the caller receives the strict result without redirecting it to a file:

```bash
bob run --mode agent --format json --max-turns 12 \
  "Validate the strict test at path/to/test-example-strict.json using the Orchestrate MCP chat_with_agent tool. Preserve the returned thread_id for every follow-up, include_reasoning=true, drive every goal_details tool step with its expected args, validate the goals graph, record the final assistant response, and return only the sanitized strict result as JSON."
```

Bob Shell's `--format json` returns one machine-readable result object; `--format stream-json` can be used instead when the caller needs live MCP/tool events.

### 7. Report and classify failures

For a passed run, report the strict status, number of matched tool steps, and the result path only if a file was requested. Do not report assertion metrics.

For a failed run, apply the existing failure taxonomy:

| Evidence | Classification |
|---|---|
| Wrong tool, missing call after the driver limit, skipped dependency, or invalid order | `AGENT_FAILURE` |
| SDK error, timeout, unavailable agent, authentication/connection failure, or malformed/missing tool response | `EXTERNAL_FAILURE` |
| Invalid graph or inconsistent repeated-step fixture | `BAD_TEST_CASE / invalid_fixture` |
| Runtime entity required by a success scenario is not found | `BAD_TEST_CASE / stale_data` |


Preserve the sanitized evidence needed for classification in `tool_events` and `step_results`, then use the existing classification protocol for the user-facing report.

An intentional negative test may pass when a tool returns its expected not-found or rejection response. Judge that response against the stated scenario intent before assigning stale data or external failure. Unexpected transport, authentication, or service failures remain external failures.

For passed runs, `classification` and `failure_reason` are null. For failed runs, populate both from the observed evidence. Assertion concerns may be reported separately as unscored review notes and must not turn a passed tool chain into a failed run.
