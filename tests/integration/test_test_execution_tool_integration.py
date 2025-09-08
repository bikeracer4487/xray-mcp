import pytest
import os
import uuid
from dotenv import load_dotenv
from src.auth import XrayAuth
from src.graphql_client import XrayGraphQLClient
from src.tools.test_execution_tool import TestExecutionTool
from src.tools.test_tool import TestTool

load_dotenv()

class TestTestExecutionToolIntegration:
    """Integration tests for Test Execution tool against live API."""
    
    @pytest.fixture
    async def tool(self):
        """Create Test Execution tool with authenticated client."""
        auth = XrayAuth(
            client_id=os.getenv('XRAY_CLIENT_ID'),
            client_secret=os.getenv('XRAY_CLIENT_SECRET')
        )
        await auth.authenticate()
        client = XrayGraphQLClient(auth)
        return TestExecutionTool(client)
    
    @pytest.fixture
    async def test_tool(self):
        """Create Test tool for creating test issues."""
        auth = XrayAuth(
            client_id=os.getenv('XRAY_CLIENT_ID'),
            client_secret=os.getenv('XRAY_CLIENT_SECRET')
        )
        await auth.authenticate()
        client = XrayGraphQLClient(auth)
        return TestTool(client)
    
    @pytest.fixture
    async def test_issues(self, test_tool):
        """Create test issues to use in executions."""
        tests = []
        for i in range(3):
            result = await test_tool.execute({
                'action': 'create',
                'test_type': 'Manual',
                'project_key': 'FTEST',
                'summary': f"Test for execution {uuid.uuid4().hex[:8]}",
                'description': 'Test for test execution',
                'steps': [
                    {'action': f'Step {i+1}', 'result': 'Expected result'}
                ]
            })
            tests.append(result['issueId'])
        return tests
    
    @pytest.mark.asyncio
    async def test_create_test_execution(self, tool, test_issues):
        """Test creating a test execution with tests."""
        summary = f"Test Execution {uuid.uuid4().hex[:8]}"
        result = await tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': summary,
            'description': 'Integration test execution',
            'test_ids': test_issues[:2],  # Add 2 of the 3 tests
            'test_environments': ['DEV', 'QA']
        })
        
        assert 'issueId' in result
        assert 'issueKey' in result
        assert result['issueKey'].startswith('FTEST-')
        assert result['summary'] == summary
        assert 'testEnvironments' in result
        assert 'DEV' in result['testEnvironments']
        assert 'QA' in result['testEnvironments']
        
        # Store for cleanup
        pytest.execution_id = result['issueId']
    
    @pytest.mark.asyncio
    async def test_get_test_execution(self, tool, test_issues):
        """Test fetching a test execution."""
        # Create an execution
        create_result = await tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': f"Execution to fetch {uuid.uuid4().hex[:8]}",
            'test_ids': [test_issues[0]]
        })
        
        # Fetch it
        get_result = await tool.execute({
            'action': 'get',
            'issue_id': create_result['issueId']
        })
        
        assert get_result['issueId'] == create_result['issueId']
        assert get_result['summary'] == create_result['summary']
        assert 'tests' in get_result
        
        # Store for cleanup
        pytest.execution_id = create_result['issueId']
    
    @pytest.mark.asyncio
    async def test_add_tests_to_execution(self, tool, test_issues):
        """Test adding tests to existing execution."""
        # Create execution with one test
        create_result = await tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': f"Execution for adding {uuid.uuid4().hex[:8]}",
            'test_ids': [test_issues[0]]
        })
        
        # Add more tests
        add_result = await tool.execute({
            'action': 'add_tests',
            'issue_id': create_result['issueId'],
            'test_ids': test_issues[1:3]
        })
        
        assert add_result['success'] is True
        assert 'addedTests' in add_result
        
        # Store for cleanup
        pytest.execution_id = create_result['issueId']
    
    @pytest.mark.asyncio
    async def test_remove_tests_from_execution(self, tool, test_issues):
        """Test removing tests from execution."""
        # Create execution with all tests
        create_result = await tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': f"Execution for removal {uuid.uuid4().hex[:8]}",
            'test_ids': test_issues
        })
        
        # Remove a test
        remove_result = await tool.execute({
            'action': 'remove_tests',
            'issue_id': create_result['issueId'],
            'test_ids': [test_issues[0]]
        })
        
        assert remove_result['success'] is True
        
        # Store for cleanup
        pytest.execution_id = create_result['issueId']
    
    @pytest.mark.asyncio
    async def test_add_test_environments(self, tool, test_issues):
        """Test adding test environments to execution."""
        # Create execution without environments
        create_result = await tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': f"Execution for environments {uuid.uuid4().hex[:8]}",
            'test_ids': [test_issues[0]]
        })
        
        # Add environments
        env_result = await tool.execute({
            'action': 'add_environments',
            'issue_id': create_result['issueId'],
            'environments': ['PROD', 'STAGING']
        })
        
        assert env_result['success'] is True
        assert 'associatedTestEnvironments' in env_result or 'createdTestEnvironments' in env_result
        
        # Store for cleanup
        pytest.execution_id = create_result['issueId']
    
    @pytest.mark.asyncio
    async def test_remove_test_environments(self, tool, test_issues):
        """Test removing test environments from execution."""
        # Create execution with environments
        create_result = await tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': f"Execution env removal {uuid.uuid4().hex[:8]}",
            'test_ids': [test_issues[0]],
            'test_environments': ['DEV', 'QA', 'PROD']
        })
        
        # Remove some environments
        remove_result = await tool.execute({
            'action': 'remove_environments',
            'issue_id': create_result['issueId'],
            'environments': ['DEV']
        })
        
        assert remove_result['success'] is True
        
        # Store for cleanup
        pytest.execution_id = create_result['issueId']
    
    @pytest.mark.asyncio
    async def test_list_test_executions(self, tool):
        """Test listing test executions in project."""
        result = await tool.execute({
            'action': 'list',
            'project_key': 'FTEST',
            'limit': 5
        })
        
        assert 'executions' in result
        assert 'total' in result
        assert isinstance(result['executions'], list)
        
        if result['executions']:
            execution = result['executions'][0]
            assert 'issueId' in execution
            assert 'issueKey' in execution
            assert 'summary' in execution
    
    @pytest.mark.asyncio
    async def test_get_test_runs_for_execution(self, tool, test_issues):
        """Test getting test runs associated with an execution."""
        # Create execution with tests
        create_result = await tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': f"Execution with runs {uuid.uuid4().hex[:8]}",
            'test_ids': test_issues[:2]
        })
        
        # Get test runs
        runs_result = await tool.execute({
            'action': 'get_test_runs',
            'issue_id': create_result['issueId'],
            'limit': 10
        })
        
        assert 'testRuns' in runs_result
        assert 'total' in runs_result
        assert isinstance(runs_result['testRuns'], list)
        
        # Should have test runs for the tests we added
        if runs_result['testRuns']:
            run = runs_result['testRuns'][0]
            assert 'id' in run
            assert 'status' in run
            assert 'test' in run
        
        # Store for cleanup
        pytest.execution_id = create_result['issueId']
    
    @pytest.mark.asyncio
    async def test_delete_test_execution(self, tool, test_issues):
        """Test deleting a test execution."""
        # Create execution to delete
        create_result = await tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': f"Execution to delete {uuid.uuid4().hex[:8]}",
            'test_ids': [test_issues[0]]
        })
        
        # Delete it
        delete_result = await tool.execute({
            'action': 'delete',
            'issue_id': create_result['issueId']
        })
        
        assert delete_result['success'] is True
        
        # Verify it's gone
        with pytest.raises(Exception):
            await tool.execute({
                'action': 'get',
                'issue_id': create_result['issueId']
            })
    
    @pytest.mark.asyncio
    async def test_error_handling(self, tool):
        """Test error handling for invalid operations."""
        # Try to get non-existent execution
        with pytest.raises(Exception) as exc_info:
            await tool.execute({
                'action': 'get',
                'issue_id': '999999999'
            })
        
        assert 'not found' in str(exc_info.value).lower() or 'error' in str(exc_info.value).lower()
        
        # Try to add tests to non-existent execution
        with pytest.raises(Exception) as exc_info:
            await tool.execute({
                'action': 'add_tests',
                'issue_id': '999999999',
                'test_ids': ['123']
            })
        
        assert 'error' in str(exc_info.value).lower()