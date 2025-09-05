import pytest
import os
import uuid
from dotenv import load_dotenv
from src.auth import XrayAuth
from src.graphql_client import XrayGraphQLClient
from src.tools.test_tool import TestTool

load_dotenv()

class TestTestToolIntegration:
    """Integration tests for Test tool against live API."""
    
    @pytest.fixture
    async def tool(self):
        """Create Test tool with authenticated client."""
        auth = XrayAuth(
            client_id=os.getenv('XRAY_CLIENT_ID'),
            client_secret=os.getenv('XRAY_CLIENT_SECRET')
        )
        await auth.authenticate()
        client = XrayGraphQLClient(auth)
        return TestTool(client)
    
    @pytest.fixture
    def test_summary(self):
        """Generate unique test summary."""
        return f"Integration Test {uuid.uuid4().hex[:8]}"
    
    @pytest.mark.asyncio
    async def test_create_manual_test(self, tool, test_summary):
        """Test creating a manual test in FTEST project."""
        result = await tool.execute({
            'action': 'create',
            'test_type': 'Manual',
            'project_key': 'FTEST',
            'summary': test_summary,
            'description': 'Created by integration test',
            'steps': [
                {
                    'action': 'Step 1: Open application',
                    'data': 'Test data',
                    'result': 'Application opens'
                },
                {
                    'action': 'Step 2: Perform action',
                    'result': 'Action successful'
                }
            ]
        })
        
        # Verify response structure
        assert 'issueId' in result
        assert 'issueKey' in result
        assert result['issueKey'].startswith('FTEST-')
        assert result['testType'] == 'Manual'
        assert result['summary'] == test_summary
        
        # Store for cleanup
        pytest.test_issue_id = result['issueId']
        return result
    
    @pytest.mark.asyncio
    async def test_get_test(self, tool):
        """Test fetching a test by issue ID."""
        # First create a test
        create_result = await tool.execute({
            'action': 'create',
            'test_type': 'Generic',
            'project_key': 'FTEST',
            'summary': f"Test to fetch {uuid.uuid4().hex[:8]}",
            'description': 'Test generic test'
        })
        
        # Now fetch it
        get_result = await tool.execute({
            'action': 'get',
            'issue_id': create_result['issueId']
        })
        
        assert get_result['issueId'] == create_result['issueId']
        assert get_result['summary'] == create_result['summary']
        assert 'testType' in get_result
        
        # Store for cleanup
        pytest.test_issue_id = create_result['issueId']
    
    @pytest.mark.asyncio
    async def test_update_test(self, tool):
        """Test updating a test."""
        # Create a test
        create_result = await tool.execute({
            'action': 'create',
            'test_type': 'Generic',
            'project_key': 'FTEST',
            'summary': f"Test to update {uuid.uuid4().hex[:8]}",
            'description': 'Original description'
        })
        
        # Update it
        new_description = 'Updated description'
        update_result = await tool.execute({
            'action': 'update',
            'issue_id': create_result['issueId'],
            'description': new_description,
            'test_type': 'Manual',
            'steps': [
                {'action': 'Updated step', 'result': 'Updated result'}
            ]
        })
        
        assert update_result['issueId'] == create_result['issueId']
        assert update_result['testType'] == 'Manual'
        
        # Store for cleanup
        pytest.test_issue_id = create_result['issueId']
    
    @pytest.mark.asyncio
    async def test_list_tests(self, tool):
        """Test listing tests in project."""
        result = await tool.execute({
            'action': 'list',
            'project_key': 'FTEST',
            'limit': 5
        })
        
        assert 'tests' in result
        assert 'total' in result
        assert isinstance(result['tests'], list)
        
        if result['tests']:
            test = result['tests'][0]
            assert 'issueId' in test
            assert 'issueKey' in test
            assert 'summary' in test
            assert 'testType' in test
    
    @pytest.mark.asyncio
    async def test_delete_test(self, tool):
        """Test deleting a test."""
        # Create a test to delete
        create_result = await tool.execute({
            'action': 'create',
            'test_type': 'Generic',
            'project_key': 'FTEST',
            'summary': f"Test to delete {uuid.uuid4().hex[:8]}",
            'description': 'Will be deleted'
        })
        
        # Delete it
        delete_result = await tool.execute({
            'action': 'delete',
            'issue_id': create_result['issueId']
        })
        
        assert delete_result['success'] is True
        assert 'message' in delete_result
        
        # Verify it's gone
        with pytest.raises(Exception):
            await tool.execute({
                'action': 'get',
                'issue_id': create_result['issueId']
            })
    
    @pytest.mark.asyncio
    async def test_error_handling(self, tool):
        """Test error handling for invalid operations."""
        # Try to get non-existent test
        with pytest.raises(Exception) as exc_info:
            await tool.execute({
                'action': 'get',
                'issue_id': '999999999'
            })
        
        assert 'not found' in str(exc_info.value).lower() or 'error' in str(exc_info.value).lower()
        
        # Try invalid action
        with pytest.raises(ValueError) as exc_info:
            await tool.execute({
                'action': 'invalid_action'
            })
        
        assert 'invalid action' in str(exc_info.value).lower()