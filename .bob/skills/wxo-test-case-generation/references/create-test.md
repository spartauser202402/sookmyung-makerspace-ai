# Creating a Unified Test

Create one unified test case directly from the selected agent, registered tools, scenario, and clarified inputs. The test case has two parts in one JSON file:

- `tool_call` steps in `goal_details`, with their dependency graph in `goals`;
- `assert_llm` assertions in `goal_details`, which check the outcome and the policy of the conversation.

Do not create a separate assertion-based candidate or a `candidate.json` file. Do not add a `summarize` step. The `assert_llm` assertions replace it.

## Test case structure

```json
{
  "agent": "<name>",
  "goals": {
    "first_tool": []
  },
  "goal_details": [
    {
      "name": "first_tool",
      "tool_name": "first_tool",
      "type": "tool_call",
      "args": {"input": "expected value"},
      "arg_matching": {"input": "ignore"}
    },
    {
      "type": "assert_llm",
      "kind": "observed",
      "scope": "conversation",
      "check": "Agent completed the task requested in the story and told the user the outcome."
    }
  ],
  "story": "",
  "starting_sentence": ""
}
```

`goals` lists only `tool_call` steps. `assert_llm` entries have no `name` and never appear in `goals`.

### Story and starting sentence

The `story` must contain the user's objective and every input needed to drive the intended tool chain. Keep it user-centered; do not describe the runner or matching strategy.

The `starting_sentence` is the user's natural first message. Keep it concise and general. Details may be supplied by Bob's follow-up tool instructions from the story and selected scenario.

### Tool steps and arguments

Select only registered tools needed for the scenario. Remove routing events such as `transfer_to_*`. Preserve the intended dependency order and name repeated calls `tool_name_1`, `tool_name_2`, and so on while retaining the actual `tool_name`.

For every tool step:

- preserve the expected arguments in `args`;
- create an `arg_matching` key for every argument;
- set every `arg_matching` value to `ignore`.

`ignore` means Bob includes the expected argument in the driver instruction but does not compare the runtime value. It does not mean the argument may be omitted from the test case or the instruction.

### Dependency graph

`goals` maps each tool step to its successors:

- If B depends on A, write `"A": ["B"]`.
- Independent steps do not depend on each other. Write `"A": []` and `"B": []`. Their execution order is not asserted.
- A terminal tool step (a step with no successors) points to `[]`.
- Do not add a `summarize` node. Do not point any step to `"summarize"`.
- Every `tool_call` step in `goal_details` must appear in `goals`, and every graph name must appear in `goal_details`.

For chained tools, preserve the expected argument in the later step even when it was derived from an earlier response. Bob keeps the same conversation thread and includes that expected argument when asking the target agent to execute the later step.

### Assertions

Add `assert_llm` entries to `goal_details` after the `tool_call` steps. Each entry has this shape:

| Field | Value |
|---|---|
| `type` | Always `"assert_llm"`. |
| `kind` | `"observed"` or `"policy"`. |
| `scope` | `"conversation"` (default) or `"response"`. |
| `check` | One clear sentence that an LLM judge can answer as pass or fail. |

No other fields are allowed.

Rules:

- Write at least one `observed` assertion for the main outcome in the `story`.
- Add `policy` assertions only for real constraints in the scenario, such as data the agent must not ask for or actions the agent must not take.
- Use `scope: "response"` only for a requirement on the final assistant message. Use `conversation` for all other checks.
- Check the outcome and the behavior. Do not name tools or tool arguments in `check`; the `tool_call` steps already cover them.
- Do not require exact wording or values that change between runs, such as generated passwords or request IDs.
- Do not require details from earlier steps in the final message. The last message can recap every step in one run and only confirm the last action in another run.

See [Strict Test Case](strict-test.md#step-5--add-the-assert_llm-assertions) for the full construction rules.

## Direct validation

1. Write the draft to `.tmp/test-generation/strict_candidate.json`. This file name stays the same for the unified format.
2. Run the format check:

```bash
python skills/wxo-test-case-generation/scripts/format_check.py \
  --path .tmp/test-generation/strict_candidate.json
```

3. Run the direct protocol in [Evaluation Protocol — Strict Test Evaluation](../../wxo-validate-test-case/references/evaluation-protocol.md#strict-test-evaluation).
4. Bob Shell calls the Orchestrate MCP `chat_with_agent` tool with the `starting_sentence`, preserves the returned `thread_id`, and asks the target agent to execute the `goal_details` tool steps with their expected arguments. Tool responses remain in the same thread for chained steps.
5. After each `chat_with_agent` call, inspect the reasoning trace `steps` for tool responses. If any tool response in the trace contains an error or not-found indicator (e.g. `error_code`, `"error": "..."`, `"status": "failed"`, an empty result, or a not-found message) **and** the story describes a successful outcome, pause and ask the user via `ask_followup_question`:
   - **Option A — Negative test**: keep the fixture as-is and reframe the story so the expected outcome is graceful failure (agent reports the error, does not fabricate data).
   - **Option B — Replace the fixture**: swap the fixture ID for one that produces a successful tool response and regenerate.
   Do not silently proceed or silently revise the test when this conflict is detected. If the tool failure is consistent with the story's intent (i.e. the story already describes an error or not-found scenario), no prompt is needed — continue as normal.
   If the graph or direct run fails for any other reason, classify the failure using the strict protocol and revise the test JSON only when the evidence shows a bad fixture.
6. If the user requests changes, update the JSON, rerun only the format check and direct validation, and present the new result.

## Post-Validation Review

Execute this step immediately after the direct validation run succeeds or completes. Do not skip this step and do not run it before validation.

1. **Story Review (Subagent)**: Call `spawn_subagent` to execute [Story Review](story-review.md) against the observed interaction trajectory (tool calls, tool responses, final assistant message). Update the candidate `story` field if the subagent returns a rewritten story.
2. **Assertion Review (Subagent)**: Call `spawn_subagent` to execute [Assertion Review](assertion-review.md) against the observed trajectory and reviewed story. Update `goal_details` with the subagent's revised `assert_llm` entries.
3. If either subagent review produces changes, update `.tmp/test-generation/strict_candidate.json` with the revised content. Do not rerun the format check or direct validation unless a structural change was made.

## User review and saving

Present the test JSON as a clickable file link and report the direct-run status, matched tool-step count, the `assert_llm` assertions (kind, scope, and check), and sanitized result path.

Once the user approves the test or indicates no further changes are needed, ask where to save it. Suggest `proposals/{scenario_id}/` when appropriate.

Save the approved test to:

```text
{output_folder}/{scenario_id}/test-{proposal_id}.json
```

After saving all approved tests and completing any requested uploads, write the [final summary](#final-summary).

## Upload

Only upload the test case when the user requests upload or approves the upload step. Use only the Orchestrate MCP `upload_test_case` tool.

Resolve the target agent UUID and pass the saved test JSON path within `WXO_MCP_WORKING_DIRECTORY`. Follow the connected tool's current input schema (`agent_id` and `file_path`).

If the tool is unavailable or cannot be invoked, retain the saved test file and report the upload as blocked. If the service rejects the upload, retain the saved file, report the upload as failed, and address the reported cause, such as invalid JSON or an authentication error, before retrying through MCP.

If an MCP call times out or loses its connection after submission, verify whether the upload succeeded before trying another upload. If the outcome cannot be verified, report it as unconfirmed and stop uploading that file. Report success only after MCP confirms it. Keep credentials out of committed files and the summary.

## Final summary

At the end of the request, generate and save one `{output_folder}/summary.md` covering all scenarios and saved test cases from that request. Write it after all approved tests are saved and any requested uploads have finished. Generate the Markdown directly from the selected scenarios and actual saved files.

Use simple English, short sentences, and these sections:

- **Scenarios chosen:** Explain what each selected scenario covers and why it was chosen.
- **Test cases created:** For each saved test, explain what it checks and the expected outcome. Make clear which scenario it belongs to.
- **Review notes:** For each test case, give one line on the story review and assertion review outcomes (status and a short critique).
- **Saved files:** Give the exact saved location and a clickable file link for every test case.

Do not present drafts or failed saves as completed tests. If some work could not be completed, briefly state what remains unfinished. Do not claim assertions passed when only tool-call validation was performed. If an upload was requested, briefly report its confirmed outcome.

Use readable scenario and test names in the prose. Keep raw JSON, hashes, internal IDs, trace details, credentials, and private reasoning out of the summary. File paths should retain their actual names so the user can find them.

If `summary.md` already exists from an earlier request, preserve its content and append a clearly labeled section for the current request. Check that every linked test file exists before finishing. Include a clickable link to the saved `summary.md` in the final response.
