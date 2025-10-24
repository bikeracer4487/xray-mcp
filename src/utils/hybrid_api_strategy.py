"""Hybrid API strategy combining GraphQL and REST APIs with reconciliation for indexing delay mitigation."""

import asyncio
import aiohttp
import json
from typing import Any, Dict, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass
from ..config import config


class APIType(Enum):
    """Types of APIs available."""
    GRAPHQL = "graphql"
    REST = "rest"


class ReconciliationStrategy(Enum):
    """Different reconciliation strategies."""
    GRAPHQL_PRIMARY = "graphql_primary"  # Try GraphQL first, REST as fallback
    REST_PRIMARY = "rest_primary"        # Try REST first, GraphQL as fallback
    PARALLEL = "parallel"                # Try both simultaneously, use fastest
    CROSS_VERIFY = "cross_verify"        # Execute on both, verify consistency


@dataclass
class HybridResult:
    """Result from hybrid API operation."""
    success: bool
    data: Any = None
    primary_api: Optional[APIType] = None
    fallback_used: bool = False
    reconciliation_successful: bool = True
    errors: List[str] = None
    warnings: List[str] = None
    execution_time_ms: float = 0.0

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
        if self.warnings is None:
            self.warnings = []


class HybridAPIClient:
    """Hybrid client that can use both GraphQL and REST APIs with intelligent fallback."""

    def __init__(self, graphql_client, auth_client):
        """Initialize with existing GraphQL and auth clients."""
        self.graphql_client = graphql_client
        self.auth = auth_client
        self.rest_base_url = self._get_rest_base_url()

    def _get_rest_base_url(self) -> str:
        """Convert GraphQL URL to REST API base URL."""
        # Convert xray.cloud.getxray.app to jira.getxray.app for JIRA REST API
        base_url = self.auth.base_url.replace('xray.cloud.getxray.app', 'jira.getxray.app')
        return base_url

    async def _execute_rest_request(
        self,
        method: str,
        endpoint: str,
        payload: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, str]] = None
    ) -> Dict[str, Any]:
        """Execute a REST API request."""
        token = await self.auth.authenticate()
        url = f"{self.rest_base_url}/{endpoint.lstrip('/')}"

        headers = {
            'Authorization': f'Bearer {token}',
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        async with aiohttp.ClientSession() as session:
            kwargs = {
                'headers': headers,
                'params': params or {}
            }

            if payload and method.upper() in ['POST', 'PUT', 'PATCH']:
                kwargs['data'] = json.dumps(payload)

            async with session.request(method, url, **kwargs) as response:
                if response.status in [200, 201, 204]:
                    if response.status == 204:  # No content
                        return {'success': True}
                    return await response.json()
                else:
                    error_text = await response.text()
                    raise Exception(f"REST API error: HTTP {response.status} - {error_text}")

    async def get_issue_via_rest(self, issue_id: str) -> Dict[str, Any]:
        """Get issue details via REST API (may have different indexing than GraphQL)."""
        try:
            endpoint = f"rest/api/3/issue/{issue_id}"
            result = await self._execute_rest_request('GET', endpoint)

            # Transform REST response to match GraphQL structure
            return {
                'issueId': issue_id,
                'key': result.get('key'),
                'summary': result['fields'].get('summary'),
                'description': result['fields'].get('description'),
                'issueType': result['fields']['issuetype'].get('name'),
                'status': result['fields']['status'].get('name'),
                'created': result['fields'].get('created'),
                'updated': result['fields'].get('updated'),
                'source': 'rest'
            }
        except Exception as e:
            raise Exception(f"REST API get issue failed: {str(e)}")

    async def update_issue_via_rest(
        self,
        issue_id: str,
        fields: Dict[str, Any],
        reconcile_immediately: bool = True
    ) -> Dict[str, Any]:
        """Update issue via REST API with optional immediate reconciliation."""
        try:
            endpoint = f"rest/api/3/issue/{issue_id}"
            payload = {'fields': fields}

            # Add reconcileIssues parameter to force immediate indexing
            params = {}
            if reconcile_immediately:
                params['reconcileIssues'] = 'true'

            await self._execute_rest_request('PUT', endpoint, payload, params)

            return {
                'issueId': issue_id,
                'updated_fields': fields,
                'reconciled': reconcile_immediately,
                'source': 'rest'
            }
        except Exception as e:
            raise Exception(f"REST API update failed: {str(e)}")

    async def search_issues_via_rest(
        self,
        jql: str,
        start_at: int = 0,
        max_results: int = 50,
        fields: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Search issues via REST API (may return different results due to indexing)."""
        try:
            endpoint = "rest/api/3/search"
            params = {
                'jql': jql,
                'startAt': str(start_at),
                'maxResults': str(max_results),
                'fields': ','.join(fields or ['key', 'summary', 'issuetype', 'created'])
            }

            result = await self._execute_rest_request('GET', endpoint, params=params)

            # Transform to match GraphQL structure
            return {
                'total': result.get('total', 0),
                'start': result.get('startAt', 0),
                'limit': result.get('maxResults', max_results),
                'results': [
                    {
                        'issueId': issue.get('id'),
                        'key': issue.get('key'),
                        'summary': issue['fields'].get('summary'),
                        'issueType': issue['fields']['issuetype'].get('name'),
                        'created': issue['fields'].get('created')
                    }
                    for issue in result.get('issues', [])
                ],
                'source': 'rest'
            }
        except Exception as e:
            raise Exception(f"REST API search failed: {str(e)}")

    async def execute_with_strategy(
        self,
        operation_name: str,
        graphql_operation: Optional[callable] = None,
        rest_operation: Optional[callable] = None,
        strategy: ReconciliationStrategy = ReconciliationStrategy.GRAPHQL_PRIMARY,
        timeout_seconds: int = 30
    ) -> HybridResult:
        """Execute operation using specified reconciliation strategy."""
        import time
        start_time = time.time()

        try:
            if strategy == ReconciliationStrategy.GRAPHQL_PRIMARY:
                return await self._execute_graphql_primary(
                    graphql_operation, rest_operation, operation_name, start_time
                )
            elif strategy == ReconciliationStrategy.REST_PRIMARY:
                return await self._execute_rest_primary(
                    rest_operation, graphql_operation, operation_name, start_time
                )
            elif strategy == ReconciliationStrategy.PARALLEL:
                return await self._execute_parallel(
                    graphql_operation, rest_operation, operation_name, start_time, timeout_seconds
                )
            elif strategy == ReconciliationStrategy.CROSS_VERIFY:
                return await self._execute_cross_verify(
                    graphql_operation, rest_operation, operation_name, start_time
                )
            else:
                raise ValueError(f"Unknown reconciliation strategy: {strategy}")

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return HybridResult(
                success=False,
                errors=[f"Hybrid operation failed: {str(e)}"],
                execution_time_ms=execution_time
            )

    async def _execute_graphql_primary(
        self, graphql_op, rest_op, operation_name, start_time
    ) -> HybridResult:
        """Execute GraphQL first, REST as fallback."""
        try:
            if graphql_op:
                result = await graphql_op()
                execution_time = (time.time() - start_time) * 1000
                return HybridResult(
                    success=True,
                    data=result,
                    primary_api=APIType.GRAPHQL,
                    fallback_used=False,
                    execution_time_ms=execution_time
                )
        except Exception as graphql_error:
            # Try REST as fallback
            if rest_op:
                try:
                    result = await rest_op()
                    execution_time = (time.time() - start_time) * 1000
                    return HybridResult(
                        success=True,
                        data=result,
                        primary_api=APIType.REST,
                        fallback_used=True,
                        warnings=[f"GraphQL failed, used REST fallback: {str(graphql_error)}"],
                        execution_time_ms=execution_time
                    )
                except Exception as rest_error:
                    execution_time = (time.time() - start_time) * 1000
                    return HybridResult(
                        success=False,
                        errors=[
                            f"GraphQL error: {str(graphql_error)}",
                            f"REST fallback error: {str(rest_error)}"
                        ],
                        execution_time_ms=execution_time
                    )

        execution_time = (time.time() - start_time) * 1000
        return HybridResult(
            success=False,
            errors=["No operations provided"],
            execution_time_ms=execution_time
        )

    async def _execute_rest_primary(
        self, rest_op, graphql_op, operation_name, start_time
    ) -> HybridResult:
        """Execute REST first, GraphQL as fallback."""
        try:
            if rest_op:
                result = await rest_op()
                execution_time = (time.time() - start_time) * 1000
                return HybridResult(
                    success=True,
                    data=result,
                    primary_api=APIType.REST,
                    fallback_used=False,
                    execution_time_ms=execution_time
                )
        except Exception as rest_error:
            # Try GraphQL as fallback
            if graphql_op:
                try:
                    result = await graphql_op()
                    execution_time = (time.time() - start_time) * 1000
                    return HybridResult(
                        success=True,
                        data=result,
                        primary_api=APIType.GRAPHQL,
                        fallback_used=True,
                        warnings=[f"REST failed, used GraphQL fallback: {str(rest_error)}"],
                        execution_time_ms=execution_time
                    )
                except Exception as graphql_error:
                    execution_time = (time.time() - start_time) * 1000
                    return HybridResult(
                        success=False,
                        errors=[
                            f"REST error: {str(rest_error)}",
                            f"GraphQL fallback error: {str(graphql_error)}"
                        ],
                        execution_time_ms=execution_time
                    )

        execution_time = (time.time() - start_time) * 1000
        return HybridResult(
            success=False,
            errors=["No operations provided"],
            execution_time_ms=execution_time
        )

    async def _execute_parallel(
        self, graphql_op, rest_op, operation_name, start_time, timeout_seconds
    ) -> HybridResult:
        """Execute both APIs in parallel, return fastest successful result."""
        if not graphql_op or not rest_op:
            return HybridResult(
                success=False,
                errors=["Parallel execution requires both GraphQL and REST operations"],
                execution_time_ms=(time.time() - start_time) * 1000
            )

        try:
            # Execute both operations concurrently
            done, pending = await asyncio.wait(
                [
                    asyncio.create_task(graphql_op()),
                    asyncio.create_task(rest_op())
                ],
                timeout=timeout_seconds,
                return_when=asyncio.FIRST_COMPLETED
            )

            # Cancel pending tasks
            for task in pending:
                task.cancel()

            if done:
                # Get the first completed task
                completed_task = next(iter(done))
                result = await completed_task

                execution_time = (time.time() - start_time) * 1000
                return HybridResult(
                    success=True,
                    data=result,
                    primary_api=APIType.GRAPHQL,  # We don't know which completed first
                    fallback_used=False,
                    warnings=["Used fastest responding API"],
                    execution_time_ms=execution_time
                )
            else:
                execution_time = (time.time() - start_time) * 1000
                return HybridResult(
                    success=False,
                    errors=["Both operations timed out"],
                    execution_time_ms=execution_time
                )

        except Exception as e:
            execution_time = (time.time() - start_time) * 1000
            return HybridResult(
                success=False,
                errors=[f"Parallel execution failed: {str(e)}"],
                execution_time_ms=execution_time
            )

    async def _execute_cross_verify(
        self, graphql_op, rest_op, operation_name, start_time
    ) -> HybridResult:
        """Execute both APIs and verify consistency."""
        if not graphql_op or not rest_op:
            return HybridResult(
                success=False,
                errors=["Cross verification requires both GraphQL and REST operations"],
                execution_time_ms=(time.time() - start_time) * 1000
            )

        graphql_result = None
        rest_result = None
        graphql_error = None
        rest_error = None

        # Execute GraphQL
        try:
            graphql_result = await graphql_op()
        except Exception as e:
            graphql_error = str(e)

        # Execute REST
        try:
            rest_result = await rest_op()
        except Exception as e:
            rest_error = str(e)

        execution_time = (time.time() - start_time) * 1000

        # Analyze results
        if graphql_result and rest_result:
            # Both succeeded - verify consistency
            consistent = self._verify_consistency(graphql_result, rest_result)
            warnings = [] if consistent else ["GraphQL and REST results are inconsistent"]

            return HybridResult(
                success=True,
                data=graphql_result,  # Prefer GraphQL result
                primary_api=APIType.GRAPHQL,
                reconciliation_successful=consistent,
                warnings=warnings,
                execution_time_ms=execution_time
            )
        elif graphql_result:
            # Only GraphQL succeeded
            return HybridResult(
                success=True,
                data=graphql_result,
                primary_api=APIType.GRAPHQL,
                reconciliation_successful=False,
                warnings=[f"REST verification failed: {rest_error}"],
                execution_time_ms=execution_time
            )
        elif rest_result:
            # Only REST succeeded
            return HybridResult(
                success=True,
                data=rest_result,
                primary_api=APIType.REST,
                reconciliation_successful=False,
                warnings=[f"GraphQL verification failed: {graphql_error}"],
                execution_time_ms=execution_time
            )
        else:
            # Both failed
            return HybridResult(
                success=False,
                errors=[
                    f"GraphQL error: {graphql_error}",
                    f"REST error: {rest_error}"
                ],
                reconciliation_successful=False,
                execution_time_ms=execution_time
            )

    def _verify_consistency(self, graphql_result: Any, rest_result: Any) -> bool:
        """Verify consistency between GraphQL and REST results."""
        # Basic consistency check - this can be enhanced based on specific needs
        if isinstance(graphql_result, dict) and isinstance(rest_result, dict):
            # Check key fields for consistency
            graphql_id = graphql_result.get('issueId') or graphql_result.get('id')
            rest_id = rest_result.get('issueId') or rest_result.get('id')

            if graphql_id and rest_id:
                return str(graphql_id) == str(rest_id)

        # Default to consistent if we can't determine
        return True


# Convenience functions for common hybrid patterns
async def get_with_hybrid_fallback(
    hybrid_client: HybridAPIClient,
    issue_id: str,
    graphql_getter: callable,
    use_rest_reconciliation: bool = True
) -> HybridResult:
    """Get entity with hybrid fallback and optional REST reconciliation."""

    async def rest_operation():
        return await hybrid_client.get_issue_via_rest(issue_id)

    strategy = ReconciliationStrategy.CROSS_VERIFY if use_rest_reconciliation else ReconciliationStrategy.GRAPHQL_PRIMARY

    return await hybrid_client.execute_with_strategy(
        f"get_{issue_id}",
        graphql_getter,
        rest_operation,
        strategy
    )


async def create_with_immediate_verification(
    hybrid_client: HybridAPIClient,
    graphql_creator: callable,
    created_issue_id: str,
    graphql_getter: callable
) -> HybridResult:
    """Create entity and immediately verify via REST to bypass indexing delays."""

    # Execute creation
    create_result = await hybrid_client.execute_with_strategy(
        "create_operation",
        graphql_creator,
        None,
        ReconciliationStrategy.GRAPHQL_PRIMARY
    )

    if not create_result.success:
        return create_result

    # Immediately verify via REST API (may have different indexing)
    async def rest_verification():
        return await hybrid_client.get_issue_via_rest(created_issue_id)

    verify_result = await hybrid_client.execute_with_strategy(
        "verification",
        graphql_getter,
        rest_verification,
        ReconciliationStrategy.REST_PRIMARY  # Try REST first for immediate verification
    )

    # Combine results
    return HybridResult(
        success=verify_result.success,
        data={
            'creation': create_result.data,
            'verification': verify_result.data
        },
        primary_api=create_result.primary_api,
        fallback_used=create_result.fallback_used or verify_result.fallback_used,
        reconciliation_successful=verify_result.success,
        warnings=create_result.warnings + verify_result.warnings,
        execution_time_ms=create_result.execution_time_ms + verify_result.execution_time_ms
    )