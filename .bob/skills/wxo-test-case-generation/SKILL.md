---
name: wxo-test-case-generation
description: The skill uses local agent definition, tool definition, agent artifacts to generate test cases for the target agent.
---

# Test Case Generation 

Use this skill for every request that involves discovering test scenarios, proposing test cases, clarifying test-case intent, selecting proposed tests, or generating test cases for an agent.

## Environment check (run first)

Before gathering context or starting the workflow, follow [Preflight environment check](references/preflight-env-check.md) to choose the project interpreter and run the shared check once for this request. Continue only on success, and use the same interpreter for subsequent Python commands.

The user's initial request may be extremely sparse. The target agent may expose many tools across unrelated capabilities.

The user also may provide additional files like support ticket or github issues that have been raised against their agent. 
Additionally, the end user may provide checklists in the form of spreadsheets, docs, etc. that track expected behavior for their agent.
When such information is provided by the user, use it as context to inform the test case generation flow.

The goal of this skill is to progressively guide the user from:

1. broad agent capabilities;
2. to scenario families;
3. to concrete proposed test cases;
4. to any important semantic clarification;
5. to a generated test case.

Optimize for:
- low user effort;
- fast time to first useful proposal;
- meaningful scenario coverage;
- minimal clarification;
- valid structured test-case output;
- reuse of previous user selections.

Do not turn test generation into a form-filling exercise unless important information genuinely cannot be inferred or parameterized.

---

# Context Gathering (ALWAYS REQUIRED)

Before beginning the test case generation process, gather the appropriate context. 

**Gather the following context:**
1. In the current directory, find the target agent definition file (usually a `.json` or `.yaml`) or the agent code.
    - If unclear, ask the user if they can provide the agent definition file or path to the code file.
    - If user does not provide it, move on and inform the user the test case generation might be less accurate.
2. In the current directory, find the tools registered to the agent.
    - If unclear, ask the user if they can provide the tool definition file or path to the tools code.
3. Use any files that the user **explicitly** provides. **Do not** scan the repository and pick up previous notes, todos, or misc. files.


---

# Core Interaction Model

Use the following conceptual flow:

```text
Target agent
    ↓
Scenario families
    ↓
Proposed test cases
    ↓
Selected test
    ↓
Important semantic clarification, if needed
    ↓
Structured test generation
```

This is not a mandatory wizard.

Skip directly to the furthest stage justified by the user's request including any provided files such as support tickets, GitHub issues, spreadsheets.

Examples:

- `"Generate a test case"` → discover scenario families.
- `"Generate a vacation-related test"` → propose tests inside the vacation scenario.
- `"Test get_weather"` → clarify only if needed, otherwise generate.
- `"Test get_weather for New York and expect temperature and conditions"` → generate immediately.

---

# Phase Classification

Before calling the generation tool, determine the current phase.

Possible phases:

- `DISCOVER_SCENARIOS`
- `PROPOSE_TESTS`
- `CLARIFY`
- `GENERATE`

The phase is determined from the user's current request plus prior test-generation context.

---

# Discover Scenarios 
## Trigger 

Use when:

- an agent is known or can be resolved;
- the user wants test cases, but the user has not supplied a meaningful scenario, capability, tool, or expected behavior.

Examples:

- `"Generate a test case for my agent"`
- `"Create some tests"`
- `"What should I test for the HR agent?"`

When this stage is triggered, read [Discover Scenario Stage](references/discover-scenario.md) on guidance.

---

# PROPOSE_TESTS

## Trigger

Use when:

- the user has selected one or more scenario families; or
- the user named a capability but not a concrete test;
- the request is specific enough to identify a scenario but not a particular interaction.

Examples:

- `"Time off"`
- `"Give me some payroll tests"`
- `"Test the vacation functionality"`
- `"Something involving employee lookup"`

When this stage is triggered, read [Propose Test Stage](references/propose-test.md) on guidance.

---

# CLARIFY 
## Trigger when 
- Clarity is needed for test semantics.
- The missing information is a test-defining input.

When this stage is triggered, read [Clarification-Protocol](references/clarification-protocol.md) on guidance.

---

# GENERATE
## Trigger when
- the initial user request to generate a test case contains all the test defining inputs
- the test has been selected and undergone the appropriate clarification steps.

During this stage, Bob generates one unified test case. The test case has `tool_call` steps and `assert_llm` assertions in `goal_details`, and the tool dependency graph in `goals`.

1. Generate one unified test case directly from the selected scenario, target-agent tools, and clarified inputs. Do not create a separate assertion-based candidate. Do not add a `summarize` step.
2. Build the intended tool chain in `goals` and `goal_details`, including dependency edges for chained calls. A terminal tool step (a step with no successors) points to `[]` in `goals`.
3. Preserve every expected tool argument in `args`, but set every `arg_matching` value to `ignore`.
4. Add `assert_llm` assertions (`kind`, `scope`, `check`) to `goal_details`. Do not put assertions in `goals`; assertions have no `name`.
5. Run the format check, then validate the test through Bob Shell's Orchestrate MCP `chat_with_agent` protocol. Do not perform an assertion-based dry-run.
6. After validation, run the post-validation reviews using `spawn_subagent` on the observed conversation. Run [Story Review](references/story-review.md) first via subagent. Then run [Assertion Review](references/assertion-review.md) via subagent. Revise the `story` and the `assert_llm` entries based on the subagents' evaluations. Do not run these reviews before validation.
7. Present the reviewed test case and the direct-run result to the user. If the user requests changes, update the test case and repeat the format check and the direct tool-call validation.
8. Keep proposals and drafts in the active generation context. After the user confirms the final test, prompt for a save location and write the test case file.
9. When the user requests or approves upload, use only the Orchestrate MCP `upload_test_case` tool. Follow [Upload](references/create-test.md#upload) for agent resolution, saved-file access, and upload outcome handling.
10. At the end of the request, after all approved test cases are saved and any requested uploads finish, generate one `{output_folder}/summary.md`. In simple English, explain the scenarios chosen and why, the test cases created and what each checks, and exactly where each test file was saved. Include clickable file links. Follow the summary instructions in [Create-Test](references/create-test.md#final-summary).

When this stage is triggered, read [Create-Test](references/create-test.md)
