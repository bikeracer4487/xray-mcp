"""
Integration tests for performance and load scenarios.

Tests system behavior under load, large datasets, concurrent operations,
and performance optimization. Covers use cases UC-301 through UC-310.
"""

import pytest
import pytest_asyncio
import asyncio
import time
from datetime import datetime
from typing import Dict, Any, List

from src.server import create_server
from src.tools.xray_tool import XrayTool


@pytest.fixture
def unique_prefix():
    """Generate unique prefix for test names."""
    return f"PerfLoad_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


@pytest.fixture
def project_key():
    """Get project key from environment."""
    import os
    return os.getenv('XRAY_PROJECT_KEY', 'FTEST')


@pytest.mark.asyncio
class TestPerformanceAndLoad:
    """Test performance and load handling scenarios."""

    async def test_bulk_test_creation_performance(self, tool, unique_prefix, project_key):
        """
        UC-301: Handle bulk operations with large datasets.

        Tests performance of creating multiple tests in batch.
        """
        created_resources = []
        batch_size = 10  # Start with smaller batch for integration testing

        try:
            # Measure time for bulk test creation
            start_time = time.time()

            # Create tests concurrently to test bulk handling
            creation_tasks = []
            for i in range(batch_size):
                task = tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Bulk_Test_{i+1:03d}',
                    'test_type': 'Manual',
                    'priority': 'Medium',
                    'steps': [
                        {"action": f"Execute bulk test step {i+1}", "data": f"Test data {i+1}", "result": f"Expected result {i+1}"}
                    ],
                    'description': f'Bulk performance test case {i+1} of {batch_size}'
                })
                creation_tasks.append(task)

            # Execute all creation tasks
            results = await asyncio.gather(*creation_tasks, return_exceptions=True)

            creation_time = time.time() - start_time

            # Analyze results
            successful_creations = 0
            failed_creations = 0

            for result in results:
                if isinstance(result, Exception):
                    failed_creations += 1
                elif isinstance(result, dict) and result.get('success'):
                    successful_creations += 1
                    test_id = result['data']['issueId']
                    created_resources.append(('test', test_id))
                else:
                    failed_creations += 1

            # Performance assertions
            assert successful_creations > 0, "Some bulk creations should succeed"
            assert creation_time < 60.0, f"Bulk creation should complete within 60 seconds, took {creation_time:.2f}s"

            # Calculate performance metrics
            if successful_creations > 0:
                avg_time_per_test = creation_time / successful_creations
                assert avg_time_per_test < 10.0, f"Average time per test should be < 10s, was {avg_time_per_test:.2f}s"

            print(f"Bulk creation performance: {successful_creations}/{batch_size} tests created in {creation_time:.2f}s")

        finally:
            # Measure cleanup performance
            if created_resources:
                cleanup_start = time.time()

                # Clean up in batches to test bulk deletion
                cleanup_tasks = []
                for resource_type, resource_id in created_resources:
                    task = tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                    cleanup_tasks.append(task)

                # Execute cleanup concurrently
                await asyncio.gather(*cleanup_tasks, return_exceptions=True)

                cleanup_time = time.time() - cleanup_start
                print(f"Bulk cleanup performance: {len(created_resources)} tests deleted in {cleanup_time:.2f}s")

    async def test_concurrent_operations_performance(self, tool, unique_prefix, project_key):
        """
        UC-302: Manage concurrent user sessions and operations.

        Tests system behavior under concurrent load.
        """
        created_resources = []
        concurrent_operations = 5

        try:
            # First, create a test to operate on
            base_test = await tool.execute({
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Concurrent_Base_Test',
                'test_type': 'Manual'
            })

            assert base_test['success'], "Should create base test for concurrent operations"
            base_test_id = base_test['data']['issueId']
            created_resources.append(('test', base_test_id))

            # Test concurrent read operations
            start_time = time.time()

            read_tasks = []
            for i in range(concurrent_operations):
                task = tool.execute({
                    'entity': 'test',
                    'action': 'get',
                    'issue_id': base_test_id
                })
                read_tasks.append(task)

            read_results = await asyncio.gather(*read_tasks, return_exceptions=True)
            concurrent_read_time = time.time() - start_time

            # Analyze concurrent read performance
            successful_reads = sum(1 for r in read_results
                                 if isinstance(r, dict) and r.get('success'))

            assert successful_reads >= concurrent_operations // 2, \
                "At least half of concurrent reads should succeed"
            assert concurrent_read_time < 30.0, \
                f"Concurrent reads should complete within 30s, took {concurrent_read_time:.2f}s"

            # Test concurrent write operations (creating different resources)
            start_time = time.time()

            write_tasks = []
            for i in range(concurrent_operations):
                task = tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Concurrent_Write_{i+1}',
                    'test_type': 'Manual'
                })
                write_tasks.append(task)

            write_results = await asyncio.gather(*write_tasks, return_exceptions=True)
            concurrent_write_time = time.time() - start_time

            # Analyze concurrent write performance
            successful_writes = 0
            for result in write_results:
                if isinstance(result, dict) and result.get('success'):
                    successful_writes += 1
                    test_id = result['data']['issueId']
                    created_resources.append(('test', test_id))

            assert successful_writes > 0, "Some concurrent writes should succeed"
            assert concurrent_write_time < 60.0, \
                f"Concurrent writes should complete within 60s, took {concurrent_write_time:.2f}s"

            print(f"Concurrent performance: {successful_reads}/{concurrent_operations} reads in {concurrent_read_time:.2f}s, "
                  f"{successful_writes}/{concurrent_operations} writes in {concurrent_write_time:.2f}s")

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

    async def test_large_execution_batch_performance(self, tool, unique_prefix, project_key):
        """
        UC-303: Process large test execution batches.

        Tests performance when managing large test executions.
        """
        created_resources = []
        test_count = 8  # Reasonable size for integration testing

        try:
            # Create multiple tests for the execution
            test_creation_start = time.time()

            test_creation_tasks = []
            for i in range(test_count):
                task = tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Execution_Test_{i+1:02d}',
                    'test_type': 'Manual',
                    'steps': [
                        {"action": f"Execute test step {i+1}", "data": f"Test data {i+1}", "result": f"Expected result {i+1}"}
                    ]
                })
                test_creation_tasks.append(task)

            test_results = await asyncio.gather(*test_creation_tasks, return_exceptions=True)
            test_creation_time = time.time() - test_creation_start

            # Collect successful test IDs
            test_ids = []
            for result in test_results:
                if isinstance(result, dict) and result.get('success'):
                    test_id = result['data']['issueId']
                    test_ids.append(test_id)
                    created_resources.append(('test', test_id))

            assert len(test_ids) >= test_count // 2, f"Should create at least {test_count // 2} tests"

            # Create test execution
            execution_start = time.time()

            execution_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Large_Batch_Execution',
                'description': f'Performance test execution with {len(test_ids)} tests',
                'test_environments': ['Performance', 'Load']
            })

            assert execution_result['success'], "Should create test execution"
            execution_id = execution_result['data']['issueId']
            created_resources.append(('test_execution', execution_id))

            # Add all tests to execution (test bulk operations)
            add_tests_start = time.time()

            add_tests_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'add_tests',
                'issue_id': execution_id,
                'test_issue_ids': test_ids
            })

            add_tests_time = time.time() - add_tests_start
            execution_creation_time = time.time() - execution_start

            assert add_tests_result['success'], "Should add tests to execution"

            # Verify execution contains all tests
            execution_details = await tool.execute({
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': execution_id
            })

            assert execution_details['success'], "Should retrieve execution details"
            test_runs = execution_details['data']['testExecution']['testRuns']
            assert len(test_runs) == len(test_ids), f"Execution should contain {len(test_ids)} test runs"

            # Performance assertions
            assert test_creation_time < 30.0, \
                f"Test creation should complete within 30s, took {test_creation_time:.2f}s"
            assert execution_creation_time < 20.0, \
                f"Execution creation should complete within 20s, took {execution_creation_time:.2f}s"
            assert add_tests_time < 10.0, \
                f"Adding tests to execution should complete within 10s, took {add_tests_time:.2f}s"

            print(f"Large batch performance: {len(test_ids)} tests created in {test_creation_time:.2f}s, "
                  f"execution with all tests in {execution_creation_time:.2f}s")

            # Test bulk status updates performance
            status_update_start = time.time()

            status_update_tasks = []
            for i, test_id in enumerate(test_ids[:5]):  # Update first 5 tests
                task = tool.execute({
                    'entity': 'test_run',
                    'action': 'update_status',
                    'test_execution_id': execution_id,
                    'test_issue_id': test_id,
                    'status': 'PASSED' if i % 2 == 0 else 'FAILED',
                    'comment': f'Bulk performance test result {i+1}'
                })
                status_update_tasks.append(task)

            status_results = await asyncio.gather(*status_update_tasks, return_exceptions=True)
            status_update_time = time.time() - status_update_start

            successful_updates = sum(1 for r in status_results
                                   if isinstance(r, dict) and r.get('success'))

            assert successful_updates > 0, "Some status updates should succeed"
            assert status_update_time < 15.0, \
                f"Bulk status updates should complete within 15s, took {status_update_time:.2f}s"

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

    async def test_query_performance_optimization(self, tool, unique_prefix, project_key):
        """
        UC-306: Optimize query performance.

        Tests query performance with different parameters and filters.
        """
        created_resources = []

        try:
            # Create some test data for querying
            test_data_count = 5
            for i in range(test_data_count):
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Query_Test_{i+1:02d}',
                    'test_type': 'Manual',
                    'priority': 'High' if i % 2 == 0 else 'Medium'
                })

                if result['success']:
                    test_id = result['data']['issueId']
                    created_resources.append(('test', test_id))

            # Test basic list query performance
            list_start = time.time()

            list_result = await tool.execute({
                'entity': 'test',
                'action': 'list',
                'project_key': project_key,
                'limit': 50
            })

            list_time = time.time() - list_start

            assert list_result['success'], "List query should succeed"
            assert list_time < 10.0, f"List query should complete within 10s, took {list_time:.2f}s"

            # Test limited query performance
            limited_start = time.time()

            limited_result = await tool.execute({
                'entity': 'test',
                'action': 'list',
                'project_key': project_key,
                'limit': 5
            })

            limited_time = time.time() - limited_start

            assert limited_result['success'], "Limited query should succeed"
            assert limited_time < 5.0, f"Limited query should complete within 5s, took {limited_time:.2f}s"

            # Compare performance - limited query should be faster or similar
            # (though with small datasets, the difference might not be significant)
            assert limited_time <= list_time + 1.0, "Limited query should not be significantly slower"

            print(f"Query performance: list({list_time:.2f}s), limited({limited_time:.2f}s)")

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

    async def test_memory_usage_optimization(self, tool, unique_prefix, project_key):
        """
        UC-308: Manage memory usage optimization.

        Tests memory-efficient handling of operations.
        """
        created_resources = []

        try:
            # Test creating tests with varying content sizes
            content_sizes = [
                ('small', 'Small test content'),
                ('medium', 'Medium test content. ' * 50),  # ~1KB
                ('large', 'Large test content. ' * 200)    # ~4KB
            ]

            for size_name, content in content_sizes:
                start_time = time.time()

                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_Memory_{size_name.title()}_Content',
                    'test_type': 'Manual',
                    'description': content,
                    'steps': [
                        {"action": f"Test {size_name} content handling", "data": content[:100], "result": "Should handle efficiently"}
                    ]
                })

                operation_time = time.time() - start_time

                if result['success']:
                    test_id = result['data']['issueId']
                    created_resources.append(('test', test_id))

                    # Verify content was stored correctly
                    details = await tool.execute({
                        'entity': 'test',
                        'action': 'get',
                        'issue_id': test_id
                    })

                    if details['success']:
                        stored_description = details['data']['test']['jira'].get('description', '')
                        # Content should be preserved (or at least not empty)
                        assert len(stored_description) > 0, f"Content should be preserved for {size_name} test"

                # Performance should be reasonable regardless of content size
                assert operation_time < 15.0, \
                    f"{size_name.title()} content operation should complete within 15s, took {operation_time:.2f}s"

                print(f"Memory test ({size_name}): {operation_time:.2f}s")

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

    async def test_api_response_time_optimization(self, tool, unique_prefix, project_key):
        """
        UC-310: Optimize API response times.

        Tests API response time under various conditions.
        """
        # Test simple operations response time
        simple_operations = [
            ('test_list', {'entity': 'test', 'action': 'list', 'project_key': project_key, 'limit': 10}),
            ('execution_list', {'entity': 'test_execution', 'action': 'list', 'project_key': project_key, 'limit': 10}),
            ('plan_list', {'entity': 'test_plan', 'action': 'list', 'project_key': project_key, 'limit': 10})
        ]

        response_times = {}

        for operation_name, operation_params in simple_operations:
            start_time = time.time()

            result = await tool.execute(operation_params)

            response_time = time.time() - start_time
            response_times[operation_name] = response_time

            # Basic response time expectations
            assert response_time < 10.0, \
                f"{operation_name} should respond within 10s, took {response_time:.2f}s"

            if result['success']:
                # Response should contain data
                assert 'data' in result, f"{operation_name} should return data"

        # Test consecutive operations (should not degrade significantly)
        consecutive_start = time.time()

        for _ in range(3):
            await tool.execute({
                'entity': 'test',
                'action': 'list',
                'project_key': project_key,
                'limit': 5
            })

        consecutive_time = time.time() - consecutive_start

        # Consecutive operations should complete in reasonable time
        assert consecutive_time < 15.0, \
            f"Consecutive operations should complete within 15s, took {consecutive_time:.2f}s"

        print(f"API response times: {', '.join(f'{k}={v:.2f}s' for k, v in response_times.items())}")
        print(f"Consecutive operations: {consecutive_time:.2f}s")

    async def test_stress_test_scenario(self, tool, unique_prefix, project_key):
        """
        UC-305: Handle peak usage periods.

        Tests system behavior under stress conditions.
        """
        created_resources = []
        stress_operations = 8  # Moderate stress for integration testing

        try:
            # Create a mixed workload stress test
            stress_tasks = []

            # Mix of different operations to simulate real usage
            for i in range(stress_operations):
                if i % 3 == 0:
                    # Create test
                    task = tool.execute({
                        'entity': 'test',
                        'action': 'create',
                        'project_key': project_key,
                        'summary': f'{unique_prefix}_Stress_Test_{i+1}',
                        'test_type': 'Manual'
                    })
                elif i % 3 == 1:
                    # List tests
                    task = tool.execute({
                        'entity': 'test',
                        'action': 'list',
                        'project_key': project_key,
                        'limit': 5
                    })
                else:
                    # Create execution
                    task = tool.execute({
                        'entity': 'test_execution',
                        'action': 'create',
                        'project_key': project_key,
                        'summary': f'{unique_prefix}_Stress_Execution_{i+1}'
                    })

                stress_tasks.append(task)

            # Execute stress test
            stress_start = time.time()
            stress_results = await asyncio.gather(*stress_tasks, return_exceptions=True)
            stress_time = time.time() - stress_start

            # Analyze stress test results
            successful_ops = 0
            failed_ops = 0

            for i, result in enumerate(stress_results):
                if isinstance(result, Exception):
                    failed_ops += 1
                elif isinstance(result, dict) and result.get('success'):
                    successful_ops += 1

                    # Track created resources for cleanup
                    if i % 3 == 0:  # Test creation
                        test_id = result['data']['issueId']
                        created_resources.append(('test', test_id))
                    elif i % 3 == 2:  # Execution creation
                        exec_id = result['data']['issueId']
                        created_resources.append(('test_execution', exec_id))
                else:
                    failed_ops += 1

            # Stress test expectations
            assert successful_ops > 0, "Some operations should succeed under stress"
            assert stress_time < 60.0, f"Stress test should complete within 60s, took {stress_time:.2f}s"

            # Most operations should succeed (allowing for some failures under stress)
            success_rate = successful_ops / len(stress_tasks)
            assert success_rate >= 0.5, f"Success rate should be >= 50%, was {success_rate:.1%}"

            print(f"Stress test: {successful_ops}/{len(stress_tasks)} operations succeeded in {stress_time:.2f}s "
                  f"(success rate: {success_rate:.1%})")

        finally:
            # Cleanup (also tests system recovery after stress)
            if created_resources:
                cleanup_start = time.time()

                cleanup_tasks = []
                for resource_type, resource_id in created_resources:
                    task = tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                    cleanup_tasks.append(task)

                await asyncio.gather(*cleanup_tasks, return_exceptions=True)

                cleanup_time = time.time() - cleanup_start
                print(f"Post-stress cleanup: {len(created_resources)} resources cleaned in {cleanup_time:.2f}s")