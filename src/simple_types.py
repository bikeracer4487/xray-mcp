"""Simple types for Xray operations - no over-engineered schemas."""

from typing import Dict, Any, List, Literal, TypedDict

# Simple type aliases - no Pydantic bloat
IssueId = str
ProjectKey = str
TestType = Literal["Manual", "Generic", "Cucumber"]
TestRunStatus = Literal["PASS", "FAIL", "EXECUTING", "TODO", "BLOCKED", "ABORTED"]

# Simple TypedDict for return values - FastMCP handles validation
class XrayResult(TypedDict):
    success: bool
    data: Dict[str, Any] | None
    warnings: List[str]
    errors: List[str]

# Entity types
EntityType = Literal["test", "test_execution", "test_plan", "test_run"]

# Common action types
ActionType = Literal[
    "create", "get", "list", "delete",
    "update_status", "update_comment", "update_type", "update_content",
    "add_tests", "remove_tests", "add_environments", "remove_environments",
    "add_defects", "add_evidence"
]

# Test step structure for Manual tests
class TestStep(TypedDict):
    action: str
    data: str
    result: str