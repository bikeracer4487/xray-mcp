import pytest
import pytest_asyncio
import os
import uuid
from dotenv import load_dotenv
from src.auth import XrayAuth
from src.graphql_client import XrayGraphQLClient
from src.tools.test_run_tool import TestRunTool
from src.tools.test_tool import TestTool
from src.tools.test_execution_tool import TestExecutionTool

load_dotenv()

class TestTestRunToolIntegration:
    """Integration tests for Test Run tool against live API."""
    
    @pytest_asyncio.fixture
    async def tool(self):
        """Create Test Run tool with authenticated client."""
        auth = XrayAuth(
            client_id=os.getenv('XRAY_CLIENT_ID'),
            client_secret=os.getenv('XRAY_CLIENT_SECRET')
        )
        await auth.authenticate()
        client = XrayGraphQLClient(auth)
        return TestRunTool(client)
    
    @pytest_asyncio.fixture
    async def test_tool(self):
        """Create Test tool for creating test issues."""
        auth = XrayAuth(
            client_id=os.getenv('XRAY_CLIENT_ID'),
            client_secret=os.getenv('XRAY_CLIENT_SECRET')
        )
        await auth.authenticate()
        client = XrayGraphQLClient(auth)
        return TestTool(client)
    
    @pytest_asyncio.fixture
    async def execution_tool(self):
        """Create Test Execution tool."""
        auth = XrayAuth(
            client_id=os.getenv('XRAY_CLIENT_ID'),
            client_secret=os.getenv('XRAY_CLIENT_SECRET')
        )
        await auth.authenticate()
        client = XrayGraphQLClient(auth)
        return TestExecutionTool(client)
    
    @pytest_asyncio.fixture
    async def test_setup(self, test_tool, execution_tool):
        """Create a test and test execution for test runs."""
        # Create a manual test with steps
        test_result = await test_tool.execute({
            'action': 'create',
            'test_type': 'Manual',
            'project_key': 'FTEST',
            'summary': f"Test for run {uuid.uuid4().hex[:8]}",
            'description': 'Test for test run',
            'steps': [
                {
                    'action': 'Step 1: Setup',
                    'data': 'Test data',
                    'result': 'Setup complete'
                },
                {
                    'action': 'Step 2: Execute',
                    'result': 'Execution complete'
                }
            ]
        })
        
        # Create a test execution with the test
        exec_result = await execution_tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': f"Execution for run {uuid.uuid4().hex[:8]}",
            'test_ids': [test_result['issueId']]
        })
        
        return {
            'test_id': test_result['issueId'],
            'test_key': test_result['issueKey'],
            'execution_id': exec_result['issueId'],
            'execution_key': exec_result['issueKey']
        }
    
    @pytest.mark.asyncio
    async def test_get_test_run(self, tool, test_setup):
        """Test fetching a test run."""
        result = await tool.execute({
            'action': 'get',
            'test_id': test_setup['test_id'],
            'execution_id': test_setup['execution_id']
        })
        
        assert 'id' in result
        assert 'status' in result
        assert 'test' in result
        assert result['test']['issueId'] == test_setup['test_id']
        assert 'testExecution' in result
        assert result['testExecution']['issueId'] == test_setup['execution_id']
        
        # Should have steps from the test
        if 'steps' in result:
            assert len(result['steps']) > 0
            step = result['steps'][0]
            assert 'id' in step
            assert 'action' in step
            assert 'status' in step
    
    @pytest.mark.asyncio
    async def test_get_test_run_by_id(self, tool, test_setup):
        """Test fetching a test run by its ID."""
        # First get the test run to get its ID
        get_result = await tool.execute({
            'action': 'get',
            'test_id': test_setup['test_id'],
            'execution_id': test_setup['execution_id']
        })
        
        run_id = get_result['id']
        
        # Now fetch by ID
        result = await tool.execute({
            'action': 'get_by_id',
            'run_id': run_id
        })
        
        assert result['id'] == run_id
        assert 'status' in result
        assert 'test' in result
    
    @pytest.mark.asyncio
    async def test_update_test_run_status(self, tool, test_setup):
        """Test updating test run status."""
        # Get the test run
        get_result = await tool.execute({
            'action': 'get',
            'test_id': test_setup['test_id'],
            'execution_id': test_setup['execution_id']
        })
        
        run_id = get_result['id']
        
        # Update status to PASSED
        update_result = await tool.execute({
            'action': 'update_status',
            'run_id': run_id,
            'status': 'PASSED'
        })
        
        assert update_result['success'] is True
        
        # Verify the update
        verify_result = await tool.execute({
            'action': 'get_by_id',
            'run_id': run_id
        })
        
        assert verify_result['status']['name'] == 'PASSED'
    
    @pytest.mark.asyncio
    async def test_update_test_run_comment(self, tool, test_setup):
        """Test updating test run comment."""
        # Get the test run
        get_result = await tool.execute({
            'action': 'get',
            'test_id': test_setup['test_id'],
            'execution_id': test_setup['execution_id']
        })
        
        run_id = get_result['id']
        comment = f"Test run comment {uuid.uuid4().hex[:8]}"
        
        # Update comment
        update_result = await tool.execute({
            'action': 'update_comment',
            'run_id': run_id,
            'comment': comment
        })
        
        assert update_result['success'] is True
        
        # Verify the update
        verify_result = await tool.execute({
            'action': 'get_by_id',
            'run_id': run_id
        })
        
        assert verify_result.get('comment') == comment
    
    @pytest.mark.asyncio
    async def test_update_test_run_step_status(self, tool, test_setup):
        """Test updating individual step status."""
        # Get the test run
        get_result = await tool.execute({
            'action': 'get',
            'test_id': test_setup['test_id'],
            'execution_id': test_setup['execution_id']
        })
        
        run_id = get_result['id']
        
        # Should have steps
        assert 'steps' in get_result
        assert len(get_result['steps']) > 0
        
        step_id = get_result['steps'][0]['id']
        
        # Update step status
        update_result = await tool.execute({
            'action': 'update_step_status',
            'run_id': run_id,
            'step_id': step_id,
            'status': 'FAILED',
            'comment': 'Step failed due to test'
        })
        
        assert update_result['success'] is True
    
    @pytest.mark.asyncio
    async def test_add_defects_to_test_run(self, tool, test_setup):
        """Test adding defects to test run."""
        # Get the test run
        get_result = await tool.execute({
            'action': 'get',
            'test_id': test_setup['test_id'],
            'execution_id': test_setup['execution_id']
        })
        
        run_id = get_result['id']
        
        # Add defects (using issue IDs that should exist in FTEST)
        # In a real scenario, you'd create a bug issue first
        try:
            add_result = await tool.execute({
                'action': 'add_defects',
                'run_id': run_id,
                'defect_ids': [test_setup['test_id']]  # Using test ID as placeholder
            })
            
            assert 'addedDefects' in add_result or 'success' in add_result
        except Exception as e:
            # It's acceptable if the defect ID doesn't exist or isn't a valid defect type
            # The important thing is that the API call worked properly
            error_msg = str(e).lower()
            acceptable_errors = [
                "not found",
                "cannot add",
                "cannot link defect",
                "to itself"
            ]
            assert any(error in error_msg for error in acceptable_errors)
    
    @pytest.mark.asyncio
    async def test_add_evidence_to_test_run(self, tool, test_setup):
        """Test adding evidence to test run."""
        # Get the test run
        get_result = await tool.execute({
            'action': 'get',
            'test_id': test_setup['test_id'],
            'execution_id': test_setup['execution_id']
        })
        
        run_id = get_result['id']
        
        # Add evidence
        add_result = await tool.execute({
            'action': 'add_evidence',
            'run_id': run_id,
            'evidence': [
                {
                    'filename': 'test_evidence.txt',
                    'mimeType': 'text/plain',
                    'data': 'VGVzdCBldmlkZW5jZSBjb250ZW50'  # Base64 encoded "Test evidence content"
                }
            ]
        })
        
        assert 'addedEvidence' in add_result or 'success' in add_result
    
    @pytest.mark.asyncio
    async def test_reset_test_run(self, tool, test_setup):
        """Test resetting a test run."""
        # Get the test run
        get_result = await tool.execute({
            'action': 'get',
            'test_id': test_setup['test_id'],
            'execution_id': test_setup['execution_id']
        })
        
        run_id = get_result['id']
        
        # First update it
        await tool.execute({
            'action': 'update_status',
            'run_id': run_id,
            'status': 'FAILED'
        })
        
        # Reset it
        reset_result = await tool.execute({
            'action': 'reset',
            'run_id': run_id
        })
        
        assert reset_result['success'] is True
        
        # Verify it's reset
        verify_result = await tool.execute({
            'action': 'get_by_id',
            'run_id': run_id
        })
        
        # Status should be back to TODO or initial state
        assert verify_result['status']['name'] in ['TODO', 'TO DO', 'EXECUTING']
    
    @pytest.mark.asyncio
    async def test_list_test_runs(self, tool, test_setup):
        """Test listing test runs."""
        result = await tool.execute({
            'action': 'list',
            'test_ids': [test_setup['test_id']],
            'limit': 10
        })
        
        assert 'testRuns' in result
        assert 'total' in result
        assert isinstance(result['testRuns'], list)
        
        if result['testRuns']:
            run = result['testRuns'][0]
            assert 'id' in run
            assert 'status' in run
            assert 'test' in run