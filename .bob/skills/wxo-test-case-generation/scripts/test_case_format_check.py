from typing import Any, Mapping

# Import order matters: GoalDetail lazily imports agentops.extractors.utils when
# a goal has args + arg_matching (strict tests). That import is circular unless
# agentops.simulation_result has been loaded first.
import agentops.simulation_result  # noqa: F401
from agentops.type import TestCase


def is_correct_format(proposed_test_case: Mapping[Any, Any]):
    return TestCase.model_validate(proposed_test_case)
