"""Async workflow processor for handling complex operations with indexing delays."""

import asyncio
import uuid
import time
from typing import Any, Callable, Dict, List, Optional, Union, Tuple
from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime, timedelta
import json


class WorkflowStatus(Enum):
    """Status of a workflow execution."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    WAITING_FOR_INDEX = "waiting_for_index"


class StepStatus(Enum):
    """Status of individual workflow steps."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"
    RETRYING = "retrying"


@dataclass
class WorkflowStep:
    """Individual step in a workflow."""
    step_id: str
    name: str
    operation: Callable
    depends_on: List[str] = field(default_factory=list)
    retry_config: Optional[Dict[str, Any]] = None
    timeout_seconds: int = 300
    expected_indexing_delay: bool = False
    status: StepStatus = StepStatus.PENDING
    result: Any = None
    error: Optional[str] = None
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    execution_time_ms: float = 0.0


@dataclass
class WorkflowExecution:
    """Represents a workflow execution instance."""
    workflow_id: str
    name: str
    steps: List[WorkflowStep]
    status: WorkflowStatus = WorkflowStatus.PENDING
    created_at: datetime = field(default_factory=datetime.now)
    started_at: Optional[datetime] = None
    completed_at: Optional[datetime] = None
    total_execution_time_ms: float = 0.0
    results: Dict[str, Any] = field(default_factory=dict)
    errors: List[str] = field(default_factory=list)
    progress_percentage: float = 0.0


class AsyncWorkflowProcessor:
    """Processes complex workflows asynchronously with indexing delay handling."""

    def __init__(self):
        """Initialize the workflow processor."""
        self.active_workflows: Dict[str, WorkflowExecution] = {}
        self.completed_workflows: Dict[str, WorkflowExecution] = {}
        self.background_tasks: Dict[str, asyncio.Task] = {}

    def create_workflow(
        self,
        name: str,
        steps: List[WorkflowStep],
        workflow_id: Optional[str] = None
    ) -> str:
        """Create a new workflow and return its ID."""
        if workflow_id is None:
            workflow_id = f"wf_{uuid.uuid4().hex[:8]}"

        workflow = WorkflowExecution(
            workflow_id=workflow_id,
            name=name,
            steps=steps
        )

        self.active_workflows[workflow_id] = workflow
        return workflow_id

    async def execute_workflow(
        self,
        workflow_id: str,
        run_in_background: bool = False
    ) -> Union[WorkflowExecution, str]:
        """Execute a workflow either synchronously or in background."""
        if workflow_id not in self.active_workflows:
            raise ValueError(f"Workflow {workflow_id} not found")

        if run_in_background:
            # Start background task
            task = asyncio.create_task(self._execute_workflow_internal(workflow_id))
            self.background_tasks[workflow_id] = task
            return workflow_id
        else:
            # Execute synchronously
            return await self._execute_workflow_internal(workflow_id)

    async def _execute_workflow_internal(self, workflow_id: str) -> WorkflowExecution:
        """Internal workflow execution logic."""
        workflow = self.active_workflows[workflow_id]
        workflow.status = WorkflowStatus.RUNNING
        workflow.started_at = datetime.now()

        try:
            await self._execute_steps(workflow)

            # Check overall status
            if all(step.status == StepStatus.COMPLETED for step in workflow.steps):
                workflow.status = WorkflowStatus.COMPLETED
            elif any(step.status == StepStatus.FAILED for step in workflow.steps):
                workflow.status = WorkflowStatus.FAILED
            else:
                workflow.status = WorkflowStatus.WAITING_FOR_INDEX

        except Exception as e:
            workflow.status = WorkflowStatus.FAILED
            workflow.errors.append(f"Workflow execution failed: {str(e)}")

        finally:
            workflow.completed_at = datetime.now()
            if workflow.started_at:
                workflow.total_execution_time_ms = (
                    workflow.completed_at - workflow.started_at
                ).total_seconds() * 1000

            # Move to completed workflows
            self.completed_workflows[workflow_id] = workflow
            if workflow_id in self.active_workflows:
                del self.active_workflows[workflow_id]
            if workflow_id in self.background_tasks:
                del self.background_tasks[workflow_id]

        return workflow

    async def _execute_steps(self, workflow: WorkflowExecution):
        """Execute workflow steps respecting dependencies and handling indexing delays."""
        completed_steps = set()
        remaining_steps = {step.step_id: step for step in workflow.steps}

        while remaining_steps:
            # Find steps that can be executed (dependencies satisfied)
            ready_steps = []
            for step_id, step in remaining_steps.items():
                if all(dep in completed_steps for dep in step.depends_on):
                    ready_steps.append(step)

            if not ready_steps:
                # Check if we're waiting for indexing
                if any(step.status == StepStatus.RETRYING for step in remaining_steps.values()):
                    workflow.status = WorkflowStatus.WAITING_FOR_INDEX
                    await asyncio.sleep(2)  # Wait before checking again
                    continue
                else:
                    # Deadlock - dependencies can't be satisfied
                    workflow.errors.append("Workflow deadlock: unresolved dependencies")
                    break

            # Execute ready steps (potentially in parallel)
            tasks = []
            for step in ready_steps:
                tasks.append(self._execute_step(step, workflow))

            # Wait for all ready steps to complete
            await asyncio.gather(*tasks, return_exceptions=True)

            # Update completed steps
            for step in ready_steps:
                if step.status == StepStatus.COMPLETED:
                    completed_steps.add(step.step_id)
                    remaining_steps.pop(step.step_id, None)
                elif step.status == StepStatus.FAILED:
                    remaining_steps.pop(step.step_id, None)
                # If still retrying, keep in remaining_steps

            # Update progress
            total_steps = len(workflow.steps)
            completed_count = len(completed_steps)
            workflow.progress_percentage = (completed_count / total_steps) * 100

    async def _execute_step(self, step: WorkflowStep, workflow: WorkflowExecution):
        """Execute an individual workflow step with retry logic."""
        step.status = StepStatus.RUNNING
        step.started_at = datetime.now()

        max_retries = 3
        if step.expected_indexing_delay:
            max_retries = 6  # More retries for indexing delay scenarios

        for attempt in range(max_retries + 1):
            try:
                if attempt > 0:
                    step.status = StepStatus.RETRYING
                    # Exponential backoff with indexing delay consideration
                    delay = 2 ** attempt
                    if step.expected_indexing_delay:
                        delay *= 2  # Longer delays for indexing issues
                    await asyncio.sleep(min(delay, 60))  # Max 60 seconds

                # Execute the step operation
                step.result = await asyncio.wait_for(
                    step.operation(),
                    timeout=step.timeout_seconds
                )

                step.status = StepStatus.COMPLETED
                break

            except asyncio.TimeoutError:
                error_msg = f"Step {step.name} timed out after {step.timeout_seconds} seconds"
                step.error = error_msg
                if attempt == max_retries:
                    step.status = StepStatus.FAILED
                    workflow.errors.append(error_msg)

            except Exception as e:
                error_msg = f"Step {step.name} failed: {str(e)}"
                step.error = error_msg

                # Check if it's an indexing delay issue
                if any(keyword in str(e).lower() for keyword in ['not found', 'indexing', 'not available']):
                    if attempt < max_retries:
                        continue  # Retry for indexing delays

                step.status = StepStatus.FAILED
                workflow.errors.append(error_msg)
                break

        if step.started_at:
            step.completed_at = datetime.now()
            step.execution_time_ms = (
                step.completed_at - step.started_at
            ).total_seconds() * 1000

        # Store step result in workflow results
        workflow.results[step.step_id] = {
            'status': step.status.value,
            'result': step.result,
            'error': step.error,
            'execution_time_ms': step.execution_time_ms
        }

    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get current status of a workflow."""
        workflow = None
        if workflow_id in self.active_workflows:
            workflow = self.active_workflows[workflow_id]
        elif workflow_id in self.completed_workflows:
            workflow = self.completed_workflows[workflow_id]

        if not workflow:
            return None

        return {
            'workflow_id': workflow.workflow_id,
            'name': workflow.name,
            'status': workflow.status.value,
            'progress_percentage': workflow.progress_percentage,
            'created_at': workflow.created_at.isoformat(),
            'started_at': workflow.started_at.isoformat() if workflow.started_at else None,
            'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None,
            'total_execution_time_ms': workflow.total_execution_time_ms,
            'steps': [
                {
                    'step_id': step.step_id,
                    'name': step.name,
                    'status': step.status.value,
                    'execution_time_ms': step.execution_time_ms,
                    'error': step.error
                }
                for step in workflow.steps
            ],
            'errors': workflow.errors,
            'results': workflow.results
        }

    async def cancel_workflow(self, workflow_id: str) -> bool:
        """Cancel a running workflow."""
        if workflow_id in self.background_tasks:
            task = self.background_tasks[workflow_id]
            task.cancel()

            if workflow_id in self.active_workflows:
                workflow = self.active_workflows[workflow_id]
                workflow.status = WorkflowStatus.CANCELLED
                workflow.completed_at = datetime.now()

            return True
        return False

    def list_workflows(self, include_completed: bool = False) -> List[Dict[str, Any]]:
        """List all workflows with their current status."""
        workflows = []

        # Active workflows
        for workflow in self.active_workflows.values():
            workflows.append({
                'workflow_id': workflow.workflow_id,
                'name': workflow.name,
                'status': workflow.status.value,
                'progress_percentage': workflow.progress_percentage,
                'created_at': workflow.created_at.isoformat()
            })

        # Completed workflows if requested
        if include_completed:
            for workflow in self.completed_workflows.values():
                workflows.append({
                    'workflow_id': workflow.workflow_id,
                    'name': workflow.name,
                    'status': workflow.status.value,
                    'progress_percentage': workflow.progress_percentage,
                    'created_at': workflow.created_at.isoformat(),
                    'completed_at': workflow.completed_at.isoformat() if workflow.completed_at else None
                })

        return workflows


# Global workflow processor instance
workflow_processor = AsyncWorkflowProcessor()


# Convenience functions for common workflow patterns
def create_create_then_validate_workflow(
    name: str,
    create_operation: Callable,
    validate_operation: Callable,
    entity_name: str = "entity"
) -> str:
    """Create a workflow for create-then-validate pattern with indexing delay handling."""

    steps = [
        WorkflowStep(
            step_id="create",
            name=f"Create {entity_name}",
            operation=create_operation,
            expected_indexing_delay=False
        ),
        WorkflowStep(
            step_id="validate",
            name=f"Validate {entity_name}",
            operation=validate_operation,
            depends_on=["create"],
            expected_indexing_delay=True,  # Validation may encounter indexing delays
            timeout_seconds=600  # Longer timeout for validation
        )
    ]

    return workflow_processor.create_workflow(name, steps)


def create_bulk_operation_workflow(
    name: str,
    operations: List[Tuple[str, Callable]],
    batch_size: int = 5
) -> str:
    """Create a workflow for bulk operations with controlled concurrency."""

    steps = []
    for i, (op_name, operation) in enumerate(operations):
        # Create dependency on previous batch
        depends_on = []
        if i >= batch_size:
            depends_on = [f"op_{i - batch_size}"]

        steps.append(WorkflowStep(
            step_id=f"op_{i}",
            name=op_name,
            operation=operation,
            depends_on=depends_on,
            expected_indexing_delay=True if "create" in op_name.lower() else False
        ))

    return workflow_processor.create_workflow(name, steps)


async def execute_with_polling(
    workflow_id: str,
    poll_interval_seconds: int = 5,
    max_wait_minutes: int = 30
) -> Dict[str, Any]:
    """Execute a workflow and poll for completion."""
    # Start workflow in background
    await workflow_processor.execute_workflow(workflow_id, run_in_background=True)

    start_time = time.time()
    max_wait_seconds = max_wait_minutes * 60

    while time.time() - start_time < max_wait_seconds:
        status = workflow_processor.get_workflow_status(workflow_id)

        if not status:
            raise ValueError(f"Workflow {workflow_id} not found")

        if status['status'] in ['completed', 'failed', 'cancelled']:
            return status

        # Still running, wait and poll again
        await asyncio.sleep(poll_interval_seconds)

    # Timeout - cancel the workflow
    await workflow_processor.cancel_workflow(workflow_id)
    raise TimeoutError(f"Workflow {workflow_id} timed out after {max_wait_minutes} minutes")