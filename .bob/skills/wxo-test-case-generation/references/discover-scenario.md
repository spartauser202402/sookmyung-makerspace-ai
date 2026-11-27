---
name: discover-scenario
description: The skill uses local agent definition, tool definition, agent artifacts, and the initial user query to provide to the end user scenarios that the test case should cover for the target agent.
---

Start with the target agent's agent definition, its tools, and the initial user query from the `SKILL.md`. 

---

## Protocol
1. Inspect the complete tool list.
2. Cluster the tools into 3–5 user-meaningful **scenario families**.
3. Probe representative tools by inspecting their schemas and, where possible, calling them with valid sample inputs from available agent artifacts or context.
4. Record the response class for each probed tool call: `success`, `empty`, `not_found`, or `error`.
5. If **any** probed call returns `empty`, `not_found`, or `error`, mark the scenario family as **adversarial-eligible** and set `adversarial_trigger: true` in its persisted shape.
6. Present the scenario families to the user, noting which ones have adversarial-eligible coverage.
7. Persist the scenario families in the test-generation draft.
8. Wait for the user to select one or more scenarios.

Do not call the final test-generation tool yet.

---

## Adversarial Trigger Detection

During tool probing (steps 3–4 above), treat a tool response as an adversarial trigger when **any** of the following conditions are true:

| Condition | Examples |
|---|---|
| Response body is empty or null | `{}`, `[]`, `null`, `""` |
| Response contains a not-found or zero-result indicator | `"employees": []`, `"result": null`, `"count": 0` |
| Response carries an error code or error message | HTTP 4xx/5xx, `"error": "..."`, `"status": "failed"` |
| A required lookup step returns no matching entity | employee not found, ticket not found, account not found |
| A dependent tool call cannot proceed because a prior tool returned no data | chained call blocked by empty upstream result |

When a trigger is detected, do **not** discard the scenario family. Add it to the list as an adversarial-eligible family (or flag the existing family with `adversarial_trigger: true`). Adversarial scenarios test how the agent handles failure — they are as important as happy-path scenarios.

## Scenario Family Rules

A scenario family represents a coherent user objective or workflow.

Group tools by:

- user goal;
- business capability;
- common entities;
- natural workflow chains;
- related read/write operations;
- tools likely to participate in the same interaction.

Do not create one scenario per tool.

### Example

Tools:

```text
find_employee
get_employee_profile
get_vacation_calendar
get_company_holidays
get_pay_statement
get_benefits
request_time_off
approve_time_off
```

Good scenario families:

```text
1. Time off & holidays
2. Employee information
3. Payroll
4. Benefits
5. Manager approvals
```

Bad scenario families:

```text
1. find_employee
2. get_employee_profile
3. get_vacation_calendar
```

A tool may belong to multiple scenario families when appropriate.

## Scenario Shape

Persist each scenario using:

```json
{
  "id": "time-off",
  "title": "Time off & holidays",
  "description": "Vacation schedules, company holidays, and leave-related workflows.",
  "relevant_tools": [
    "find_employee",
    "get_vacation_calendar",
    "get_company_holidays",
    "request_time_off"
  ],
  "example_goals": [
    "Retrieve an employee's vacation calendar",
    "Compare leave with company holidays"
  ],
  "adversarial_trigger": false,
  "adversarial_trigger_reason": null
}
```

Set `adversarial_trigger: true` and populate `adversarial_trigger_reason` with a one-sentence description of the observed failure whenever a probe result matches any [Adversarial Trigger Detection](#adversarial-trigger-detection) condition. Example:

```json
{
  "id": "employee-lookup-not-found",
  "title": "Employee lookup — not found",
  "description": "Test agent behavior when a requested employee does not exist.",
  "relevant_tools": [
    "find_employee",
    "get_employee_profile"
  ],
  "example_goals": [
    "Look up an employee who does not exist in the system",
    "Request a profile for an unknown employee ID"
  ],
  "adversarial_trigger": true,
  "adversarial_trigger_reason": "Probing find_employee with a sample ID returned an empty result set."
}
```

## User-Facing Response

Prefer:

> This agent supports several useful test areas:
>
> 1. **Time off & holidays** — vacation calendars, holidays, and leave workflows.
> 2. **Payroll** — pay statements and compensation-related requests.
> 3. **Benefits** — benefits and eligibility queries.
> 4. **Employee information** — employee and organizational lookup.
> 5. ⚠ **Employee lookup — not found** *(adversarial)* — agent behavior when an employee does not exist.
>
> Pick one or more and I'll suggest concrete tests. Adversarial families are marked ⚠ — they test that the agent handles missing or failed data gracefully without fabricating a response.

Do not overwhelm the user with the full tool inventory.

When presenting adversarial-eligible families, prepend ⚠ to the title and include a one-line explanation of the trigger that was detected. Do not hide adversarial families — surface them alongside regular families so the user can choose to cover failure paths.