import pytest
import os
from dotenv import load_dotenv
from src.auth import XrayAuth
from src.graphql_client import XrayGraphQLClient

load_dotenv()

class TestXrayGraphQLIntegration:
    """Integration tests for GraphQL client against live API."""
    
    @pytest.fixture
    async def client(self):
        """Create authenticated GraphQL client."""
        auth = XrayAuth(
            client_id=os.getenv('XRAY_CLIENT_ID'),
            client_secret=os.getenv('XRAY_CLIENT_SECRET')
        )
        await auth.authenticate()
        return XrayGraphQLClient(auth)
    
    @pytest.mark.asyncio
    async def test_get_project_settings(self, client):
        """Test fetching project settings for FTEST project."""
        query = """
        query GetProjectSettings($projectKey: String!) {
            getProjectSettings(projectIdOrKey: $projectKey) {
                projectId
                testEnvironments
                testTypeSettings {
                    testTypes {
                        id
                        name
                        kind
                    }
                }
            }
        }
        """
        
        result = await client.execute(query, {'projectKey': 'FTEST'})
        
        # Verify we got project settings
        assert 'getProjectSettings' in result
        settings = result['getProjectSettings']
        assert settings['projectId']
        assert 'testTypeSettings' in settings
        assert 'testTypes' in settings['testTypeSettings']
        
        # Should have standard test types
        test_types = [t['name'] for t in settings['testTypeSettings']['testTypes']]
        assert 'Manual' in test_types or 'Generic' in test_types
    
    @pytest.mark.asyncio
    async def test_get_tests_in_project(self, client):
        """Test fetching tests from FTEST project."""
        query = """
        query GetTests($jql: String!, $limit: Int!) {
            getTests(jql: $jql, limit: $limit) {
                total
                start
                results {
                    issueId
                    projectId
                    testType {
                        name
                        kind
                    }
                }
            }
        }
        """
        
        variables = {
            'jql': f"project = 'FTEST' AND issuetype = 'Test'",
            'limit': 10
        }
        
        result = await client.execute(query, variables)
        
        assert 'getTests' in result
        tests = result['getTests']
        assert 'total' in tests
        assert 'results' in tests
        
        # If there are tests, verify structure
        if tests['results']:
            test = tests['results'][0]
            assert 'issueId' in test
            assert 'testType' in test
            assert 'name' in test['testType']
    
    @pytest.mark.asyncio
    async def test_invalid_query(self, client):
        """Test error handling for invalid GraphQL query."""
        query = """
        query {
            invalidField {
                doesNotExist
            }
        }
        """
        
        with pytest.raises(Exception) as exc_info:
            await client.execute(query)
        
        assert 'error' in str(exc_info.value).lower() or 'invalid' in str(exc_info.value).lower()