"""TestRunTool for managing Xray test runs via GraphQL API."""

from typing import Dict, Any, Optional, List
from src.graphql_client import XrayGraphQLClient


class TestRunTool:
    """Tool for managing Xray test runs via GraphQL API."""
    
    def __init__(self, client: XrayGraphQLClient):
        """Initialize TestRunTool with GraphQL client.
        
        Args:
            client: Authenticated XrayGraphQLClient instance
        """
        self.client = client
    
    async def execute(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Execute test run operation based on action parameter.
        
        Args:
            params: Dictionary containing action and action-specific parameters
            
        Returns:
            Dictionary containing operation results
            
        Raises:
            ValueError: If action is invalid or required parameters are missing
            Exception: If GraphQL operation fails
        """
        action = params.get('action')
        
        if not action:
            raise ValueError("Missing required parameter: action")
        
        if action == 'get':
            return await self._get_test_run(params)
        elif action == 'get_by_id':
            return await self._get_test_run_by_id(params)
        elif action == 'update_status':
            return await self._update_status(params)
        elif action == 'update_comment':
            return await self._update_comment(params)
        elif action == 'update_step_status':
            return await self._update_step_status(params)
        elif action == 'add_defects':
            return await self._add_defects(params)
        elif action == 'add_evidence':
            return await self._add_evidence(params)
        elif action == 'reset':
            return await self._reset_test_run(params)
        elif action == 'list':
            return await self._list_test_runs(params)
        else:
            raise ValueError(f"Invalid action: {action}")
    
    async def _get_test_run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test run by test ID and execution ID."""
        test_id = params.get('test_id')
        execution_id = params.get('execution_id')
        
        if not test_id:
            raise ValueError("Missing required parameter: test_id")
        if not execution_id:
            raise ValueError("Missing required parameter: execution_id")
        
        query = """
        query GetTestRun($testIssueId: String!, $testExecIssueId: String!) {
            getTestRun(testIssueId: $testIssueId, testExecIssueId: $testExecIssueId) {
                id
                status {
                    name
                    color
                    description
                }
                comment
                startedOn
                finishedOn
                executedById
                assigneeId
                evidence {
                    id
                    filename
                }
                defects
                steps {
                    id
                    action
                    data
                    result
                    status {
                        name
                        color
                    }
                    attachments {
                        id
                        filename
                    }
                }
                examples {
                    id
                    status {
                        name
                        color
                        description
                    }
                }
                test {
                    issueId
                }
                testExecution {
                    issueId
                }
                testType {
                    name
                }
                gherkin
                unstructured
            }
        }
        """
        
        variables = {
            "testIssueId": test_id,
            "testExecIssueId": execution_id
        }
        
        try:
            result = await self.client.execute(query, variables)
            
            if not result.get('getTestRun'):
                raise Exception(f"Test run not found for test ID {test_id} and execution ID {execution_id}")
            
            return result['getTestRun']
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise Exception(f"Test run not found for test ID {test_id} and execution ID {execution_id}")
            raise Exception(f"Failed to get test run: {str(e)}")
    
    async def _get_test_run_by_id(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Get test run by its ID."""
        run_id = params.get('run_id')
        
        if not run_id:
            raise ValueError("Missing required parameter: run_id")
        
        query = """
        query GetTestRunById($id: String!) {
            getTestRunById(id: $id) {
                id
                status {
                    name
                    color
                    description
                }
                comment
                startedOn
                finishedOn
                executedById
                assigneeId
                evidence {
                    id
                    filename
                }
                defects
                steps {
                    id
                    action
                    data
                    result
                    status {
                        name
                        color
                    }
                    attachments {
                        id
                        filename
                    }
                }
                examples {
                    id
                    status {
                        name
                        color
                        description
                    }
                }
                test {
                    issueId
                }
                testExecution {
                    issueId
                }
                testType {
                    name
                }
                gherkin
                unstructured
            }
        }
        """
        
        variables = {"id": run_id}
        
        try:
            result = await self.client.execute(query, variables)
            
            if not result.get('getTestRunById'):
                raise Exception(f"Test run with ID {run_id} not found")
            
            return result['getTestRunById']
            
        except Exception as e:
            if "not found" in str(e).lower():
                raise Exception(f"Test run with ID {run_id} not found")
            raise Exception(f"Failed to get test run by ID: {str(e)}")
    
    async def _update_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update test run status."""
        run_id = params.get('run_id')
        status = params.get('status')
        
        if not run_id:
            raise ValueError("Missing required parameter: run_id")
        if not status:
            raise ValueError("Missing required parameter: status")
        
        mutation = """
        mutation UpdateTestRunStatus($id: String!, $status: String!) {
            updateTestRunStatus(id: $id, status: $status)
        }
        """
        
        variables = {
            "id": run_id,
            "status": status
        }
        
        try:
            await self.client.execute(mutation, variables)
            return {"success": True}
            
        except Exception as e:
            raise Exception(f"Failed to update test run status: {str(e)}")
    
    async def _update_comment(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update test run comment."""
        run_id = params.get('run_id')
        comment = params.get('comment')
        
        if not run_id:
            raise ValueError("Missing required parameter: run_id")
        if not comment:
            raise ValueError("Missing required parameter: comment")
        
        mutation = """
        mutation UpdateTestRunComment($id: String!, $comment: String!) {
            updateTestRunComment(id: $id, comment: $comment)
        }
        """
        
        variables = {
            "id": run_id,
            "comment": comment
        }
        
        try:
            await self.client.execute(mutation, variables)
            return {"success": True}
            
        except Exception as e:
            raise Exception(f"Failed to update test run comment: {str(e)}")
    
    async def _update_step_status(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Update individual step status."""
        run_id = params.get('run_id')
        step_id = params.get('step_id')
        status = params.get('status')
        comment = params.get('comment', '')
        
        if not run_id:
            raise ValueError("Missing required parameter: run_id")
        if not step_id:
            raise ValueError("Missing required parameter: step_id")
        if not status:
            raise ValueError("Missing required parameter: status")
        
        mutation = """
        mutation UpdateTestRunStepStatus($testRunId: String!, $stepId: String!, $status: String!) {
            updateTestRunStepStatus(testRunId: $testRunId, stepId: $stepId, status: $status) {
                warnings
            }
        }
        """
        
        variables = {
            "testRunId": run_id,
            "stepId": step_id,
            "status": status
        }
        
        try:
            result = await self.client.execute(mutation, variables)
            
            # Also update comment if provided
            if comment:
                comment_mutation = """
                mutation UpdateTestRunStepComment($testRunId: String!, $stepId: String!, $comment: String!) {
                    updateTestRunStepComment(testRunId: $testRunId, stepId: $stepId, comment: $comment)
                }
                """
                
                comment_variables = {
                    "testRunId": run_id,
                    "stepId": step_id,
                    "comment": comment
                }
                
                await self.client.execute(comment_mutation, comment_variables)
            
            return {"success": True}
            
        except Exception as e:
            raise Exception(f"Failed to update test run step status: {str(e)}")
    
    async def _add_defects(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add defects to test run."""
        run_id = params.get('run_id')
        defect_ids = params.get('defect_ids', [])
        
        if not run_id:
            raise ValueError("Missing required parameter: run_id")
        if not defect_ids:
            raise ValueError("Missing required parameter: defect_ids")
        
        mutation = """
        mutation AddDefectsToTestRun($id: String!, $issues: [String!]!) {
            addDefectsToTestRun(id: $id, issues: $issues) {
                addedDefects
                warnings
            }
        }
        """
        
        variables = {
            "id": run_id,
            "issues": defect_ids
        }
        
        try:
            result = await self.client.execute(mutation, variables)
            return result['addDefectsToTestRun']
            
        except Exception as e:
            raise Exception(f"Failed to add defects to test run: {str(e)}")
    
    async def _add_evidence(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Add evidence to test run."""
        run_id = params.get('run_id')
        evidence = params.get('evidence', [])
        
        if not run_id:
            raise ValueError("Missing required parameter: run_id")
        if not evidence:
            raise ValueError("Missing required parameter: evidence")
        
        mutation = """
        mutation AddEvidenceToTestRun($id: String!, $evidence: [AttachmentDataInput!]!) {
            addEvidenceToTestRun(id: $id, evidence: $evidence) {
                addedEvidence
                warnings
            }
        }
        """
        
        variables = {
            "id": run_id,
            "evidence": evidence
        }
        
        try:
            result = await self.client.execute(mutation, variables)
            return result['addEvidenceToTestRun']
            
        except Exception as e:
            raise Exception(f"Failed to add evidence to test run: {str(e)}")
    
    async def _reset_test_run(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Reset test run to initial state."""
        run_id = params.get('run_id')
        
        if not run_id:
            raise ValueError("Missing required parameter: run_id")
        
        mutation = """
        mutation ResetTestRun($id: String!) {
            resetTestRun(id: $id)
        }
        """
        
        variables = {"id": run_id}
        
        try:
            await self.client.execute(mutation, variables)
            return {"success": True}
            
        except Exception as e:
            raise Exception(f"Failed to reset test run: {str(e)}")
    
    async def _list_test_runs(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """List test runs by criteria."""
        test_ids = params.get('test_ids', [])
        execution_ids = params.get('execution_ids', [])
        limit = params.get('limit', 50)
        start = params.get('start', 0)
        
        # Ensure limit doesn't exceed 100 (Xray constraint)
        if limit > 100:
            limit = 100
        
        query = """
        query GetTestRuns($testIssueIds: [String!], $testExecIssueIds: [String!], $limit: Int!, $start: Int!) {
            getTestRuns(testIssueIds: $testIssueIds, testExecIssueIds: $testExecIssueIds, limit: $limit, start: $start) {
                total
                limit
                start
                results {
                    id
                    status {
                        name
                        color
                        description
                    }
                    comment
                    startedOn
                    finishedOn
                    evidence {
                        id
                        filename
                    }
                    defects
                    steps {
                        id
                        action
                        data
                        result
                        status {
                            name
                            color
                        }
                        attachments {
                            id
                            filename
                        }
                    }
                    examples {
                        id
                        status {
                            name
                            color
                            description
                        }
                    }
                    test {
                        issueId
                    }
                    testExecution {
                        issueId
                    }
                    testType {
                        name
                    }
                    gherkin
                    unstructured
                }
            }
        }
        """
        
        variables = {
            "testIssueIds": test_ids if test_ids else None,
            "testExecIssueIds": execution_ids if execution_ids else None,
            "limit": limit,
            "start": start
        }
        
        try:
            result = await self.client.execute(query, variables)
            
            test_runs_data = result['getTestRuns']
            
            return {
                'testRuns': test_runs_data['results'],
                'total': test_runs_data['total'],
                'start': test_runs_data['start'],
                'limit': test_runs_data['limit']
            }
            
        except Exception as e:
            raise Exception(f"Failed to list test runs: {str(e)}")