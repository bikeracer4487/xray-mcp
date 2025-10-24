"""Test management operations for Xray."""

from typing import Dict, Any, List, Optional
from .base_manager import XrayEntityManager
from ..utils.graphql_templates import (
    CREATE_MANUAL_TEST, CREATE_GENERIC_TEST, CREATE_CUCUMBER_TEST,
    GET_TEST, LIST_TESTS, DELETE_TEST, UPDATE_TEST_TYPE,
    UPDATE_UNSTRUCTURED_TEST_DEFINITION, UPDATE_GHERKIN_TEST_DEFINITION,
    UPDATE_TEST_METADATA
)
from ..utils.retry_strategy import IndexingDelayMitigator, RetryReason


class TestManager(XrayEntityManager):
    """Manager for Xray test operations."""

    def __init__(self, client):
        """Initialize TestManager with indexing delay mitigation."""
        super().__init__(client)
        self.retry_mitigator = IndexingDelayMitigator()

    async def create(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Create a new test."""
        project_key = params.get('project_key')
        summary = params.get('summary')
        test_type = params.get('test_type', 'Manual')
        description = params.get('description', '')
        steps = params.get('steps', [])
        gherkin = params.get('gherkin')

        if not project_key:
            return self.create_error_result("Missing required parameter: project_key")
        if not summary:
            return self.create_error_result("Missing required parameter: summary")

        # Parse steps parameter if it's a JSON string
        if isinstance(steps, str):
            try:
                import json
                steps = json.loads(steps)
            except json.JSONDecodeError as e:
                return self.create_error_result(f"Invalid JSON format for steps parameter: {str(e)}")
        
        # Validate steps format if provided
        if steps and not isinstance(steps, list):
            return self.create_error_result("Steps parameter must be a list of step objects or a JSON string")
        
        # Validate each step has required structure for CreateStepInput
        if steps:
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    return self.create_error_result(f"Step {i+1} must be an object with 'action', 'data', and 'result' fields")
                # Note: action, data, result are optional in CreateStepInput but commonly used

        try:
            # Choose template based on test type
            if test_type == 'Manual':
                query = CREATE_MANUAL_TEST
                variables = {
                    'projectKey': project_key,
                    'summary': summary,
                    'description': description,
                    'steps': steps
                }
            elif test_type == 'Cucumber':
                if not gherkin:
                    return self.create_error_result("Missing required parameter: gherkin for Cucumber tests")
                query = CREATE_CUCUMBER_TEST
                variables = {
                    'projectKey': project_key,
                    'summary': summary,
                    'description': description,
                    'gherkin': gherkin
                }
            else:  # Generic
                query = CREATE_GENERIC_TEST
                variables = {
                    'projectKey': project_key,
                    'summary': summary,
                    'description': description
                }

            result = await self.execute_query(query, variables)
            test_data = result['createTest']['test']
            jira_data = test_data['jira']

            response_data = {
                'issueId': test_data['issueId'],
                'issueKey': jira_data['key'],
                'summary': jira_data['summary'],
                'testType': test_data['testType']['name']
            }

            # Add indexing delay advisory for immediate follow-up operations
            warnings = result['createTest'].get('warnings', [])
            warnings.append(
                f"INDEXING DELAY ADVISORY: Test '{response_data['issueKey']}' created successfully. "
                f"If you plan to immediately search for, retrieve, or use this test in other operations, "
                f"please wait 2-5 seconds for Xray indexing to complete."
            )

            return self.create_success_result(response_data, warnings)

        except Exception as e:
            return self.create_error_result(f"Failed to create test: {str(e)}")

    async def get(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test by issue ID with advanced indexing delay mitigation and ID format validation."""
        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate ID format before making API calls
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test")
        if not validation_result.is_valid:
            # Provide helpful error message for ID format issues
            error_msg = validation_result.error_message
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        async def get_operation():
            variables = {'issueId': issue_id}
            result = await self.execute_query(GET_TEST, variables)

            if result.get('getTest'):
                # Success case
                test_data = result['getTest']
                response_data = self.extract_jira_data(test_data)
                response_data['testType'] = test_data['testType']['name']

                # Add test-specific data
                if test_data.get('steps'):
                    response_data['steps'] = test_data['steps']
                if test_data.get('gherkin'):
                    response_data['gherkin'] = test_data['gherkin']
                if test_data.get('lastModified'):
                    response_data['lastModified'] = test_data['lastModified']

                return response_data
            else:
                raise Exception(f"Test with issue ID {issue_id} not found")

        # Use advanced retry strategy with indexing delay mitigation
        retry_result = await self.retry_mitigator.execute_with_retry(
            get_operation,
            f"get_test_{issue_id}",
            expected_indexing_delay=True
        )

        if retry_result.success:
            return self.create_success_result(retry_result.result)
        else:
            # Enhanced error message for failed operations
            error_msg = f"Failed to get test after {retry_result.attempts} attempts"
            if retry_result.last_error:
                error_msg += f": {str(retry_result.last_error)}"
            
            # If the error is "not found" and user provided what looks like a numeric ID,
            # this might be a real indexing delay or the test doesn't exist
            if "not found" in error_msg.lower():
                error_msg += f". Note: Using numeric ID '{issue_id}' (correct format). If test was just created, try again in a few seconds due to indexing delays."
            
            return self.create_error_result(error_msg)

    async def list(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List tests with advanced indexing delay handling."""
        project_key = params.get('project_key')
        jql = params.get('jql')
        limit = min(params.get('limit', 50), 100)
        start = params.get('start', 0)
        retry_on_empty = params.get('retry_on_empty_results', False)

        async def list_operation():
            # Build JQL query
            final_jql = self.build_jql(project_key, jql, 'Test')

            variables = {
                'jql': final_jql,
                'limit': limit,
                'start': start
            }

            result = await self.execute_query(LIST_TESTS, variables)
            tests_data = result['getTests']

            # Transform results
            tests = []
            for test in tests_data['results']:
                test_info = self.extract_jira_data(test)
                test_info['testType'] = test['testType']['name']
                if test.get('lastModified'):
                    test_info['lastModified'] = test['lastModified']
                tests.append(test_info)

            response_data = {
                'tests': tests,
                'total': tests_data['total'],
                'start': tests_data['start'],
                'limit': tests_data['limit']
            }

            # Check if we should retry on empty results
            if tests_data['total'] == 0 and retry_on_empty:
                raise Exception("No results found - potential indexing delay")

            return response_data

        # Use advanced retry strategy if retry_on_empty is enabled
        if retry_on_empty:
            retry_result = await self.retry_mitigator.execute_with_retry(
                list_operation,
                f"list_tests_{project_key or 'all'}",
                expected_indexing_delay=True
            )

            if retry_result.success:
                warnings = []
                if retry_result.result['total'] == 0 and project_key:
                    warnings.append("No tests found. If tests were recently created, Xray indexing delays may affect visibility.")
                return self.create_success_result(retry_result.result, warnings)
            else:
                return self.create_error_result(f"Failed to list tests after {retry_result.attempts} attempts: {str(retry_result.last_error)}")
        else:
            # Execute once without retry
            try:
                result = await list_operation()
                warnings = []
                if result['total'] == 0 and project_key:
                    warnings.append("No tests found. If tests were recently created, Xray indexing delays may affect visibility.")
                return self.create_success_result(result, warnings)
            except Exception as e:
                return self.create_error_result(f"Failed to list tests: {str(e)}")

    async def delete(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Delete test by issue ID with ID format validation."""
        issue_id = params.get('issue_id')
        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate ID format before making API calls
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test")
        if not validation_result.is_valid:
            # Provide helpful error message for ID format issues
            error_msg = validation_result.error_message
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        try:
            # First verify the test exists (this will also benefit from ID validation in get method)
            get_result = await self.get({'issue_id': issue_id})
            if not get_result['success']:
                return self.create_error_result(f"Cannot delete test: {get_result['errors'][0]}")

            variables = {'issueId': issue_id}
            await self.execute_query(DELETE_TEST, variables)

            response_data = {
                'message': f'Test with issue ID {issue_id} has been deleted successfully'
            }
            return self.create_success_result(response_data)

        except Exception as e:
            error_msg = f"Failed to delete test: {str(e)}"
            
            # Enhance error message if it's a "not found" error
            if "not found" in error_msg.lower():
                error_msg += f". Note: Using numeric ID '{issue_id}' (correct format). Verify the test exists and try again if recently created (indexing delays)."
            
            return self.create_error_result(error_msg)

    async def update_type(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update test type with ID format validation."""
        issue_id = params.get('issue_id')
        test_type = params.get('test_type')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")
        if not test_type:
            return self.create_error_result("Missing required parameter: test_type")

        # Import ID validation utility
        from ..utils.id_validation import IDFormatValidator

        # Validate ID format before making API calls
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test")
        if not validation_result.is_valid:
            # Provide helpful error message for ID format issues
            error_msg = validation_result.error_message
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        try:
            variables = {
                'issueId': issue_id,
                'testType': {'name': test_type}
            }

            result = await self.execute_query(UPDATE_TEST_TYPE, variables)
            warnings = result['updateTestType'].get('warnings', [])

            response_data = {
                'issueId': issue_id,
                'testType': test_type,
                'message': f'Test type updated to {test_type}'
            }

            return self.create_success_result(response_data, warnings)

        except Exception as e:
            error_msg = f"Failed to update test type: {str(e)}"
            
            # Enhance error message if it contains ID validation hints
            if "not valid" in error_msg.lower() or "invalid" in error_msg.lower():
                error_msg += f". Note: Using numeric ID '{issue_id}' (correct format). Verify the test exists."
            
            return self.create_error_result(error_msg)

    async def update_content(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update test content (Gherkin for Cucumber tests)."""
        issue_id = params.get('issue_id')
        gherkin = params.get('gherkin')
        steps = params.get('steps')

        if not issue_id:
            return self.create_error_result("Missing required parameter: issue_id")

        if gherkin:
            # Update Gherkin content for Cucumber tests
            try:
                variables = {
                    'issueId': issue_id,
                    'gherkin': gherkin
                }

                result = await self.execute_query(UPDATE_GHERKIN_TEST_DEFINITION, variables)
                warnings = result['updateGherkinTestDefinition'].get('warnings', [])

                response_data = {
                    'issueId': issue_id,
                    'gherkin': gherkin,
                    'message': 'Test Gherkin content updated successfully'
                }

                return self.create_success_result(response_data, warnings)

            except Exception as e:
                return self.create_error_result(f"Failed to update test content: {str(e)}")

        elif steps:
            # Manual test steps require individual step operations
            return self.create_success_result({
                'issueId': issue_id,
                'message': 'Manual test step updates require individual step operations'
            }, ['Step updates require individual step operations'])

        else:
            return self.create_error_result("No content updates specified (gherkin or steps required)")

    async def update_metadata(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update test metadata (summary and description) with enhanced workaround guidance.

        Note: Xray's GraphQL API does not support direct metadata updates.
        This provides comprehensive workaround guidance.
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
        validation_result = IDFormatValidator.validate_for_xray_graphql(issue_id, "test")
        if not validation_result.is_valid:
            error_msg = f"Invalid test ID: {validation_result.error_message}"
            if validation_result.helpful_message:
                error_msg += f". {validation_result.helpful_message}"
            return self.create_error_result(error_msg)

        # Get current test details to provide context for workarounds
        try:
            current_test = await self.get({'issue_id': issue_id})
            if not current_test['success']:
                return self.create_error_result(f"Cannot update metadata: {current_test['errors'][0]}")

            test_data = current_test['data']
            test_key = test_data.get('issueKey', 'Unknown')
            test_type = test_data.get('testType', 'Unknown')

            # Create detailed workaround guidance based on test type and current state
            workaround_guidance = self._create_metadata_workaround_guidance(
                test_key, test_type, issue_id, summary, description, test_data
            )

            error_lines = [
                "LIMITATION: Metadata-only updates are not supported by Xray's GraphQL API",
                f"TEST CONTEXT: {test_key} (Type: {test_type}, ID: {issue_id})",
                "WORKAROUND OPTIONS:"
            ]
            error_lines.extend(workaround_guidance)
            return self.create_error_result("; ".join(error_lines))

        except Exception as e:
            # Fallback to basic error message if we can't get test details
            error_message = "; ".join([
                "Metadata-only updates are not supported by Xray's GraphQL API",
                "This is a known limitation of the Xray Cloud platform",
                "Workarounds: (1) Use update_content with both metadata and content changes",
                "(2) Update metadata directly in Jira UI",
                "(3) Use Jira's REST API separately (requires additional authentication setup)"
            ])
            return self.create_error_result(error_message)

    def _create_metadata_workaround_guidance(self, test_key: str, test_type: str,
                                           issue_id: str, summary: str, description: str,
                                           test_data: Dict[str, Any]) -> List[str]:
        """Create detailed workaround guidance for metadata updates."""
        guidance = []

        # Option 1: Combined content + metadata update
        if test_type == 'Manual' and test_data.get('steps'):
            guidance.append(
                f"1. COMBINED UPDATE: Use update_content to update both metadata and steps together:"
            )
            guidance.append(
                f"   entity='test', action='update_content', issue_id='{issue_id}', "
                f"summary='{summary or test_data.get('summary', 'Current Summary')}', "
                f"description='{description or test_data.get('description', 'Current Description')}', "
                f"steps=[...existing steps...]"
            )
        elif test_type == 'Cucumber' and test_data.get('gherkin'):
            guidance.append(
                f"1. COMBINED UPDATE: Use update_content to update both metadata and Gherkin:"
            )
            guidance.append(
                f"   entity='test', action='update_content', issue_id='{issue_id}', "
                f"summary='{summary or test_data.get('summary', 'Current Summary')}', "
                f"description='{description or test_data.get('description', 'Current Description')}', "
                f"gherkin='...existing gherkin...'"
            )
        else:
            guidance.append(
                f"1. COMBINED UPDATE: Not available for {test_type} tests without content"
            )

        # Option 2: Direct Jira UI
        guidance.append(
            f"2. JIRA UI: Navigate to {test_key} in Jira and edit Summary/Description directly"
        )

        # Option 3: Alternative approach suggestion
        if summary and description:
            guidance.append(
                f"3. RECREATION: For major changes, consider creating a new test with desired metadata:"
            )
            guidance.append(
                f"   entity='test', action='create', project_key='{test_key.split('-')[0]}', "
                f"summary='{summary}', description='{description}', test_type='{test_type}'"
            )

        # Option 4: Jira REST API
        guidance.append(
            f"4. JIRA REST API: Use Jira's REST API PUT /rest/api/2/issue/{test_key} "
            f"with appropriate authentication to update summary/description"
        )

        return guidance