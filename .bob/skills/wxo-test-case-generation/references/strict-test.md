# Strict Test Case (Unified Format)

Generate one unified test case directly from the selected scenario and registered tools. It is the only generated test case; do not create a separate assertion-based candidate.

The unified test is a classical AgentOps test case. It declares which tools Bob must ask the target agent to call, the expected arguments to include in those instructions, the dependency graph (`goals`), and `assert_llm` assertions about the outcome. Every argument uses `ignore` matching so the run checks tool execution and chaining without asserting runtime argument values.

The unified format has no `summarize` step. Terminal tool steps point to `[]` in `goals`. The `assert_llm` entries in `goal_details` check the final outcome.

---

## Inputs

| Input | Source |
|---|---|
| Scenario inputs and expected tool chain | The selected scenario, clarified user inputs, target-agent tool definitions, and any explicit expected outcome. |
| `agent`, `story`, `starting_sentence` | The generated strict test. |
| Registered tool names | The tool definitions found in Context Gathering. |

---

## Step 1 — Select the tool calls

1. Select the registered tools required to complete the user story.
2. Remove routing calls such as `transfer_to_*`; they are not test steps.
3. Keep the intended dependency order from the scenario and tool contracts.
4. If the story can be completed without a registered tool, do not create a strict test; tell the user that no registered tool step was identified.

## Step 2 — Name the steps

| Case | `name` | `tool_name` |
|---|---|---|
| Tool is called once | The tool name | The tool name |
| Tool is called more than once | The tool name with `_1`, `_2`, and so on | The tool name, unchanged |

## Step 3 — Set the arguments and matching

For every argument in every selected tool step, preserve the expected value in `args` and set its strategy in `arg_matching` to `ignore`. Bob includes the expected values when instructing the target agent, but the runner does not assert the values returned by the agent.

| Strategy | Use when | Example |
|---|---|---|
| `ignore` | Default for every argument. Use it when the test should not assert the runtime argument value. | `employee_id`, `account_id`, or `reason` |
| `strict` | Not used by this generation flow. | |
| `fuzzy` | Not used by this generation flow. | |
| `optional` | Not used by this generation flow. | |

Rules:

- Preserve the expected, non-null argument value in `args`; `ignore` disables value matching, but does not mean the parameter value should be omitted from Bob's tool instruction.
- Set every `arg_matching` value to `ignore`, including arguments copied from the story or from an earlier step's expected response.
- Do not use `strict`, `fuzzy`, or `optional` in generated strict tests.
- `arg_matching` keys must exist in `args`.

## Step 4 — Build the `goals` graph

`goals` maps each step name to the list of steps that come after it.

| Pattern | How to write it |
|---|---|
| Call B uses a value from call A | `"A": ["B"]` |
| Calls are independent | Each one points to `[]`. Order does not matter. |
| Terminal step (no successors) | `"<step>": []` |

Do not add a `summarize` node. Do not point any step to `"summarize"`.

Every `tool_call` name in `goal_details` must appear in `goals`. Every name in `goals` must appear in `goal_details`. `assert_llm` entries have no `name` and do not appear in `goals`.

## Step 5 — Add the `assert_llm` assertions

Add `assert_llm` entries to `goal_details` after the `tool_call` steps. Each entry has exactly these fields:

```json
{
  "type": "assert_llm",
  "kind": "observed",
  "scope": "conversation",
  "check": "<one clear, judgeable sentence>"
}
```

| Field | Allowed values | Meaning |
|---|---|---|
| `type` | `"assert_llm"` | Marks the entry as an assertion. |
| `kind` | `"observed"`, `"policy"` | `observed`: the agent reached a required outcome or did a required action. `policy`: the agent kept a negative constraint, a safety boundary, or a communication rule. |
| `scope` | `"conversation"` (default), `"response"` | `conversation`: the judge reads the whole conversation. `response`: the judge reads only the final assistant message. |
| `check` | Non-empty string | The requirement the LLM judge answers with pass or fail. |

No other fields are allowed. Do not add `name` to an `assert_llm` entry. The format check treats a named entry as a graph step and fails with `goal_details contains names not in goals`.

### How to construct each entry

1. **Outcome assertion (required).** Write at least one `observed` assertion that states the main outcome of the `story`. Use `conversation` scope.
2. **Final message assertion (optional).** Use `scope: "response"` only when the story requires a specific statement in the final message. Write it for the part that is true in every run, which is usually the result of the last tool call. Do not require details from earlier steps.
3. **Policy assertions (optional).** Add `policy` assertions only for real constraints in the scenario. Examples: the agent must not ask for an internal ID, or must not act on a different account. Use `conversation` scope.
4. **Phrasing.** Write `check` in the past tense, from the point of view of the judge. Start with "Agent". Use one sentence. Describe one requirement per entry.
5. **No tool mechanics.** Do not name tools, tool arguments, or call order in `check`. The `tool_call` steps and `goals` already cover them.
6. **No unstable values.** Do not require exact wording or values that change on each run, such as a temporary password or a request ID.

Example:

```json
[
  {
    "type": "assert_llm",
    "kind": "observed",
    "check": "Agent reset the password for the account that belongs to employee E1001 and told the user how to sign in."
  },
  {
    "type": "assert_llm",
    "kind": "policy",
    "scope": "conversation",
    "check": "Agent did not ask the user for an internal account ID."
  }
]
```

If the post-validation review changes an assertion, follow [Assertion Review](assertion-review.md).

---

## Worked example

An intended chained tool plan may look like this (the terminal tool step `send_summary_email` points to `[]`):

| # | `tool_name` | `args` | Source of values |
|---|---|---|---|
| 1 | `lookup_employee_by_id` | `{"employee_id": "E1001"}` | `E1001` is in the story. |
| 2 | `reset_account_password` | `{"account_id": "ACCT-7K9X3M2N", "reason": "forgot password"}` | `account_id` is in the response of call 1. `reason` is free text. |
| 3 | `send_summary_email` | `{"email": "avery.chen@example.com", "summary": "..."}` | `email` is in the response of call 1. `summary` is long free text. |

Result:

```json
{
  "agent": "it_support_agent",
  "goals": {
    "lookup_employee_by_id": ["reset_account_password", "send_summary_email"],
    "reset_account_password": ["send_summary_email"],
    "send_summary_email": []
  },
  "goal_details": [
    {
      "name": "lookup_employee_by_id",
      "tool_name": "lookup_employee_by_id",
      "type": "tool_call",
      "args": { "employee_id": "E1001" },
      "arg_matching": { "employee_id": "ignore" }
    },
    {
      "name": "reset_account_password",
      "tool_name": "reset_account_password",
      "type": "tool_call",
      "args": { "account_id": "ACCT-7K9X3M2N", "reason": "forgot password" },
      "arg_matching": { "account_id": "ignore", "reason": "ignore" }
    },
    {
      "name": "send_summary_email",
      "tool_name": "send_summary_email",
      "type": "tool_call",
      "args": { "email": "avery.chen@example.com", "summary": "Password reset summary" },
      "arg_matching": { "email": "ignore", "summary": "ignore" }
    },
    {
      "type": "assert_llm",
      "kind": "observed",
      "scope": "conversation",
      "check": "Agent reset the password for employee E1001 and confirmed that a summary email was sent to the employee's email address."
    },
    {
      "type": "assert_llm",
      "kind": "policy",
      "scope": "conversation",
      "check": "Agent did not ask the user for an internal account ID."
    }
  ],
  "story": "You are employee E1001. You forgot your password. You want the IT support assistant to reset it and send you a summary email.",
  "starting_sentence": "I need help resetting my corporate password."
}
```

`send_summary_email` depends on `reset_account_password` because the email text uses the reset result. The argument values remain ignored by default, including values copied from an earlier response. `send_summary_email` is the terminal tool step, so it points to `[]`.

---

## Direct validation

1. Write the unified test to `.tmp/test-generation/strict_candidate.json`.
2. Run the format check:

```bash
python skills/wxo-test-case-generation/scripts/format_check.py --path .tmp/test-generation/strict_candidate.json
```

The format check imports `agentops`. If it fails with `circular import` on `AgentResponseExtractor`, run it with the workspace virtual environment (`.venv/bin/python`) instead of the global `python`.

The check fails when `goals` points to `summarize` but `goal_details` has no `summarize` step. Remove the `summarize` reference from `goals`.

3. Once the format check passes, run the direct strict protocol in [Evaluation Protocol — Strict Test Evaluation](../../wxo-validate-test-case/references/evaluation-protocol.md#strict-test-evaluation).
4. If the format check fails, correct the JSON and rerun only the format check. Do not change `story` or `starting_sentence`.
5. Present the test and direct-run result to the user. List the `assert_llm` assertions (kind, scope, check). Do not report assertion scores; the direct run does not score assertions.

## Direct strict-test evaluation

When the user asks to validate an existing strict test, use the direct Orchestrate chat path. Read [Evaluation Protocol — Strict Test Evaluation](../../wxo-validate-test-case/references/evaluation-protocol.md#strict-test-evaluation) before executing it.

The direct path starts a fresh Bob Shell conversation through the Orchestrate MCP `chat_with_agent` tool with the test case's `starting_sentence`, keeps the returned `thread_id`, and observes structured tool calls with `include_reasoning=True`. It validates the existing `goals` graph, preserves the initial unprompted behavior, and sends follow-up driver instructions for the next runnable expected call after each response.

For chained tools, the target agent receives each preceding tool response through the same conversation thread. Do not add response-to-argument binding fields to the strict JSON. Bob still includes every expected argument in the driver instruction, while `ignore` means the runtime value is not compared afterward.

Independent graph branches may complete in either order. Repeated calls retain distinct step names, and unexpected registered tools, wrong arguments, skipped dependencies, and invalid ordering are failures even if a later follow-up completes the remaining chain.

The direct run validates the `tool_call` graph. `assert_llm` entries are evaluated later by the AgentOps runner when the test is uploaded and run; they do not affect the graph check.
