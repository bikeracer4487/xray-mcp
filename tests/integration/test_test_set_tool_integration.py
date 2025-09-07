import pytest
import pytest_asyncio
import os
import uuid
from dotenv import load_dotenv
from src.auth import XrayAuth
from src.graphql_client import XrayGraphQLClient
from src.tools.test_set_tool import TestSetTool
from src.tools.test_tool import TestTool

load_dotenv()

class TestTestSetToolIntegration:
    """Integration tests for Test Set tool against live API."""
    
    @pytest_asyncio.fixture
    async def tool(self):
        """Create Test Set tool with authenticated client."""
        auth = XrayAuth(
            client_id=os.getenv('XRAY_CLIENT_ID'),
            client_secret=os.getenv('XRAY_CLIENT_SECRET')
        )
        await auth.authenticate()
        client = XrayGraphQLClient(auth)
        return TestSetTool(client)
    
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
    async def test_issues(self, test_tool):
        """Create test issues to use in test sets."""
        tests = []
        for i in range(2):
            result = await test_tool.execute({
                'action': 'create',
                'test_type': 'Generic',
                'project_key': 'FTEST',
                'summary': f"Test for set {uuid.uuid4().hex[:8]}",
                'description': 'Test for test set'
            })
            tests.append(result['issueId'])
        return tests
    
    @pytest.mark.asyncio
    async def test_create_test_set(self, tool, test_issues):
        """Test creating a test set with tests."""
        summary = f"Test Set {uuid.uuid4().hex[:8]}"
        result = await tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': summary,
            'description': 'Integration test set',
            'test_ids': test_issues
        })
        
        assert 'issueId' in result
        assert 'issueKey' in result
        assert result['issueKey'].startswith('FTEST-')
        assert result['summary'] == summary
        assert 'tests' in result
        
        # Store for cleanup
        pytest.test_set_id = result['issueId']
    
    @pytest.mark.asyncio
    async def test_add_tests_to_test_set(self, tool, test_tool, test_issues):
        """Test adding tests to existing test set."""
        # Create test set
        create_result = await tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': f"Set for adding {uuid.uuid4().hex[:8]}",
            'test_ids': [test_issues[0]]
        })
        
        # Add more tests
        add_result = await tool.execute({
            'action': 'add_tests',
            'issue_id': create_result['issueId'],
            'test_ids': [test_issues[1]]
        })
        
        assert add_result['success'] is True
        assert 'addedTests' in add_result
        
        # Store for cleanup
        pytest.test_set_id = create_result['issueId']
    
    @pytest.mark.asyncio
    async def test_remove_tests_from_test_set(self, tool, test_issues):
        """Test removing tests from test set."""
        # Create test set with tests
        create_result = await tool.execute({
            'action': 'create',
            'project_key': 'FTEST',
            'summary': f"Set for removal {uuid.uuid4().hex[:8]}",
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
        pytest.test_set_id = create_result['issueId']
    
    @pytest.mark.asyncio
    async def test_list_test_sets(self, tool):
        """Test listing test sets in project."""
        result = await tool.execute({
            'action': 'list',
            'project_key': 'FTEST',
            'limit': 5
        })
        
        assert 'testSets' in result
        assert 'total' in result
        assert isinstance(result['testSets'], list)