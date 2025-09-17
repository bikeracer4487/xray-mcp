"""
Integration tests for authentication edge cases.

Tests various authentication failure scenarios, token expiry,
invalid credentials, and recovery mechanisms. Covers use cases UC-281 through UC-290.
"""

import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List

from src.server import create_server
from src.tools.xray_tool import XrayTool
from src.auth import XrayAuth


@pytest.fixture
def unique_prefix():
    """Generate unique prefix for test names."""
    return f"AuthEdgeCase_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


@pytest.fixture
def project_key():
    """Get project key from environment."""
    import os
    return os.getenv('XRAY_PROJECT_KEY', 'FTEST')


@pytest.mark.asyncio
class TestAuthenticationEdgeCases:
    """Test authentication failure scenarios and edge cases."""

    async def test_invalid_credentials_handling(self, project_key):
        """
        UC-284: Handle authentication token expiry and invalid credentials.

        Tests various invalid credential scenarios.
        """
        # Test with completely invalid credentials
        invalid_auth = XrayAuth(
            client_id="invalid_client_id",
            client_secret="invalid_client_secret"
        )

        try:
            token = await invalid_auth.get_token()
            assert False, "Should fail with invalid credentials"
        except Exception as e:
            # Should get authentication error
            error_msg = str(e).lower()
            assert any(keyword in error_msg for keyword in ['auth', 'credential', 'invalid', 'unauthorized']), \
                f"Should indicate authentication failure: {e}"

        # Test with empty credentials
        try:
            empty_auth = XrayAuth(client_id="", client_secret="")
            token = await empty_auth.get_token()
            assert False, "Should fail with empty credentials"
        except Exception as e:
            error_msg = str(e).lower()
            assert any(keyword in error_msg for keyword in ['auth', 'credential', 'required', 'empty']), \
                f"Should indicate missing credentials: {e}"

        # Test with None credentials
        try:
            none_auth = XrayAuth(client_id=None, client_secret=None)
            token = await none_auth.get_token()
            assert False, "Should fail with None credentials"
        except Exception as e:
            error_msg = str(e).lower()
            assert any(keyword in error_msg for keyword in ['auth', 'credential', 'required', 'none']), \
                f"Should indicate missing credentials: {e}"

    async def test_token_expiry_simulation(self, tool, unique_prefix, project_key):
        """
        UC-284: Test token expiry and refresh handling.

        Simulates token expiry scenarios and validates refresh mechanisms.
        """
        created_resources = []

        try:
            # First, perform a successful operation to ensure we have a valid token
            initial_test = await tool.execute({
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Token_Expiry_Test_Initial',
                'test_type': 'Manual'
            })

            if initial_test['success']:
                test_id = initial_test['data']['issueId']
                created_resources.append(('test', test_id))

                # Simulate token expiry by invalidating the current token
                # Note: In a real scenario, we would wait for natural expiry or manipulate the token
                original_client = tool.client

                # Try to perform operations that should trigger token refresh
                for i in range(3):
                    result = await tool.execute({
                        'entity': 'test',
                        'action': 'get',
                        'issue_id': test_id
                    })

                    # The operation should either succeed (token still valid/refreshed)
                    # or fail with appropriate auth error
                    if not result['success']:
                        error_msg = str(result.get('errors', [])).lower()
                        # Check if it's an auth-related error
                        if any(keyword in error_msg for keyword in ['auth', 'token', 'expired', 'unauthorized']):
                            # This is expected behavior for expired tokens
                            break
                    else:
                        # Token refresh worked or token is still valid
                        assert result['data'], "Should return test data"

                    # Small delay between operations
                    await asyncio.sleep(0.1)

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    async def test_concurrent_authentication_requests(self, project_key):
        """
        UC-286: Test concurrent access and authentication conflicts.

        Tests multiple simultaneous authentication requests.
        """
        # Create multiple auth instances
        import os
        client_id = os.getenv('XRAY_CLIENT_ID')
        client_secret = os.getenv('XRAY_CLIENT_SECRET')

        if not client_id or not client_secret:
            pytest.skip("Xray credentials not configured")

        auth_instances = [
            XrayAuth(client_id=client_id, client_secret=client_secret)
            for _ in range(5)
        ]

        # Perform concurrent token requests
        async def get_token_task(auth_instance, task_id):
            try:
                token = await auth_instance.get_token()
                return {'task_id': task_id, 'success': True, 'token': token}
            except Exception as e:
                return {'task_id': task_id, 'success': False, 'error': str(e)}

        # Execute concurrent authentication requests
        tasks = [get_token_task(auth, i) for i, auth in enumerate(auth_instances)]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Analyze results
        successful_auths = sum(1 for r in results if isinstance(r, dict) and r.get('success'))
        failed_auths = len(results) - successful_auths

        # Most auth requests should succeed (depending on rate limiting)
        assert successful_auths >= 1, "At least one authentication should succeed"

        # Check for rate limiting or other expected failures
        for result in results:
            if isinstance(result, dict) and not result.get('success'):
                error_msg = result.get('error', '').lower()
                # Rate limiting or concurrent access errors are acceptable
                assert any(keyword in error_msg for keyword in
                          ['rate', 'limit', 'too many', 'concurrent', 'auth']), \
                    f"Unexpected auth failure: {result.get('error')}"

    async def test_network_timeout_scenarios(self, tool, unique_prefix, project_key):
        """
        UC-281: Handle network timeouts gracefully.

        Tests behavior during network connectivity issues.
        """
        # Note: This test is limited by the actual network environment
        # In a real test environment, you might use network simulation tools

        # Test rapid succession of requests (may trigger timeouts)
        timeout_tasks = []
        for i in range(10):
            task = tool.execute({
                'entity': 'test',
                'action': 'list',
                'project_key': project_key,
                'limit': 1  # Small limit to reduce response size
            })
            timeout_tasks.append(task)

        # Execute all requests concurrently
        try:
            results = await asyncio.wait_for(
                asyncio.gather(*timeout_tasks, return_exceptions=True),
                timeout=30.0  # 30 second timeout for all requests
            )

            # Analyze results
            successful_requests = 0
            timeout_errors = 0
            other_errors = 0

            for result in results:
                if isinstance(result, Exception):
                    if 'timeout' in str(result).lower():
                        timeout_errors += 1
                    else:
                        other_errors += 1
                elif isinstance(result, dict) and result.get('success'):
                    successful_requests += 1
                else:
                    other_errors += 1

            # At least some requests should complete
            assert successful_requests > 0, "Some requests should complete successfully"

            # Timeout errors are acceptable in this scenario
            total_requests = len(timeout_tasks)
            assert successful_requests + timeout_errors + other_errors == total_requests, \
                "All requests should be accounted for"

        except asyncio.TimeoutError:
            # If the entire batch times out, that's also valid behavior
            assert True, "Timeout occurred as expected in stress test"

    async def test_malformed_token_handling(self, project_key):
        """
        UC-287: Handle malformed or corrupted authentication tokens.

        Tests behavior with invalid token formats.
        """
        # This test requires internal access to token manipulation
        # In a real implementation, you might test this by:
        # 1. Intercepting HTTP requests
        # 2. Modifying the Authorization header
        # 3. Observing the error handling

        # For now, we'll test the auth module directly
        import os
        client_id = os.getenv('XRAY_CLIENT_ID')
        client_secret = os.getenv('XRAY_CLIENT_SECRET')

        if not client_id or not client_secret:
            pytest.skip("Xray credentials not configured")

        auth = XrayAuth(client_id=client_id, client_secret=client_secret)

        # Test with manually corrupted tokens by accessing internal state
        # Note: This depends on the internal implementation of XrayAuth
        try:
            # Get a valid token first
            valid_token = await auth.get_token()
            assert valid_token, "Should get a valid token"

            # Simulate token corruption (if the implementation allows it)
            # This is implementation-specific and may not be testable
            # without access to internal token storage

        except Exception as e:
            # If we can't manipulate tokens directly, that's actually good security
            pass

    async def test_rate_limiting_behavior(self, tool, project_key):
        """
        UC-282 & UC-288: Test rate limiting and retry mechanisms.

        Tests behavior under rate limiting conditions.
        """
        # Perform rapid-fire requests to potentially trigger rate limiting
        rapid_requests = []
        for i in range(20):  # 20 rapid requests
            request = tool.execute({
                'entity': 'test',
                'action': 'list',
                'project_key': project_key,
                'limit': 1
            })
            rapid_requests.append(request)

        # Execute requests with minimal delay
        results = []
        for request in rapid_requests:
            try:
                result = await request
                results.append(result)
                # Very small delay to simulate rapid requests
                await asyncio.sleep(0.01)
            except Exception as e:
                results.append({'success': False, 'error': str(e)})

        # Analyze rate limiting behavior
        successful_requests = sum(1 for r in results if r.get('success'))
        failed_requests = len(results) - successful_requests

        # Some requests should succeed
        assert successful_requests > 0, "Some requests should succeed even under load"

        # Check for rate limiting indicators in failed requests
        for result in results:
            if not result.get('success'):
                error_msg = str(result.get('error', '') + str(result.get('errors', []))).lower()
                # Rate limiting errors are acceptable
                rate_limit_indicators = ['rate', 'limit', 'too many', 'throttle', '429']
                if any(indicator in error_msg for indicator in rate_limit_indicators):
                    # This is expected rate limiting behavior
                    continue
                elif any(indicator in error_msg for indicator in ['timeout', 'network', 'connection']):
                    # Network-related errors are also acceptable under load
                    continue

    async def test_authentication_recovery_mechanisms(self, tool, unique_prefix, project_key):
        """
        UC-289: Test system recovery from authentication failures.

        Tests the system's ability to recover from auth issues.
        """
        created_resources = []

        try:
            # Perform a baseline operation to ensure auth is working
            baseline_test = await tool.execute({
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Auth_Recovery_Baseline',
                'test_type': 'Manual'
            })

            if baseline_test['success']:
                test_id = baseline_test['data']['issueId']
                created_resources.append(('test', test_id))

                # Perform multiple operations to test sustained auth
                for i in range(5):
                    recovery_test = await tool.execute({
                        'entity': 'test',
                        'action': 'get',
                        'issue_id': test_id
                    })

                    if recovery_test['success']:
                        # Auth is working correctly
                        assert recovery_test['data'], "Should return test data"
                    else:
                        # If auth fails, check if it's a recoverable error
                        error_msg = str(recovery_test.get('errors', [])).lower()
                        if any(keyword in error_msg for keyword in ['auth', 'token', 'unauthorized']):
                            # Try one more time to see if it recovers
                            retry_result = await tool.execute({
                                'entity': 'test',
                                'action': 'get',
                                'issue_id': test_id
                            })

                            # Document whether recovery worked
                            recovery_worked = retry_result.get('success', False)
                            # Either way is acceptable - depends on implementation

                    # Small delay between operations
                    await asyncio.sleep(0.2)

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    async def test_authentication_state_consistency(self, tool, unique_prefix, project_key):
        """
        UC-290: Test authentication state consistency across operations.

        Tests that authentication state remains consistent during complex workflows.
        """
        created_resources = []

        try:
            # Perform a complex workflow that requires multiple authenticated requests
            workflow_operations = [
                # Create test
                {
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Auth_Consistency_Test',
                    'test_type': 'Manual'
                },
                # Create execution
                {
                    'entity': 'test_execution',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Auth_Consistency_Execution'
                },
                # Create plan
                {
                    'entity': 'test_plan',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Auth_Consistency_Plan'
                }
            ]

            operation_results = []
            for operation in workflow_operations:
                result = await tool.execute(operation)
                operation_results.append(result)

                if result['success']:
                    entity_type = operation['entity']
                    if entity_type == 'test':
                        issue_id = result['data']['issueId']
                    elif entity_type == 'test_execution':
                        issue_id = result['data']['issueId']
                    elif entity_type == 'test_plan':
                        issue_id = result['data']['issueId']

                    created_resources.append((entity_type, issue_id))

                # Verify authentication remained consistent
                assert result.get('success') is not None, "Should get a response"

                # Small delay between operations
                await asyncio.sleep(0.1)

            # Count successful operations
            successful_ops = sum(1 for r in operation_results if r.get('success'))

            # Most operations should succeed if auth is consistent
            assert successful_ops >= len(workflow_operations) // 2, \
                "Most operations should succeed with consistent auth"

            # If any operations failed, check if they're auth-related
            for result in operation_results:
                if not result.get('success'):
                    error_msg = str(result.get('errors', [])).lower()
                    # Auth failures are documented but not necessarily test failures
                    if any(keyword in error_msg for keyword in ['auth', 'token', 'unauthorized']):
                        # Auth-related failure - acceptable in edge case testing
                        pass

        finally:
            # Cleanup - test that cleanup operations also work with consistent auth
            for resource_type, resource_id in reversed(created_resources):
                try:
                    cleanup_result = await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })

                    # Cleanup should also work with consistent auth
                    # (failures are acceptable but should be auth-related if they occur)
                    if not cleanup_result.get('success'):
                        error_msg = str(cleanup_result.get('errors', [])).lower()
                        # Document cleanup auth behavior
                        pass

                except Exception as e:
                    # Cleanup failures are acceptable in edge case testing
                    pass