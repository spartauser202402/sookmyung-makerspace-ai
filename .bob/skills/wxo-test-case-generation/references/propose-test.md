---
name: propose-test
description: The skill uses local agent definition, tool definition, agent artifacts, and the initial user query to propose to the end user tests cases for the target agent.


Start with the target agent's agent definition, its tools, and the initial user query from the `SKILL.md`. 

---

## Protocol

1. Use the selected scenario and relevant target-agent tools.
2. Check whether the selected scenario has `adversarial_trigger: true` (set during [discover-scenario](discover-scenario.md)). If yes, **one of the proposals must be an adversarial/negative test case** (see [Adversarial Proposals](#adversarial-proposals)).
3. Generate exactly 3 concrete test case proposals unless the scenario has fewer meaningful options or needs additional coverage to represent distinct risk categories.
4. Keep the proposals in the current test-generation draft/context; do not ask for an output folder or write files at this stage.
5. Present compact summary cards to the user (see [User-Facing Response](#user-facing-response)).
6. Using Bob's `ask_followup_question` tool, ask the user to select, combine, modify, or reject a proposal.

## Proposal Diversity

Include a mix of:

- basic happy path;
- multi-tool workflow;
- multi-entity interaction;
- edge case;
- ordering-sensitive interaction;
- **adversarial/negative** — required when the scenario has `adversarial_trigger: true`.

When `adversarial_trigger: true`, replace one of the three proposals with an adversarial proposal. Do not add a fourth proposal simply to preserve happy-path coverage — adjust the mix within the three slots.

## Proposal Shape

```json
{
  "id": "compare-vacation-calendars",
  "scenario_id": "time-off",
  "title": "Compare two employee vacation calendars",
  "description": "Verify that the agent retrieves vacation information for two employees and compares the results.",
  "user_prompt_template": "Compare the vacation calendars for {{employee_1}} and {{employee_2}}.",
  "expected_behavior": "Agent retrieves vacation information for both employees and summarizes the comparison.",
  "relevant_tools": [
    "get_vacation_calendar"
  ],
  "assumptions": [
    "{{employee_1}} and {{employee_2}} refer to valid employees."
  ],
  "adversarial": false
}
```

---

## Adversarial Proposals

An adversarial proposal tests graceful failure: the agent must respond accurately to a missing entity, empty result, or tool error without fabricating data.

### When to generate

Generate an adversarial proposal when:

- the selected scenario has `adversarial_trigger: true`; **or**
- the user explicitly requests a negative or error-handling test.

### Rules for adversarial proposals

1. Set `"adversarial": true` in the proposal shape.
2. State negative intent explicitly in the `title` — use language such as "not found", "unknown", "invalid", "missing", or "non-existent".
3. Write the `user_prompt_template` so that the agent will attempt a lookup that is expected to return no data or an error.
4. Set `expected_behavior` to describe graceful failure: the agent must report that the entity was not found or that an error occurred. It must **not** invent or assume data.
5. List the same tools as the happy-path scenario — the test validates failure handling inside those tools, not different tools.
6. Do not use a real identifier known to exist; use a symbolic placeholder such as `{{unknown_employee}}` or `{{nonexistent_id}}`.

### Adversarial proposal shape

```json
{
  "id": "employee-not-found",
  "scenario_id": "employee-lookup-not-found",
  "title": "Look up a non-existent employee",
  "description": "Verify that the agent correctly reports that no employee was found rather than fabricating a result.",
  "user_prompt_template": "Find the profile for {{unknown_employee}}.",
  "expected_behavior": "Agent reports that no employee matching the request was found. Agent does not fabricate an employee profile or invent data.",
  "relevant_tools": [
    "find_employee",
    "get_employee_profile"
  ],
  "assumptions": [
    "{{unknown_employee}} is a name or ID that does not exist in the system."
  ],
  "adversarial": true
}
```

## User-Facing Response

Render each proposal as two lines: a bold-numbered title and the prompt template. Nothing else.

Prefer:

**1. Compare two employee vacation calendars**
> `Compare the vacation calendars for {{employee_1}} and {{employee_2}}.`

One card per proposal, numbered sequentially. Separate cards with a blank line only — no `---` rules. Do not include description, `relevant_tools`, or `assumptions` in the chat output.

## Saving Proposals

Do not save proposals before the user selects a test. Proposal generation is exploratory and should not create repository files or require a destination from the user.

If the user explicitly asks to save the proposals without selecting a test, ask for an output folder and write the JSON array to:

```
{output_folder}/{scenario_id}/proposals.json
```

Otherwise, retain the proposals in the current test-generation draft/context and save only the approved test case during the final save step in [create-test](create-test.md).

## Runtime Values in Proposals

The tools may expose required arguments without exposing valid runtime values.

Examples:

- `employee_id`
- `account_id`
- `project_id`
- `document_id`
- `assignment_id`

Do not invent a concrete value and claim that it is valid.

Prefer symbolic proposal text:

```text
Show me the vacation calendar for {{employee}}.
```

over:

```text
Show me the vacation calendar for employee E-101.
```

unless `E-101` was supplied by the user or is otherwise known from context.


After resolving the selected proposal, reassess whether the test can be generated or requires further clarification. 

If further clarification is required, see [clarification-protocol](clarification-protocol.md)
If the test has enough information, see [create-test](create-test.md)
