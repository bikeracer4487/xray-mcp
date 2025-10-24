"""Test plan management operations for Xray."""

from typing import Dict, Any, List
from .base_manager import XrayEntityManager
from ..utils.graphql_templates import (
    CREATE_TEST_PLAN, GET_TEST_PLAN, LIST_TEST_PLANS,
    DELETE_TEST_PLAN, ADD_TESTS_TO_PLAN, REMOVE_TESTS_FROM_PLAN,
    ADD_EXECUTIONS_TO_PLAN, REMOVE_EXECUTIONS_FROM_PLAN
)


class PlanManager(XrayEntityManager):
    """Manager for Xray test plan operations."""

    def __init__(self, client):
        """Initialize PlanManager with indexing delay mitigation."""
        super().__init__(client)
        from ..utils.retry_strategy import IndexingDelayMitigator
        self.retry_mitigator = IndexingDelayMitigator()

    async def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test plan with array validation for test IDs."""
        project_key = params.get('project_key')
        summary = params.get('summary')
        test_issue_ids = params.get('test_issue_ids', [])

        if not project_key:
            return self.create_error_result("Missing required parameter: project_key")
        if not summary:
            return self.create_error_result("Missing required parameter: summary")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate test_issue_ids array if provided (allow empty arrays for creation)
        if test_issue_ids:
            validation_result = IDFormatValidator.validate_id_array_for_xray_graphql_allow_empty(test_issue_ids, "test")
            if not validation_result.is_valid:
                # Provide helpful error message for array validation issues
                error_msg = f"Invalid test_issue_ids: {validation_result.error_message}"
                if validation_result.helpful_message:
                    error_msg += f". {validation_result.helpful_message}"
                return self.create_error_result(error_msg)

        try:
            variables = {
                'projectKey': project_key,
                'summary': summary,
                'testIssueIds': test_issue_ids
            }

            result = await self.execute_query(CREATE_TEST_PLAN, variables)
            plan_data = result['createTestPlan']['testPlan']
            jira_data = plan_data['jira']

            response_data = {
                'issueId': plan_data['issueId'],
                'issueKey': jira_data['key'],
                'summary': jira_data['summary']
            }

            warnings = result['createTestPlan'].get('warnings', [])

            # Add indexing delay advisory for immediate follow-up operations
            warnings.append(
                f"INDEXING DELAY ADVISORY: Test plan '{response_data['issueKey']}' created successfully. "
                f"If you plan to immediately search for, retrieve, or add tests/executions to this plan, "
                f"please wait 2-5 seconds for Xray indexing to complete."
            )

            return self.create_success_result(response_data, warnings)

        except Exception as e:
            return self.create_error_result(f"Failed to create test plan: {str(e)}")

    async def get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test plan by issue ID with advanced indexing delay mitigation and ID format validation."""
        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate ID format before making API calls
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_plan")
        if not validation_result.is_valid:
            # Provide helpful error message for ID format issues
            error_msg = validation_result.error_message
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        async def get_operation():
            variables = {'issueId': issue_id}
            result = await self.execute_query(GET_TEST_PLAN, variables)

            if result.get('getTestPlan'):
                # Success case
                plan_data = result['getTestPlan']
                response_data = self.extract_jira_data(plan_data)

                # Add plan-specific data
                if plan_data.get('tests'):
                    response_data['tests'] = plan_data['tests']

                return response_data
            else:
                raise Exception(f"Test plan with issue ID {issue_id} not found")

        # Use advanced retry strategy with indexing delay mitigation
        retry_result = await self.retry_mitigator.execute_with_retry(
            get_operation,
            f"get_plan_{issue_id}",
            expected_indexing_delay=True
        )

        if retry_result.success:
            return self.create_success_result(retry_result.result)
        else:
            # Enhanced error message for failed operations
            error_msg = f"Failed to get test plan after {retry_result.attempts} attempts"
            if retry_result.last_error:
                error_msg += f": {str(retry_result.last_error)}"
            
            # If the error is "not found" and user provided what looks like a numeric ID,
            # this might be a real indexing delay or the plan doesn't exist
            if "not found" in error_msg.lower():
                error_msg += f". Note: Using numeric ID '{issue_id}' (correct format). If plan was just created, try again in a few seconds due to indexing delays."
            
            return self.create_error_result(error_msg)

    async def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List test plans with optional filtering and indexing delay handling."""
        import asyncio

        project_key = params.get('project_key')
        jql = params.get('jql')
        limit = min(params.get('limit', 50), 100)
        start = params.get('start', 0)
        retry_on_empty = params.get('retry_on_empty_results', False)

        # Retry logic for potential indexing delays
        max_retries = 2 if retry_on_empty else 0
        base_delay = 1  # seconds (shorter for list operations)

        for attempt in range(max_retries + 1):
            try:
                # Build JQL query
                final_jql = self.build_jql(project_key, jql, 'Test Plan')

                variables = {
                    'jql': final_jql,
                    'limit': limit,
                    'start': start
                }

                result = await self.execute_query(LIST_TEST_PLANS, variables)
                plans_data = result['getTestPlans']

                # Transform results
                plans = []
                for plan in plans_data['results']:
                    plan_info = self.extract_jira_data(plan)
                    plans.append(plan_info)

                response_data = {
                    'plans': plans,
                    'total': plans_data['total'],
                    'start': plans_data['start'],
                    'limit': plans_data['limit']
                }

                # If we got results or this isn't a retry scenario, return
                if plans_data['total'] > 0 or not retry_on_empty or attempt == max_retries:
                    warnings = []
                    if plans_data['total'] == 0 and project_key:
                        warnings.append("No test plans found. If plans were recently created, Xray indexing delays may affect visibility.")
                    return self.create_success_result(response_data, warnings)

                # If empty results and retry enabled, wait and try again
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff: 1, 2 seconds
                    await asyncio.sleep(delay)

            except Exception as e:
                # Check if it's an indexing-related error
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['index', 're-index']) and attempt < max_retries:
                    delay = base_delay * (2 ** attempt)
                    await asyncio.sleep(delay)
                    continue

                return self.create_error_result(f"Failed to list test plans: {str(e)}")

        # Should not reach here, but fallback
        return self.create_error_result("Failed to list test plans after retries")

    async def delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete test plan by issue ID with ID format validation."""
        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate ID format before making API calls
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_plan")
        if not validation_result.is_valid:
            # Provide helpful error message for ID format issues
            error_msg = validation_result.error_message
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        try:
            # First verify the test plan exists (this will also benefit from ID validation in get method)
            get_result = await self.get({'issue_id': issue_id})
            if not get_result['success']:
                return self.create_error_result(f"Cannot delete test plan: {get_result['errors'][0]}")

            variables = {'issueId': issue_id}
            await self.execute_query(DELETE_TEST_PLAN, variables)

            response_data = {
                'message': f'Test plan with issue ID {issue_id} has been deleted successfully'
            }
            return self.create_success_result(response_data)

        except Exception as e:
            error_msg = f"Failed to delete test plan: {str(e)}"
            
            # Enhance error message if it's a "not found" error
            if "not found" in error_msg.lower():
                error_msg += f". Note: Using numeric ID '{issue_id}' (correct format). Verify the test plan exists and try again if recently created (indexing delays)."
            
            return self.create_error_result(error_msg)

    async def add_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add tests to test plan with array validation."""
        issue_id = params.get('issue_id')
        test_issue_ids = params.get('test_issue_ids')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        
        # Check if test_issue_ids parameter was provided
        if test_issue_ids is None:
            return self.create_error_result("Missing required parameter: test_issue_ids")
        
        # Check if array is empty
        if len(test_issue_ids) == 0:
            return self.create_error_result("At least one test ID must be provided in test_issue_ids array")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate plan ID format
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_plan")
        if not validation_result.is_valid:
            error_msg = f"Invalid plan issue_id: {validation_result.error_message}"
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        # Validate test_issue_ids array
        array_validation_result = IDFormatValidator.validate_id_array_for_xray_graphql(test_issue_ids, "test")
        if not array_validation_result.is_valid:
            error_msg = f"Invalid test_issue_ids: {array_validation_result.error_message}"
            if array_validation_result.helpful_message:
                error_msg += f". {array_validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        try:
            variables = {
                'issueId': issue_id,
                'testIssueIds': test_issue_ids
            }

            result = await self.execute_query(ADD_TESTS_TO_PLAN, variables)
            response = result['addTestsToTestPlan']

            return self.create_success_result(response)

        except Exception as e:
            return self.create_error_result(f"Failed to add tests to test plan: {str(e)}")

    async def remove_tests(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove tests from test plan with array validation."""
        issue_id = params.get('issue_id')
        test_issue_ids = params.get('test_issue_ids')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        
        # Check if test_issue_ids parameter was provided
        if test_issue_ids is None:
            return self.create_error_result("Missing required parameter: test_issue_ids")
        
        # Check if array is empty
        if len(test_issue_ids) == 0:
            return self.create_error_result("At least one test ID must be provided in test_issue_ids array")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate plan ID format
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_plan")
        if not validation_result.is_valid:
            error_msg = f"Invalid plan issue_id: {validation_result.error_message}"
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        # Validate test_issue_ids array
        array_validation_result = IDFormatValidator.validate_id_array_for_xray_graphql(test_issue_ids, "test")
        if not array_validation_result.is_valid:
            error_msg = f"Invalid test_issue_ids: {array_validation_result.error_message}"
            if array_validation_result.helpful_message:
                error_msg += f". {array_validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        try:
            variables = {
                'issueId': issue_id,
                'testIssueIds': test_issue_ids
            }

            await self.execute_query(REMOVE_TESTS_FROM_PLAN, variables)

            response_data = {
                'message': f'Tests {test_issue_ids} removed from test plan {issue_id}'
            }
            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to remove tests from test plan: {str(e)}")

    async def add_executions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add test executions to test plan with array validation and retry logic for indexing delays."""
        import asyncio
        
        issue_id = params.get('issue_id')
        exec_issue_ids = params.get('test_exec_issue_ids')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        
        # Check if test_exec_issue_ids parameter was provided
        if exec_issue_ids is None:
            return self.create_error_result("Missing required parameter: test_exec_issue_ids")
        
        # Check if array is empty
        if len(exec_issue_ids) == 0:
            return self.create_error_result("At least one execution ID must be provided in test_exec_issue_ids array")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate plan ID format
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_plan")
        if not validation_result.is_valid:
            error_msg = f"Invalid plan issue_id: {validation_result.error_message}"
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        # Validate test_exec_issue_ids array
        array_validation_result = IDFormatValidator.validate_id_array_for_xray_graphql(exec_issue_ids, "test_execution")
        if not array_validation_result.is_valid:
            error_msg = f"Invalid test_exec_issue_ids: {array_validation_result.error_message}"
            if array_validation_result.helpful_message:
                error_msg += f". {array_validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        # Retry logic for potential indexing delays when adding executions
        max_attempts = 3  # More attempts for association operations
        base_delay = 2    # Start with 2 seconds

        for attempt in range(max_attempts):
            try:
                variables = {
                    'issueId': issue_id,
                    'testExecIssueIds': exec_issue_ids
                }

                result = await self.execute_query(ADD_EXECUTIONS_TO_PLAN, variables)
                response = result['addTestExecutionsToTestPlan']

                # Check if all executions were successfully added
                added_executions = response.get('addedTestExecutions', [])
                if len(added_executions) < len(exec_issue_ids) and attempt < max_attempts - 1:
                    # Not all executions were added, likely indexing delay
                    retry_delay = base_delay * (2 ** attempt)  # Exponential backoff: 2, 4 seconds
                    await asyncio.sleep(retry_delay)
                    continue

                return self.create_success_result(response)

            except Exception as e:
                error_str = str(e).lower()
                # Check if it's likely an indexing-related error
                if any(keyword in error_str for keyword in ['not found', 'invalid', 'index', 'exist']) and attempt < max_attempts - 1:
                    retry_delay = base_delay * (2 ** attempt)  # Exponential backoff: 2, 4 seconds
                    await asyncio.sleep(retry_delay)
                    continue
                else:
                    return self.create_error_result(f"Failed to add executions to test plan: {str(e)}")

        # Fallback (should not reach here)
        return self.create_error_result("Failed to add executions to test plan after retry")

    async def remove_executions(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Remove test executions from test plan with array validation."""
        issue_id = params.get('issue_id')
        exec_issue_ids = params.get('test_exec_issue_ids')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        
        # Check if test_exec_issue_ids parameter was provided
        if exec_issue_ids is None:
            return self.create_error_result("Missing required parameter: test_exec_issue_ids")
        
        # Check if array is empty
        if len(exec_issue_ids) == 0:
            return self.create_error_result("At least one execution ID must be provided in test_exec_issue_ids array")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate plan ID format
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_plan")
        if not validation_result.is_valid:
            error_msg = f"Invalid plan issue_id: {validation_result.error_message}"
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        # Validate test_exec_issue_ids array
        array_validation_result = IDFormatValidator.validate_id_array_for_xray_graphql(exec_issue_ids, "test_execution")
        if not array_validation_result.is_valid:
            error_msg = f"Invalid test_exec_issue_ids: {array_validation_result.error_message}"
            if array_validation_result.helpful_message:
                error_msg += f". {array_validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        try:
            variables = {
                'issueId': issue_id,
                'testExecIssueIds': exec_issue_ids
            }

            await self.execute_query(REMOVE_EXECUTIONS_FROM_PLAN, variables)

            response_data = {
                'message': f'Test executions {exec_issue_ids} removed from test plan {issue_id}'
            }
            return self.create_success_result(response_data)

        except Exception as e:
            return self.create_error_result(f"Failed to remove executions from test plan: {str(e)}")

    async def update_metadata(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update test plan metadata (summary and description) with enhanced workaround guidance.

        Note: Xray's GraphQL API does not support direct metadata updates for test plans.
        This provides comprehensive workaround guidance specific to test plans.
        """
        issue_id = params.get('issue_id')
        summary = params.get('summary')
        description = params.get('description')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        if not summary and not description:
            return self.create_error_result("At least one of summary or description must be provided")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate ID format to provide helpful guidance
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test_plan")
        if not validation_result.is_valid:
            error_msg = f"Invalid plan ID: {validation_result.error_message}"
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        # Get current plan details to provide context for workarounds
        try:
            current_plan = await self.get({'issue_id': issue_id})
            if not current_plan['success']:
                return self.create_error_result(f"Cannot update metadata: {current_plan['errors'][0]}")

            plan_data = current_plan['data']
            plan_key = plan_data.get('issueKey', 'Unknown')
            project_key = plan_key.split('-')[0] if '-' in plan_key else 'PROJECT'
            tests_count = len(plan_data.get('tests', []))

            # Create detailed workaround guidance for test plan metadata
            workaround_guidance = [
                f"1. JIRA UI: Navigate to {plan_key} in Jira and edit Summary/Description directly",
                f"2. RECREATION: Create a new test plan with desired metadata:",
                f"   entity='test_plan', action='create', project_key='{project_key}', summary='{summary or plan_data.get('summary', 'New Summary')}', description='{description or plan_data.get('description', 'New Description')}'",
                f"3. JIRA REST API: Use Jira's REST API PUT /rest/api/2/issue/{plan_key} with appropriate authentication",
                f"4. BULK OPERATIONS: If updating multiple plans, use Jira's bulk edit feature"
            ]

            if tests_count > 0:
                workaround_guidance.append(
                    f"5. NOTE: This plan contains {tests_count} test(s). If recreating, remember to add tests back using add_tests action."
                )

            error_lines = [
                "LIMITATION: Metadata-only updates are not supported by Xray's GraphQL API",
                f"PLAN CONTEXT: {plan_key} (ID: {issue_id}, Tests: {tests_count})",
                "WORKAROUND OPTIONS:"
            ]
            error_lines.extend(workaround_guidance)
            return self.create_error_result("; ".join(error_lines))

        except Exception as e:
            # Fallback to basic error message if we can't get plan details
            error_message = "; ".join([
                "Metadata-only updates are not supported by Xray's GraphQL API for test plans",
                "This is a known limitation of the Xray Cloud platform",
                "Workarounds: (1) Update metadata directly in Jira UI",
                "(2) Use Jira's REST API separately (requires additional authentication setup)",
                "(3) Create a new plan with desired metadata"
            ])
            return self.create_error_result(error_message)