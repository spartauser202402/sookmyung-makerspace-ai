# CLARIFY

## Clarify Test Semantics, Not Runtime Data

Do not ask solely because a required OpenAPI field lacks a known valid runtime value

## Required Parameter Clarification

Do not automatically ignore every unknown tool parameter.

For each required parameter whose value is not known, determine whether the
parameter is test-defining, opaque/derived, or runtime-generated. 

There are edge-cases where a tool's spec has empty defaults for the parameter values such as empty strings, `null` values, or a boolean value set to `False`. You can treat these parameters for a tool spec as required parameters. **Apply the same clarification logic for these parameters as you would for actual required parameters.**

### Test-Defining Inputs

A parameter is test-defining when its value would normally be supplied or
meaningfully chosen by the user and is necessary to make the test scenario
concrete.

Common examples include:

* username
* names (person's name, employee names, etc.)
* email address
* city
* country
* origin
* destination
* date or date range
* search query
* product name
* category
* amount

A parameter is more likely to be test-defining when:

1. it appears naturally in the user’s opening message;
2. changing its value produces a meaningfully different concrete test;
3. the value can reasonably be known or chosen by the test author;
4. the target agent would normally obtain the value from the user’s request;
5. the value is needed to construct a natural starting_sentence.

If a required test-defining parameter is unknown and no safe default exists,
ask the user for it.

Example:

if there is a tool, `get_orders(username)`, and the user says: "Generate a test for getting a user's orders.", then the preferred clarification is "Which username should the test use?".

### Opaque or Derived Inputs

A parameter is opaque or derived when it is primarily an implementation-level identifier rather than a meaningful choice made by the user.

Examples:

* employee_id resolved from an employee name
* assignment_id returned by another tool
* database record ID
* internal resource UUID
* pagination cursor

Do not ask the user for these values

