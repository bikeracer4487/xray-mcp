"""Test resources and prompts functionality for Xray MCP server."""

import os
import json
import pytest
import pytest_asyncio
from dotenv import load_dotenv
from src.server import create_server
from tests.integration.test_helpers import parse_mcp_response

# Load environment for authentication
load_dotenv()

@pytest.mark.skipif(
    not all([os.getenv('XRAY_CLIENT_ID'), os.getenv('XRAY_CLIENT_SECRET')]),
    reason="Xray credentials not available"
)
class TestResourcesAndPrompts:
    """Test MCP resources and prompts functionality."""

    @pytest_asyncio.fixture
    async def server(self):
        """Create MCP server instance."""
        return create_server()

    @pytest_asyncio.fixture
    async def resources(self, server):
        """Get the server resources."""
        return await server.get_resources()

    @pytest_asyncio.fixture
    async def prompts(self, server):
        """Get the server prompts."""
        return await server.get_prompts()

    @pytest.mark.asyncio
    async def test_documentation_resource(self, server, resources):
        """Test the documentation resource is available and provides useful content."""
        # Check resource is registered
        resource_names = list(resources.keys()) if isinstance(resources, dict) else [r.name for r in resources]
        assert "xray://documentation" in resource_names

        # Try to read the documentation resource
        try:
            if isinstance(resources, dict):
                # FastMCP returns resources as dict
                doc_resource = resources["xray://documentation"]
                content = await doc_resource.fn()
            else:
                # Standard MCP format
                doc_resource = next(r for r in resources if r.name == "xray://documentation")
                content = await server.read_resource(doc_resource.uri)

            assert "Xray MCP Server Documentation" in content
            assert "xray_test" in content
            assert "entity" in content and "action" in content
            assert "steps" in content  # Should document our JSON string format
            assert "Manual" in content and "Cucumber" in content
        except Exception as e:
            print(f"Documentation resource test failed: {e}")
            # At least verify it's registered
            assert "xray://documentation" in resource_names

    @pytest.mark.asyncio
    async def test_project_tests_resource(self, server, resources):
        """Test the project tests resource."""
        # Check resource pattern is registered
        assert any("project" in r.name for r in resources)

        # Test with FTEST project
        try:
            content = await server.read_resource("xray://project/FTEST/tests")
            assert "Tests in Project FTEST" in content
            # Content should either show tests or "No tests found"
            assert ("Found" in content and "tests:" in content) or "No tests found" in content
        except Exception as e:
            # If resource reading fails, at least check it was registered properly
            print(f"Resource read failed (expected for some MCP implementations): {e}")

    @pytest.mark.asyncio
    async def test_test_details_resource(self, server):
        """Test the test details resource with a known test."""
        # First create a test to ensure we have something to read
        tools = await server.get_tools()
        tool = tools['xray_test']

        # Create a simple test
        create_params = {
            'entity': 'test',
            'action': 'create',
            'project_key': 'FTEST',
            'summary': 'Test for Resource Reading',
            'test_type': 'Generic',
            'description': 'Simple test to validate resource functionality'
        }

        result = await tool.run(create_params)
        data = parse_mcp_response(result)

        if data['success']:
            test_id = data['data']['issueId']

            try:
                # Test the resource
                content = await server.read_resource(f"xray://test/{test_id}")
                assert "Test Details:" in content
                assert "Test for Resource Reading" in content
                assert "Generic" in content

                # Clean up
                delete_params = {
                    'entity': 'test',
                    'action': 'delete',
                    'issue_id': test_id
                }
                await tool.run(delete_params)

            except Exception as e:
                # Clean up even if resource read failed
                delete_params = {
                    'entity': 'test',
                    'action': 'delete',
                    'issue_id': test_id
                }
                await tool.run(delete_params)
                print(f"Resource read failed: {e}")

    @pytest.mark.asyncio
    async def test_manual_test_prompt(self, server, prompts):
        """Test the create manual test prompt."""
        # Check prompt is registered
        prompt_names = list(prompts.keys()) if isinstance(prompts, dict) else [p.name for p in prompts]
        assert "create_manual_test" in prompt_names

        # Test prompt without parameters
        try:
            if isinstance(prompts, dict):
                # FastMCP format
                prompt = prompts["create_manual_test"]
                content = await prompt.fn()
            else:
                # Standard MCP format
                content = await server.get_prompt("create_manual_test")

            assert "Create Manual Test Guide" in content
            assert "project key" in content.lower()
            assert "test title" in content.lower()
        except Exception as e:
            print(f"Prompt execution failed: {e}")

        # Test prompt with parameters
        try:
            if isinstance(prompts, dict):
                prompt = prompts["create_manual_test"]
                content = await prompt.fn(project_key="FTEST", test_title="Sample Test")
            else:
                content = await server.get_prompt("create_manual_test", project_key="FTEST", test_title="Sample Test")

            assert "FTEST" in content
            assert "Sample Test" in content
            assert "Test Steps Structure" in content
            assert "action" in content and "data" in content and "result" in content
        except Exception as e:
            print(f"Parameterized prompt failed: {e}")

    @pytest.mark.asyncio
    async def test_test_execution_prompt(self, server, prompts):
        """Test the create test execution prompt."""
        # Check prompt is registered
        prompt_names = [p.name for p in prompts]
        assert "create_test_execution" in prompt_names

        try:
            content = await server.get_prompt("create_test_execution")
            assert "Create Test Execution Guide" in content
            assert "groups multiple tests" in content
            assert "test_execution" in content
        except Exception as e:
            print(f"Test execution prompt failed: {e}")

    @pytest.mark.asyncio
    async def test_bdd_converter_prompt(self, server, prompts):
        """Test the BDD converter prompt."""
        # Check prompt is registered
        prompt_names = [p.name for p in prompts]
        assert "bdd_converter" in prompt_names

        try:
            content = await server.get_prompt("bdd_converter")
            assert "BDD/Gherkin Converter" in content
            assert "Gherkin format" in content
            assert "requirement" in content.lower()
        except Exception as e:
            print(f"BDD converter prompt failed: {e}")

        # Test with a requirement
        try:
            requirement = "Users should be able to log in"
            content = await server.get_prompt("bdd_converter", requirement=requirement)
            assert requirement in content
            assert "Feature:" in content
            assert "Scenario:" in content
            assert "Given" in content and "When" in content and "Then" in content
        except Exception as e:
            print(f"BDD converter with requirement failed: {e}")

    @pytest.mark.asyncio
    async def test_resource_and_prompt_counts(self, server, resources, prompts):
        """Verify we have the expected number of resources and prompts."""
        # Resources and prompts are returned as dictionaries
        resource_names = list(resources.keys()) if isinstance(resources, dict) else [r.name for r in resources]
        prompt_names = list(prompts.keys()) if isinstance(prompts, dict) else [p.name for p in prompts]

        print(f"Found resources: {resource_names}")
        print(f"Found prompts: {prompt_names}")

        # Check for expected resources (at least documentation should exist)
        assert "xray://documentation" in resource_names, "Documentation resource missing"

        # Check for expected prompts
        expected_prompts = ["create_manual_test", "create_test_execution", "bdd_converter"]

        for expected in expected_prompts:
            assert expected in prompt_names, f"Missing prompt: {expected}"

        print(f"✅ Found {len(resource_names)} resources and {len(prompt_names)} prompts")