# Story Review — Post-Validation Subagent Review Protocol

Execute this review **after** the direct tool-chain validation via the Orchestrate MCP `chat_with_agent` tool has succeeded or completed. Do not run this review before validation.

Spawn a subagent using the `spawn_subagent` tool to independently critique and refine the `story` against the observed interaction trajectory and quality criteria.

## Inputs Provided to Subagent

Provide the subagent with the following context:

- **Observed interaction trajectory**: sequence of tool calls made, tool arguments and responses, and final assistant message from the completed `chat_with_agent` validation run.
- **User's objective**: what the user originally requested.
- **Candidate story**: the `story` field from the draft test case.
- **Scenario context**: scenario ID, intent, and any adversarial/negative-case flags.

## Quality Criteria Checklist

The subagent evaluates the `story` against these criteria:

1. **Required information**: Does the `story` contain every input the user must supply to reproduce the validated tool chain? Cross-checked against actual tool arguments observed during validation.
2. **User-centered**: Does the `story` describe the user's objective and expected outcome without mentioning runner mechanics, test infrastructure, or internal system details?
3. **No tool mechanics**: Does the `story` avoid naming specific tools, parameter names, or step sequences?
4. **Negative intent (adversarial / edge cases only)**: If the scenario is adversarial or negative, does the `story`:
   - Explicitly identify the intentional edge case or error condition?
   - Distinguish the expected negative result from stale or missing test fixture data?
   - State any behavior the agent must **not** perform (e.g. must not fabricate data)?
   - Avoid implying a successful positive outcome when testing an error or edge case?

## Subagent Invocation Pattern

Call `spawn_subagent` with `name: "general"` and a prompt structured as follows:

```text
Review and refine the candidate test case story based on the observed execution trajectory.

Context:
- User Objective: <user_objective>
- Scenario: <scenario_id> (Adversarial: <true|false>)
- Candidate Story: <candidate_story>
- Observed Trajectory:
  Tool Calls: <observed_tool_calls_and_args>
  Tool Responses: <observed_tool_responses>
  Final Message: <final_assistant_message>

Quality Criteria:
1. Required information: Contains all inputs required by the user to reproduce observed tool calls.
2. User-centered: Focuses on user objective, no runner or testing jargon.
3. No tool mechanics: No tool names, parameter payloads, or step sequences.
4. Negative intent: If adversarial, clearly declares intentional edge case and non-fabrication constraint.

Output Format:
Return a JSON object:
{
  "status": "pass" | "rewrite",
  "critique": "<concise explanation of findings>",
  "story": "<original story if pass, or rewritten story if rewrite>"
}
```

## Post-Subagent Action

1. If the subagent returns `"status": "rewrite"`, update the `story` in the candidate test case with the returned `story`.
2. Keep a one-line summary of the review outcome (status and critique) to include in the final summary.
3. Proceed to the [Assertion Review](assertion-review.md) subagent pass.
