"""
ibm_watsonx_orchestrate mock — 로컬 단위 테스트용
실제 WxO ADK 없이 @tool 데코레이터가 동작하도록 stub.
"""
import sys
from types import ModuleType
from enum import Enum


class ToolPermission(str, Enum):
    READ_ONLY = "READ_ONLY"
    WRITE_ONLY = "WRITE_ONLY"
    READ_WRITE = "READ_WRITE"
    ADMIN = "ADMIN"


def tool(permission=ToolPermission.READ_ONLY, expected_credentials=None):
    """No-op decorator for local testing."""
    def decorator(fn):
        return fn
    return decorator


# Build mock module hierarchy
def _make_module(name):
    m = ModuleType(name)
    sys.modules[name] = m
    return m


wxo = _make_module("ibm_watsonx_orchestrate")
ab = _make_module("ibm_watsonx_orchestrate.agent_builder")
tools_mod = _make_module("ibm_watsonx_orchestrate.agent_builder.tools")
tools_mod.tool = tool
tools_mod.ToolPermission = ToolPermission

conn_mod = _make_module("ibm_watsonx_orchestrate.agent_builder.connections")

class ConnectionType(str, Enum):
    API_KEY_AUTH = "api_key_auth"

class ExpectedCredentials:
    def __init__(self, app_id, type):
        self.app_id = app_id
        self.type = type

conn_mod.ConnectionType = ConnectionType
conn_mod.ExpectedCredentials = ExpectedCredentials

run_mod = _make_module("ibm_watsonx_orchestrate.run")
conns_sub = _make_module("ibm_watsonx_orchestrate.run.connections")
run_mod.connections = conns_sub
