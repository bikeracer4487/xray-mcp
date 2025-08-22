"""
Pytest configuration and fixtures for Xray MCP E2E tests.

This module provides:
- MCP server process management
- Xray API authentication and stubbing
- Playwright browser fixtures for visual testing
- Test data lifecycle management
- Environment configuration
"""

import asyncio
import json
import os
import subprocess
import time
from pathlib import Path
from typing import Dict, Any, Generator, AsyncGenerator, List, Optional
import pytest
import signal
import requests
from dotenv import load_dotenv

# Import test utilities
from fixtures.mcp_client import XrayMCPClient
from fixtures.xray_stub import XrayStub
from fixtures.test_data_manager import TestDataManager
from fixtures.visual_validators import XrayVisualValidator


# Load environment variables
ROOT_DIR = Path(__file__).resolve().parents[2]
load_dotenv(ROOT_DIR / ".env")
load_dotenv(Path(__file__).parent / ".env")

# Test artifacts directory
ARTIFACTS_DIR = Path(__file__).parent / ".artifacts"
ARTIFACTS_DIR.mkdir(exist_ok=True)


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """
    Validate and provide test configuration from environment variables.
    
    Returns:
        Dict containing validated environment configuration
        
    Raises:
        pytest.skip: If required environment variables are missing
    """
    def required(name: str) -> str:
        value = os.getenv(name)
        if not value:
            pytest.skip(f"Missing required environment variable: {name}")
        return value
    
    def optional(name: str, default: Any = None) -> Any:
        return os.getenv(name, default)
    
    # Required Xray configuration
    config = {
        "xray_client_id": required("XRAY_CLIENT_ID"),
        "xray_client_secret": required("XRAY_CLIENT_SECRET"),
        "test_project": required("TEST_PROJECT"),
    }
    
    # Optional configuration with defaults
    config.update({
        "xray_base_url": optional("XRAY_BASE_URL", "https://xray.cloud.getxray.app"),
        "jira_base_url": optional("JIRA_BASE_URL", "https://your-instance.atlassian.net"),
        "jira_username": optional("JIRA_USERNAME"),
        "jira_api_token": optional("JIRA_API_TOKEN"),
        "mcp_server_url": optional("MCP_SERVER_URL", "http://localhost:8000"),
        "mcp_server_timeout": int(optional("MCP_SERVER_TIMEOUT", 30)),
        "test_label": optional("TEST_LABEL", f"xray-mcp-e2e-test-{os.getpid()}"),
        "test_data_prefix": optional("TEST_DATA_PREFIX", "XrayMCP_E2E"),
        "browser_headless": optional("BROWSER_HEADLESS", "true").lower() == "true",
        "browser_slow_mo": int(optional("BROWSER_SLOW_MO", 0)),
        "browser_timeout": int(optional("BROWSER_TIMEOUT", 30000)),
        "cleanup_on_success": optional("CLEANUP_ON_SUCCESS", "true").lower() == "true",
        "cleanup_on_failure": optional("CLEANUP_ON_FAILURE", "false").lower() == "true",
        "debug_level": optional("DEBUG_LEVEL", "INFO"),
        "capture_screenshots": optional("CAPTURE_SCREENSHOTS", "true").lower() == "true",
        "capture_videos": optional("CAPTURE_VIDEOS", "false").lower() == "true",
    })
    
    return config


@pytest.fixture(scope="session")
def mcp_server_process(test_config):
    """
    Start MCP server process and ensure it's responsive.
    
    Args:
        test_config: Test configuration with MCP server URL
        
    Yields:
        subprocess.Popen: Running MCP server process
    """
    # Extract port from MCP URL
    mcp_url = test_config["mcp_server_url"]
    try:
        port = int(mcp_url.split(":")[-1])
    except (ValueError, IndexError):
        port = 8000
    
    # Start the MCP server
    cmd = ["python", "main.py", "--port", str(port)]
    
    # Start server in project root directory
    server_process = subprocess.Popen(
        cmd,
        cwd=ROOT_DIR,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        preexec_fn=os.setsid  # Create new process group for clean shutdown
    )
    
    # Wait for server to be responsive
    max_wait = test_config["mcp_server_timeout"]
    start_time = time.time()
    server_ready = False
    
    while time.time() - start_time < max_wait:
        try:
            response = requests.get(f"http://localhost:{port}/health", timeout=1)
            if response.status_code == 200:
                server_ready = True
                break
        except requests.RequestException:
            pass
        time.sleep(0.5)
    
    if not server_ready:
        # Capture server output for debugging
        stdout, stderr = server_process.communicate(timeout=5)
        server_process.kill()
        pytest.fail(f"MCP server failed to start within {max_wait}s. Stdout: {stdout}, Stderr: {stderr}")
    
    try:
        yield server_process
    finally:
        # Clean shutdown
        try:
            os.killpg(os.getpgid(server_process.pid), signal.SIGTERM)
            server_process.wait(timeout=10)
        except (subprocess.TimeoutExpired, ProcessLookupError):
            try:
                os.killpg(os.getpgid(server_process.pid), signal.SIGKILL)
            except ProcessLookupError:
                pass


@pytest.fixture
async def mcp_client(mcp_server_process, test_config):
    """
    Create MCP client for individual test functions.
    
    Args:
        mcp_server_process: Running MCP server process
        test_config: Test configuration
        
    Returns:
        XrayMCPClient: MCP client instance
    """
    client = XrayMCPClient(test_config["mcp_server_url"])
    await client.connect()
    
    try:
        yield client
    finally:
        await client.disconnect()


@pytest.fixture
def xray_stub(test_config):
    """
    Create Xray HTTP API stub for mocking external requests.
    
    Args:
        test_config: Test configuration
        
    Returns:
        XrayStub: HTTP stubbing utility
    """
    stub = XrayStub(test_config["xray_base_url"])
    stub.setup()
    
    try:
        yield stub
    finally:
        stub.teardown()


@pytest.fixture
async def test_data_manager(test_config):
    """
    Create test data manager for resource lifecycle management.
    
    Args:
        test_config: Test configuration
        
    Returns:
        TestDataManager: Test data management utility
    """
    manager = TestDataManager(
        project_key=test_config["test_project"],
        prefix=test_config["test_data_prefix"],
        label=test_config["test_label"],
        cleanup_on_success=test_config["cleanup_on_success"],
        cleanup_on_failure=test_config["cleanup_on_failure"]
    )
    
    try:
        yield manager
    finally:
        await manager.cleanup()


@pytest.fixture
async def visual_validator(test_config, page):
    """
    Create visual validator for Playwright-based verification.
    
    Args:
        test_config: Test configuration
        page: Playwright page fixture
        
    Returns:
        XrayVisualValidator: Visual validation utility
    """
    validator = XrayVisualValidator(
        artifacts_dir=ARTIFACTS_DIR,
        base_url=test_config["jira_base_url"],
        capture_screenshots=test_config["capture_screenshots"]
    )
    
    # Authenticate with Jira if credentials provided
    if test_config["jira_username"] and test_config["jira_api_token"]:
        await validator.authenticate(
            page, 
            test_config["jira_username"],
            test_config["jira_api_token"]
        )
    
    try:
        yield validator
    finally:
        await validator.cleanup()


# Playwright configuration
@pytest.fixture(scope="session")
def browser_context_args(test_config):
    """Configure browser context arguments."""
    return {
        "viewport": {"width": 1920, "height": 1080},
        "ignore_https_errors": True,
        "record_video_dir": ARTIFACTS_DIR / "videos" if test_config["capture_videos"] else None,
    }


@pytest.fixture
async def browser_page(test_config, context):
    """Create a new browser page for each test."""
    page = await context.new_page()
    
    # Configure page settings
    page.set_default_timeout(test_config["browser_timeout"])
    
    if test_config["browser_slow_mo"] > 0:
        await page.set_extra_http_headers({"X-Slow-Mo": str(test_config["browser_slow_mo"])})
    
    try:
        yield page
    finally:
        # Capture screenshot on failure
        if test_config["capture_screenshots"]:
            screenshot_path = ARTIFACTS_DIR / "screenshots" / f"failure_{int(time.time())}.png"
            screenshot_path.parent.mkdir(exist_ok=True)
            try:
                await page.screenshot(path=screenshot_path)
            except:
                pass  # Ignore screenshot errors
        
        await page.close()


# Test markers for categorization
def pytest_configure(config):
    """Configure test markers."""
    config.addinivalue_line("markers", "contract: MCP contract validation tests")
    config.addinivalue_line("markers", "visual: Playwright visual verification tests")
    config.addinivalue_line("markers", "integration: End-to-end integration tests")
    config.addinivalue_line("markers", "slow: Slow running tests")
    config.addinivalue_line("markers", "smoke: Quick smoke tests")


# Test collection customization
def pytest_collection_modifyitems(config, items):
    """Modify test collection to add markers based on file location."""
    for item in items:
        # Add markers based on file path
        if "contracts/" in str(item.fspath):
            item.add_marker(pytest.mark.contract)
        elif "visual/" in str(item.fspath):
            item.add_marker(pytest.mark.visual)
        elif "integration/" in str(item.fspath):
            item.add_marker(pytest.mark.integration)
        
        # Mark visual tests as slow by default
        if hasattr(item, "get_closest_marker") and item.get_closest_marker("visual"):
            item.add_marker(pytest.mark.slow)


# Session-scoped cleanup
@pytest.fixture(scope="session", autouse=True)
def cleanup_session():
    """Cleanup session-level resources."""
    yield
    
    # Clean up any remaining artifacts if needed
    # This runs after all tests complete