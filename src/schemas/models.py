"""Pydantic models for validating Xray MCP server parameters."""

from typing import List, Optional, Literal
from pydantic import BaseModel, Field, field_validator


class StepInput(BaseModel):
    """Model for manual test steps.

    Each step must have an action, data, and expected result.

    Example:
        {
            "action": "Click the login button",
            "data": "Username: testuser, Password: secret123",
            "result": "User is logged in and redirected to dashboard"
        }
    """
    action: str = Field(..., description="The action to perform in this step", min_length=1)
    data: str = Field(..., description="The test data or input for this step", min_length=1)
    result: str = Field(..., description="The expected result or outcome", min_length=1)

    @field_validator('action', 'data', 'result')
    @classmethod
    def validate_non_empty_strings(cls, v):
        if not v or not v.strip():
            raise ValueError("Field cannot be empty or whitespace only")
        return v.strip()


class TestCreateParams(BaseModel):
    """Parameters for creating Xray tests."""

    entity: Literal["test"] = Field(..., description="Must be 'test' for test creation")
    action: Literal["create"] = Field(..., description="Must be 'create' for test creation")
    project_key: str = Field(..., description="Jira project key (e.g., 'FTEST')", min_length=1)
    summary: str = Field(..., description="Test case title/summary", min_length=1)
    test_type: Literal["Manual", "Generic", "Cucumber"] = Field(
        default="Manual",
        description="Type of test to create"
    )
    description: Optional[str] = Field(
        default="",
        description="Optional test description"
    )
    steps: Optional[List[StepInput]] = Field(
        default=None,
        description="Test steps for Manual tests. Each step must have action, data, and result fields."
    )
    gherkin: Optional[str] = Field(
        default=None,
        description="Gherkin script for Cucumber tests"
    )

    @field_validator('steps')
    @classmethod
    def validate_steps_for_manual_tests(cls, v, info):
        if hasattr(info, 'data') and info.data:
            test_type = info.data.get('test_type')
            if test_type == 'Manual' and v is not None and len(v) == 0:
                raise ValueError("Manual tests with steps parameter must have at least one step")
        return v

    @field_validator('gherkin')
    @classmethod
    def validate_gherkin_for_cucumber_tests(cls, v, info):
        if hasattr(info, 'data') and info.data:
            test_type = info.data.get('test_type')
            if test_type == 'Cucumber' and not v:
                raise ValueError("Cucumber tests require a gherkin script")
        return v


class TestExecutionParams(BaseModel):
    """Parameters for test execution operations."""

    entity: Literal["test_execution"] = Field(..., description="Must be 'test_execution'")
    action: str = Field(..., description="Action to perform (create, get, update, delete, etc.)")
    project_key: Optional[str] = Field(default=None, description="Jira project key for create operations")
    summary: Optional[str] = Field(default=None, description="Execution summary for create operations")
    issue_id: Optional[str] = Field(default=None, description="Execution issue ID for get/update/delete operations")
    test_issue_ids: Optional[List[str]] = Field(default=None, description="List of test issue IDs to include")
    test_environments: Optional[List[str]] = Field(default=None, description="Test environments")


class TestPlanParams(BaseModel):
    """Parameters for test plan operations."""

    entity: Literal["test_plan"] = Field(..., description="Must be 'test_plan'")
    action: str = Field(..., description="Action to perform (create, get, update, delete, etc.)")
    project_key: Optional[str] = Field(default=None, description="Jira project key for create operations")
    summary: Optional[str] = Field(default=None, description="Plan summary for create operations")
    issue_id: Optional[str] = Field(default=None, description="Plan issue ID for get/update/delete operations")
    test_issue_ids: Optional[List[str]] = Field(default=None, description="List of test issue IDs to include")
    test_exec_issue_ids: Optional[List[str]] = Field(default=None, description="List of execution issue IDs")


class TestRunParams(BaseModel):
    """Parameters for test run operations."""

    entity: Literal["test_run"] = Field(..., description="Must be 'test_run'")
    action: str = Field(..., description="Action to perform (get, update_status, update_comment, etc.)")
    test_execution_id: Optional[str] = Field(default=None, description="Test execution issue ID")
    test_issue_id: Optional[str] = Field(default=None, description="Test issue ID")
    status: Optional[str] = Field(default=None, description="Test run status (PASS, FAIL, etc.)")
    comment: Optional[str] = Field(default=None, description="Test run comment")
    defects: Optional[List[str]] = Field(default=None, description="List of defect issue IDs")