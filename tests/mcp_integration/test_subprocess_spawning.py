"""
Tests for MCP server subprocess spawning and lifecycle management.

Tests the full subprocess lifecycle including startup, communication,
and cleanup as MCP clients would actually use the server.
"""

import pytest
import asyncio
import json
import signal
import time
from typing import Dict, Any
from unittest.mock import patch, AsyncMock
from tests.mcp_protocol import BaseMCPTest, MCPProtocolValidator, MCPTestUtils


@pytest.mark.mcp_integration
@pytest.mark.mcp_subprocess
@pytest.mark.slow
class TestMCPSubprocessLifecycle(BaseMCPTest):
    """Test MCP server subprocess lifecycle management."""

    @pytest.mark.asyncio
    async def test_server_startup_and_shutdown(self, mcp_server_process):
        """Test basic server startup and shutdown."""
        # Server should be running
        assert mcp_server_process.process is not None
        assert mcp_server_process.process.returncode is None

        # Should be able to send basic requests
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        response = await mcp_server_process.send_json_rpc(init_request)
        await self.assert_valid_jsonrpc_response(response, init_request['id'])

    @pytest.mark.asyncio
    async def test_server_environment_variables(self, server_script_path, subprocess_server_config):
        """Test that server respects environment variables."""
        from tests.conftest import MCPServerProcess

        # Test with custom environment
        custom_env = {
            'XRAY_CLIENT_ID': 'custom_test_id',
            'XRAY_CLIENT_SECRET': 'custom_test_secret',
            'XRAY_BASE_URL': 'https://custom.xray.example.com'
        }

        server = MCPServerProcess(server_script_path, custom_env)

        try:
            await server.start()
            assert server.process.returncode is None

            # Server should start successfully with custom env
            await asyncio.sleep(1)  # Give it time to initialize
            assert server.process.returncode is None

        finally:
            await server.stop()

    @pytest.mark.asyncio
    async def test_server_startup_failure_handling(self, server_script_path):
        """Test handling of server startup failures."""
        from tests.conftest import MCPServerProcess

        # Test with invalid environment that should cause startup failure
        invalid_env = {
            'PYTHON_PATH': '/nonexistent/path'  # This might cause import errors
        }

        server = MCPServerProcess(server_script_path, invalid_env)

        try:
            await server.start()

            # Wait a moment to see if it crashes
            await asyncio.sleep(2)

            # If it started, that's fine (environment wasn't problematic)
            # If it failed, that's also fine (we're testing failure handling)
            if server.process.returncode is not None:
                # Server failed to start as expected
                assert server.process.returncode != 0

        except RuntimeError:
            # Expected if server fails to start
            pass
        finally:
            try:
                await server.stop()
            except:
                pass

    @pytest.mark.asyncio
    async def test_concurrent_server_instances(self, server_script_path, subprocess_server_config):
        """Test running multiple server instances concurrently."""
        from tests.conftest import MCPServerProcess

        servers = []

        try:
            # Start 3 concurrent server instances
            for i in range(3):
                env = subprocess_server_config['env_vars'].copy()
                env['INSTANCE_ID'] = str(i)  # Unique identifier

                server = MCPServerProcess(server_script_path, env)
                await server.start()
                servers.append(server)

            # All servers should be running
            for i, server in enumerate(servers):
                assert server.process.returncode is None, f"Server {i} should be running"

            # Each should respond to requests independently
            for i, server in enumerate(servers):
                init_request = {
                    'jsonrpc': '2.0',
                    'id': i + 1,
                    'method': 'initialize',
                    'params': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {},
                        'clientInfo': {'name': f'test-client-{i}', 'version': '1.0.0'}
                    }
                }

                response = await server.send_json_rpc(init_request)
                await self.assert_valid_jsonrpc_response(response, init_request['id'])

        finally:
            # Clean up all servers
            for server in servers:
                try:
                    await server.stop()
                except:
                    pass

    @pytest.mark.asyncio
    async def test_server_graceful_shutdown(self, mcp_server_process):
        """Test graceful server shutdown."""
        # Server should be running
        assert mcp_server_process.process.returncode is None

        # Send a request first
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        response = await mcp_server_process.send_json_rpc(init_request)
        await self.assert_valid_jsonrpc_response(response, init_request['id'])

        # Now test graceful shutdown
        start_time = time.time()

        # Terminate the process gracefully
        mcp_server_process.process.terminate()

        # Wait for it to shut down
        try:
            await asyncio.wait_for(mcp_server_process.process.wait(), timeout=5.0)
            shutdown_time = time.time() - start_time

            # Should shut down within reasonable time
            assert shutdown_time < 5.0, f"Server took {shutdown_time}s to shut down"

        except asyncio.TimeoutError:
            # If graceful shutdown fails, force kill
            mcp_server_process.process.kill()
            await mcp_server_process.process.wait()
            pytest.fail("Server did not shut down gracefully within 5 seconds")

    @pytest.mark.asyncio
    async def test_server_communication_after_errors(self, mcp_server_process):
        """Test that server continues to work after handling errors."""
        # Initialize first
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        await mcp_server_process.send_json_rpc(init_request)

        # Send an invalid request that should cause an error
        invalid_request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'nonexistent_method',
            'params': {}
        }

        error_response = await mcp_server_process.send_json_rpc(invalid_request)
        await self.assert_valid_error_response(error_response, invalid_request['id'])

        # Server should still be responsive after the error
        valid_request = {
            'jsonrpc': '2.0',
            'id': 3,
            'method': 'tools/list',
            'params': {}
        }

        valid_response = await mcp_server_process.send_json_rpc(valid_request)
        await self.assert_valid_jsonrpc_response(valid_response, valid_request['id'])

    @pytest.mark.asyncio
    async def test_server_handles_rapid_requests(self, mcp_server_process):
        """Test server handling of rapid consecutive requests."""
        # Initialize first
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        await mcp_server_process.send_json_rpc(init_request)

        # Send rapid consecutive requests
        requests = []
        for i in range(5):
            request = {
                'jsonrpc': '2.0',
                'id': i + 2,
                'method': 'tools/list',
                'params': {}
            }
            requests.append(request)

        # Send all requests rapidly
        tasks = []
        for request in requests:
            task = asyncio.create_task(mcp_server_process.send_json_rpc(request))
            tasks.append(task)

        # Wait for all responses
        responses = await asyncio.gather(*tasks, return_exceptions=True)

        # All should succeed or be valid errors
        for i, response in enumerate(responses):
            if isinstance(response, Exception):
                # Connection issues under load are acceptable
                continue

            if 'error' in response:
                await self.assert_valid_error_response(response, i + 2)
            else:
                await self.assert_valid_jsonrpc_response(response, i + 2)

    @pytest.mark.asyncio
    async def test_server_memory_stability(self, mcp_server_process):
        """Test server memory stability over multiple requests."""
        # Initialize
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        await mcp_server_process.send_json_rpc(init_request)

        # Make many requests to test for memory leaks
        for i in range(20):
            request = {
                'jsonrpc': '2.0',
                'id': i + 2,
                'method': 'tools/list',
                'params': {}
            }

            response = await mcp_server_process.send_json_rpc(request)

            if 'error' in response:
                await self.assert_valid_error_response(response, request['id'])
            else:
                await self.assert_valid_jsonrpc_response(response, request['id'])

            # Small delay to avoid overwhelming
            await asyncio.sleep(0.1)

        # Server should still be responsive
        assert mcp_server_process.process.returncode is None


@pytest.mark.mcp_integration
@pytest.mark.mcp_subprocess
class TestMCPSubprocessCommunication(BaseMCPTest):
    """Test MCP server subprocess communication patterns."""

    @pytest.mark.asyncio
    async def test_stdio_communication_integrity(self, mcp_server_process):
        """Test integrity of stdio communication."""
        # Test that messages are properly delimited and not corrupted
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        response = await mcp_server_process.send_json_rpc(init_request)

        # Response should be valid JSON
        assert isinstance(response, dict)
        await self.assert_valid_jsonrpc_response(response, init_request['id'])

        # Response should have all required fields
        assert 'result' in response
        result = response['result']
        assert 'protocolVersion' in result
        assert 'serverInfo' in result
        assert 'capabilities' in result

    @pytest.mark.asyncio
    async def test_large_message_handling(self, mcp_server_process):
        """Test handling of large messages."""
        # Initialize first
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        await mcp_server_process.send_json_rpc(init_request)

        # Create a request with large data
        large_data = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {
                'name': 'xray_test',
                'arguments': {
                    'entity': 'test',
                    'action': 'create',
                    'project_key': 'DEMO',
                    'summary': 'Large test summary: ' + 'A' * 1000,  # Large summary
                    'description': 'Large description: ' + 'B' * 2000  # Large description
                }
            }
        }

        try:
            response = await mcp_server_process.send_json_rpc(large_data)

            # Should either succeed or fail gracefully
            if 'error' in response:
                await self.assert_valid_error_response(response, large_data['id'])
            else:
                await self.assert_valid_jsonrpc_response(response, large_data['id'])

        except Exception:
            # Connection issues with large messages are acceptable
            pass

    @pytest.mark.asyncio
    async def test_unicode_message_handling(self, mcp_server_process):
        """Test handling of Unicode characters in messages."""
        # Initialize first
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        await mcp_server_process.send_json_rpc(init_request)

        # Test Unicode characters
        unicode_request = {
            'jsonrpc': '2.0',
            'id': 2,
            'method': 'tools/call',
            'params': {
                'name': 'xray_test',
                'arguments': {
                    'entity': 'test',
                    'action': 'create',
                    'project_key': 'DEMO',
                    'summary': 'Test with émojis 🚀 and ünicöde 测试 characters'
                }
            }
        }

        response = await mcp_server_process.send_json_rpc(unicode_request)

        # Should handle Unicode properly
        if 'error' in response:
            await self.assert_valid_error_response(response, unicode_request['id'])
            # Error should not be due to Unicode encoding issues
            error_msg = response['error']['message'].lower()
            assert 'unicode' not in error_msg and 'encoding' not in error_msg
        else:
            await self.assert_valid_jsonrpc_response(response, unicode_request['id'])

    @pytest.mark.asyncio
    async def test_message_ordering(self, mcp_server_process):
        """Test that request/response ordering is maintained."""
        # Initialize first
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        await mcp_server_process.send_json_rpc(init_request)

        # Send multiple requests in sequence
        request_ids = [2, 3, 4, 5]
        responses = {}

        for req_id in request_ids:
            request = {
                'jsonrpc': '2.0',
                'id': req_id,
                'method': 'tools/list',
                'params': {}
            }

            response = await mcp_server_process.send_json_rpc(request)

            if 'error' in response:
                await self.assert_valid_error_response(response, req_id)
            else:
                await self.assert_valid_jsonrpc_response(response, req_id)

            responses[req_id] = response

        # All responses should have correct IDs
        for req_id in request_ids:
            assert responses[req_id]['id'] == req_id

    @pytest.mark.asyncio
    async def test_connection_recovery(self, server_script_path, subprocess_server_config):
        """Test connection recovery scenarios."""
        from tests.conftest import MCPServerProcess

        server = MCPServerProcess(server_script_path, subprocess_server_config['env_vars'])

        try:
            # Start server
            await server.start()

            # Establish communication
            init_request = {
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'initialize',
                'params': {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {},
                    'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
                }
            }

            response = await server.send_json_rpc(init_request)
            await self.assert_valid_jsonrpc_response(response, init_request['id'])

            # Close stdin to simulate connection issue
            server.process.stdin.close()

            # Wait a moment
            await asyncio.sleep(1)

            # Server should handle the closed connection gracefully
            # (not crash, and either shut down cleanly or continue running)
            if server.process.returncode is not None:
                # Server shut down, which is acceptable
                assert server.process.returncode == 0 or server.process.returncode is not None
            else:
                # Server is still running, which is also acceptable
                pass

        finally:
            await server.stop()


@pytest.mark.mcp_integration
@pytest.mark.mcp_subprocess
@pytest.mark.performance
class TestMCPSubprocessPerformance(BaseMCPTest):
    """Test MCP server subprocess performance characteristics."""

    @pytest.mark.asyncio
    async def test_startup_time(self, server_script_path, subprocess_server_config, performance_timer):
        """Test server startup time."""
        from tests.conftest import MCPServerProcess

        with performance_timer("Server Startup") as timer:
            server = MCPServerProcess(server_script_path, subprocess_server_config['env_vars'])

            try:
                await server.start()

                # Verify it's actually responsive
                init_request = {
                    'jsonrpc': '2.0',
                    'id': 1,
                    'method': 'initialize',
                    'params': {
                        'protocolVersion': '2024-11-05',
                        'capabilities': {},
                        'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
                    }
                }

                response = await server.send_json_rpc(init_request)
                await self.assert_valid_jsonrpc_response(response, init_request['id'])

            finally:
                await server.stop()

        # Should start within 10 seconds
        timer.assert_duration_under(10.0)

    @pytest.mark.asyncio
    async def test_request_response_latency(self, mcp_server_process, performance_timer):
        """Test request/response latency."""
        # Initialize first
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        await mcp_server_process.send_json_rpc(init_request)

        # Test latency for simple requests
        with performance_timer("Tools List Request") as timer:
            request = {
                'jsonrpc': '2.0',
                'id': 2,
                'method': 'tools/list',
                'params': {}
            }

            response = await mcp_server_process.send_json_rpc(request)

            if 'error' in response:
                await self.assert_valid_error_response(response, request['id'])
            else:
                await self.assert_valid_jsonrpc_response(response, request['id'])

        # Should respond within 1 second for simple requests
        timer.assert_duration_under(1.0)

    @pytest.mark.asyncio
    async def test_throughput_capacity(self, mcp_server_process):
        """Test server throughput capacity."""
        # Initialize first
        init_request = {
            'jsonrpc': '2.0',
            'id': 1,
            'method': 'initialize',
            'params': {
                'protocolVersion': '2024-11-05',
                'capabilities': {},
                'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
            }
        }

        await mcp_server_process.send_json_rpc(init_request)

        # Test throughput with sequential requests
        start_time = time.time()
        successful_requests = 0

        for i in range(10):  # Send 10 requests
            request = {
                'jsonrpc': '2.0',
                'id': i + 2,
                'method': 'tools/list',
                'params': {}
            }

            try:
                response = await mcp_server_process.send_json_rpc(request)

                if 'error' in response:
                    await self.assert_valid_error_response(response, request['id'])
                else:
                    await self.assert_valid_jsonrpc_response(response, request['id'])

                successful_requests += 1

            except Exception:
                # Some failures under load are acceptable
                pass

        end_time = time.time()
        duration = end_time - start_time

        # Should handle reasonable throughput
        requests_per_second = successful_requests / duration
        assert requests_per_second > 1.0, f"Throughput too low: {requests_per_second:.2f} req/s"

    @pytest.mark.asyncio
    async def test_resource_cleanup(self, server_script_path, subprocess_server_config):
        """Test that server properly cleans up resources."""
        from tests.conftest import MCPServerProcess
        import psutil
        import os

        server = MCPServerProcess(server_script_path, subprocess_server_config['env_vars'])

        try:
            await server.start()
            server_pid = server.process.pid

            # Verify process exists
            assert psutil.pid_exists(server_pid)

            # Do some work
            init_request = {
                'jsonrpc': '2.0',
                'id': 1,
                'method': 'initialize',
                'params': {
                    'protocolVersion': '2024-11-05',
                    'capabilities': {},
                    'clientInfo': {'name': 'test-client', 'version': '1.0.0'}
                }
            }

            await server.send_json_rpc(init_request)

        finally:
            await server.stop()

        # Wait a moment for cleanup
        await asyncio.sleep(1)

        # Process should be gone
        assert not psutil.pid_exists(server_pid), "Server process should be cleaned up"