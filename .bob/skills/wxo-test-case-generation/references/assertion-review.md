# Assertion Review — Post-Validation Subagent Review Protocol

Execute this review **after** the direct tool-chain validation via the Orchestrate MCP `chat_with_agent` tool has succeeded or completed, and after the Story Review pass. Do not run this review before validation.

Spawn a subagent using the `spawn_subagent` tool to independently critique and refine the `assert_llm` entries against the observed interaction trajectory, refined `story`, and quality criteria.

## Inputs Provided to Subagent

Provide the subagent with the following context:

- **Observed interaction trajectory**: sequence of tool calls made, tool arguments and responses, and final assistant message from the completed `chat_with_agent` validation run.
- **Story field**: the `story` from the candidate test case (after any Story Review update).
- **Candidate assertions**: the list of `assert_llm` objects currently in `goal_details`.
- **Scenario context**: scenario ID, intent, and any adversarial/negative-case flags.

## Quality Criteria Checklist

The subagent evaluates each assertion against these criteria:

1. **Outcome and trajectory focus**: Does each assertion verify an end-to-end outcome or observable agent behavior from the validated run? (No checking events that never occurred).
2. **No tool mechanics**: Does the `check` avoid naming specific tools, parameter names, or step sequences?
3. **Correct kind**:
   - `observed`: Verifies that the agent achieved a required outcome or performed an observable action.
   - `policy`: Verifies that the agent respected a negative constraint, safety boundary, or communication rule.
4. **Correct scope**:
   - `conversation`: Asserts behavior across the multi-turn interaction or tool actions (default).
   - `response`: Asserts constraints strictly on the final assistant message only.
5. **Clear and definitive phrasing**: Is each `check` a single, unambiguous sentence evaluable as pass/fail by an LLM judge? (No variable runtime values like timestamps or generated IDs).
6. **Comprehensive coverage**: Do the assertions together fully cover the user's primary goal and any critical policy constraints in the story?

## Subagent Invocation Pattern

Call `spawn_subagent` with `name: "general"` and a prompt structured as follows:

```text
Review and refine the candidate test case assert_llm assertions based on the validated execution trajectory.

Context:
- Story: <reviewed_story>
- Scenario: <scenario_id> (Adversarial: <true|false>)
- Candidate Assertions: <candidate_assert_llm_json_list>
- Observed Trajectory:
  Tool Calls: <observed_tool_calls_and_args>
  Tool Responses: <observed_tool_responses>
  Final Message: <final_assistant_message>

Quality Criteria:
1. Outcome and trajectory focus: Verifies observable outcomes/behaviors, not internal mechanics.
2. No tool mechanics: No tool names, argument keys, or payload schemas in check text.
3. Correct kind: "observed" for positive outcomes/actions, "policy" for negative constraints/rules.
4. Correct scope: "conversation" for multi-turn behavior, "response" for final message only.
5. Clear and definitive phrasing: Single unambiguous sentence, no unstable runtime values.
6. Comprehensive coverage: At least one observed assertion for primary goal; policy assertions for key constraints.

Output Format:
Return a JSON object:
{
  "status": "pass" | "revised",
  "critique": "<concise explanation of findings>",
  "assertions": [
    {
      "type": "assert_llm",
      "kind": "observed" | "policy",
      "scope": "conversation" | "response",
      "check": "<assertion text>"
    }
  ]
}
```

## Post-Subagent Action

1. If the subagent returns `"status": "revised"`, replace the `assert_llm` entries in `goal_details` with the returned `assertions` list.
2. Ensure `tool_call` entries in `goal_details` and dependency mappings in `goals` remain intact.
3. Keep a one-line summary of the review outcome (status and critique) to include in the final summary.
4. Proceed to user review and presentation.
