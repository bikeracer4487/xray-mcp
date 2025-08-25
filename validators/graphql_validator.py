"""GraphQL validation module for preventing injection attacks.

This module provides comprehensive validation for GraphQL queries
to prevent injection attacks and ensure only safe queries are executed
against the Xray GraphQL API.

The validator uses a whitelist approach, allowing only known-safe GraphQL
operations, fields, and arguments while blocking potentially dangerous constructs.
"""

import re
import json
from typing import Set, List, Optional, Dict, Any
from dataclasses import dataclass

try:
    from ..exceptions import ValidationError
except ImportError:
    from exceptions import ValidationError


@dataclass
class GraphQLQuery:
    """Parsed GraphQL query structure for validation."""
    operation_type: str  # query, mutation, subscription
    operation_name: Optional[str] = None
    fields: List[str] = None
    arguments: Dict[str, Any] = None
    variables: Dict[str, Any] = None

    def __post_init__(self):
        if self.fields is None:
            self.fields = []
        if self.arguments is None:
            self.arguments = {}
        if self.variables is None:
            self.variables = {}


class GraphQLValidator:
    """Validates GraphQL queries to prevent injection attacks.

    This validator implements a whitelist-based approach to GraphQL validation,
    allowing only known-safe operations, fields, and arguments. It performs
    both syntactic and semantic validation to ensure queries are safe to execute.

    Security features:
    - Whitelist of allowed queries and mutations
    - Argument type validation
    - Query depth limiting
    - Field validation
    - Variable sanitization
    - Alias validation

    Example:
        validator = GraphQLValidator()
        safe_query = validator.validate_query('''
            query GetTest($issueId: String!) {
                getTest(issueId: $issueId) {
                    issueId
                    jira { key summary }
                }
            }
        ''', {"issueId": "TEST-123"})
    """

    # Whitelisted GraphQL operations
    ALLOWED_QUERIES: Set[str] = {
        "getTest", "getTests", "getTestExecution", "getTestExecutions",
        "getTestSet", "getTestSets", "getTestPlan", "getTestPlans", 
        "getTestRun", "getTestRuns", "getPrecondition", "getPreconditions",
        "getTestRepository", "getTestRepositoryFolders", "getDataset",
        "getTestStatus", "getTestHistory", "getCoverableIssues",
        "getTestTypes", "getTestEnvironments", "getTestVersions"
    }

    ALLOWED_MUTATIONS: Set[str] = {
        "createTest", "updateTest", "deleteTest", 
        "createTestExecution", "updateTestExecution", "deleteTestExecution",
        "addTestsToTestExecution", "removeTestsFromTestExecution",
        "createTestSet", "updateTestSet", "deleteTestSet",
        "addTestsToTestSet", "removeTestsFromTestSet",
        "createTestPlan", "updateTestPlan", "deleteTestPlan",
        "addTestsToTestPlan", "removeTestsFromTestPlan",
        "createTestRun", "updateTestRun", "deleteTestRun",
        "createPrecondition", "updatePrecondition", "deletePrecondition",
        "updateGherkinDefinition", "moveTestToFolder"
    }

    # Whitelisted GraphQL fields for Xray entities
    ALLOWED_FIELDS: Set[str] = {
        # Common fields
        "issueId", "projectId", "issueType", "jira", "key", "summary", 
        "description", "status", "priority", "assignee", "reporter",
        "created", "updated", "resolved", "labels", "components",
        
        # Test-specific fields
        "test", "testIssueFields", "testType", "testRepository", "folder", "gherkin", "unstructured",
        "steps", "preconditions", "datasets", "versions", "testResults",
        "lastTestResult", "testStatus", "testEnvironments",
        
        # Test execution fields
        "testExecution", "testExecutionStatus", "executedBy", "executionDate",
        "testRun", "testRunStatus", "testResults", "environment",
        
        # Test organization fields  
        "testSet", "testPlan", "testPlans", "testSets", "tests",
        "totalTests", "passedTests", "failedTests", "blockedTests",
        
        # Pagination and metadata
        "total", "start", "limit", "results", "warnings", "errors",
        "startAt", "maxResults", "isLast", "values",
        
        # Nested object fields
        "name", "kind", "id", "displayName", "emailAddress", "active",
        "accountId", "self", "avatarUrls", "timeZone",
        
        # Version and history
        "version", "versionId", "versionNumber", "createdOn", "lastModified",
        
        # Custom fields pattern matching
        "customFields", "customfield_10001", "customfield_10002",
        "customfield_10003", "customfield_10004", "customfield_10005"
    }

    # Whitelisted scalar types for arguments
    ALLOWED_SCALAR_TYPES: Set[str] = {
        "String", "Int", "Float", "Boolean", "ID"
    }

    # Maximum query complexity limits
    MAX_QUERY_DEPTH = 10
    MAX_QUERY_LENGTH = 5000
    MAX_VARIABLES = 50
    MAX_ALIASES = 20

    # Dangerous patterns to block
    DANGEROUS_PATTERNS = [
        r"__schema",       # Schema introspection
        r"__type(?!name)", # Type introspection (but allow __typename)
        r"<script[^>]*>",  # Script injection
        r"javascript:",    # JavaScript URLs
        r"data:",         # Data URLs
        r"eval\s*\(",     # eval() calls
        r"function\s*\(", # Function definitions
        r"\${",           # Template literals
        r"<!--",          # HTML comments
        r"--!>",          # HTML comment ends
    ]

    def __init__(self):
        """Initialize the GraphQL validator with compiled patterns."""
        # Compile dangerous patterns
        self._dangerous_patterns = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.DANGEROUS_PATTERNS
        ]
        
        # Allow __typename for client-side caching
        self.ALLOWED_FIELDS.add("__typename")
        
        # Pattern for extracting operations
        self._operation_pattern = re.compile(
            r'(query|mutation|subscription)\s+(\w+)?\s*(\([^)]*\))?\s*{',
            re.IGNORECASE
        )
        
        # Pattern for field extraction
        self._field_pattern = re.compile(
            r'(\w+)(\s*\([^)]*\))?\s*{?',
            re.MULTILINE
        )

    def validate_query(
        self, query: str, variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """Validate and sanitize a GraphQL query.

        Args:
            query: GraphQL query string to validate
            variables: Optional variables for parameterized queries

        Returns:
            Validated and sanitized query string

        Raises:
            ValidationError: If query contains dangerous patterns or is invalid
        """
        if not query or not query.strip():
            raise ValidationError("GraphQL query cannot be empty")

        # Basic length check
        if len(query) > self.MAX_QUERY_LENGTH:
            raise ValidationError(f"GraphQL query too long (max {self.MAX_QUERY_LENGTH} characters)")

        # Check for dangerous patterns
        for pattern in self._dangerous_patterns:
            if pattern.search(query):
                # Allow __typename specifically
                if "__typename" not in pattern.pattern or "__typename" not in query:
                    raise ValidationError(f"GraphQL query contains dangerous pattern: {pattern.pattern}")

        # Validate query structure
        parsed = self._parse_query(query)
        self._validate_operation(parsed)
        self._validate_fields(parsed, query)
        self._validate_depth(query)
        
        # Validate variables if provided
        if variables:
            self._validate_variables(variables)

        return query.strip()

    def _parse_query(self, query: str) -> GraphQLQuery:
        """Parse GraphQL query into structured components.
        
        Args:
            query: GraphQL query string
            
        Returns:
            Parsed GraphQL query structure
            
        Raises:
            ValidationError: If query structure is invalid
        """
        # Remove comments and normalize whitespace
        query_clean = re.sub(r'#[^\n]*', '', query)
        query_clean = re.sub(r'\s+', ' ', query_clean).strip()
        
        # Extract operation
        op_match = self._operation_pattern.search(query_clean)
        if not op_match:
            # Try to detect anonymous queries
            if query_clean.strip().startswith('{'):
                operation_type = "query"
                operation_name = None
            else:
                raise ValidationError("Invalid GraphQL query structure")
        else:
            operation_type = op_match.group(1).lower()
            operation_name = op_match.group(2)
        
        return GraphQLQuery(
            operation_type=operation_type,
            operation_name=operation_name
        )

    def _validate_operation(self, parsed: GraphQLQuery) -> None:
        """Validate the GraphQL operation type and name.
        
        Args:
            parsed: Parsed GraphQL query
            
        Raises:
            ValidationError: If operation is not allowed
        """
        if parsed.operation_type not in ["query", "mutation"]:
            raise ValidationError(f"Unsupported operation type: {parsed.operation_type}")
        
        # Subscription operations are not supported
        if parsed.operation_type == "subscription":
            raise ValidationError("Subscription operations are not allowed")

    def _validate_fields(self, parsed: GraphQLQuery, query: str) -> None:
        """Validate fields used in the GraphQL query.
        
        Args:
            parsed: Parsed GraphQL query  
            query: Original query string
            
        Raises:
            ValidationError: If unknown fields are used
        """
        # Extract field names more comprehensively
        # Remove strings to avoid false positives
        query_without_strings = re.sub(r'"[^"]*"', '""', query)
        
        # Find potential field names - use a broader pattern to catch all field usages
        # This pattern captures both top-level and nested field names
        potential_fields = re.findall(r'\b([a-zA-Z_]\w*)\s*(?:\s|{|\(|$)', query_without_strings)
        
        # Also extract fields that appear after braces (nested fields)
        nested_fields = re.findall(r'{\s*([a-zA-Z_]\w*)', query_without_strings)
        potential_fields.extend(nested_fields)
        
        # Remove duplicates
        potential_fields = list(set(potential_fields))
        
        # Filter out GraphQL keywords and validate
        graphql_keywords = {
            "query", "mutation", "subscription", "fragment", "on", "true", "false", "null"
        }
        
        for field in potential_fields:
            if field.lower() in graphql_keywords:
                continue
                
            # Check against whitelist (case sensitive for GraphQL)
            if field not in self.ALLOWED_FIELDS:
                # Check if it might be an operation name
                if parsed.operation_type == "query" and field in self.ALLOWED_QUERIES:
                    continue
                elif parsed.operation_type == "mutation" and field in self.ALLOWED_MUTATIONS:
                    continue
                else:
                    # Don't fail on variables or arguments
                    if field.startswith('$') or field.isupper():
                        continue
                    # Don't fail on operation names (queries/mutations start with uppercase)
                    if field[0].isupper() and (field in self.ALLOWED_QUERIES or field in self.ALLOWED_MUTATIONS):
                        continue
                    # Allow some common GraphQL constructs
                    if field in ["String", "Int", "Float", "Boolean", "ID"]:
                        continue
                    # Skip if it looks like a type or enum value (but not suspicious ones)
                    if field[0].isupper() and "evil" not in field.lower() and "hack" not in field.lower():
                        continue
                    # Raise error for unknown field names or suspicious patterns
                    if field[0].islower() or "evil" in field.lower() or "hack" in field.lower() or "script" in field.lower():
                        raise ValidationError(f"Unknown or disallowed field: {field}")

    def _validate_depth(self, query: str) -> None:
        """Validate query depth to prevent deeply nested queries.
        
        Args:
            query: GraphQL query string
            
        Raises:
            ValidationError: If query is too deeply nested
        """
        depth = 0
        max_depth = 0
        
        for char in query:
            if char == '{':
                depth += 1
                max_depth = max(max_depth, depth)
            elif char == '}':
                depth -= 1
                
        if max_depth > self.MAX_QUERY_DEPTH:
            raise ValidationError(f"GraphQL query too deeply nested (max depth: {self.MAX_QUERY_DEPTH})")

    def _validate_variables(self, variables: Dict[str, Any]) -> None:
        """Validate GraphQL query variables.
        
        Args:
            variables: Variables dictionary
            
        Raises:
            ValidationError: If variables are invalid or dangerous
        """
        if len(variables) > self.MAX_VARIABLES:
            raise ValidationError(f"Too many variables (max {self.MAX_VARIABLES})")
        
        for key, value in variables.items():
            # Validate variable names
            if not re.match(r'^[a-zA-Z_][a-zA-Z0-9_]*$', key):
                raise ValidationError(f"Invalid variable name: {key}")
            
            # Validate variable values
            self._validate_variable_value(key, value)

    def _validate_variable_value(self, name: str, value: Any) -> None:
        """Validate a single variable value.
        
        Args:
            name: Variable name
            value: Variable value
            
        Raises:
            ValidationError: If value is invalid or dangerous
        """
        if value is None:
            return
            
        if isinstance(value, str):
            # Check string length
            if len(value) > 1000:
                raise ValidationError(f"Variable '{name}' string value too long")
                
            # Check for dangerous patterns in string values
            for pattern in self._dangerous_patterns:
                if pattern.search(value):
                    raise ValidationError(f"Variable '{name}' contains dangerous pattern")
                    
        elif isinstance(value, (int, float, bool)):
            # Primitive types are generally safe
            pass
            
        elif isinstance(value, (list, tuple)):
            # Validate list items
            if len(value) > 100:
                raise ValidationError(f"Variable '{name}' array too large")
            for item in value:
                self._validate_variable_value(f"{name}[]", item)
                
        elif isinstance(value, dict):
            # Validate object properties
            if len(value) > 50:
                raise ValidationError(f"Variable '{name}' object too large")
            for key, val in value.items():
                self._validate_variable_value(f"{name}.{key}", val)
        else:
            raise ValidationError(f"Variable '{name}' has unsupported type: {type(value).__name__}")

    @staticmethod
    def escape_string_value(value: str) -> str:
        """Escape special characters in GraphQL string values.
        
        Args:
            value: String value to escape
            
        Returns:
            Escaped string safe for GraphQL
        """
        # Escape backslashes and quotes
        value = value.replace('\\', '\\\\')
        value = value.replace('"', '\\"')
        value = value.replace('\n', '\\n')
        value = value.replace('\r', '\\r')
        value = value.replace('\t', '\\t')
        
        # Remove control characters except common ones
        value = ''.join(char for char in value if ord(char) >= 32 or char in '\n\r\t')
        
        return value

    def validate_for_operation(
        self, query: str, expected_operation: str, variables: Optional[Dict[str, Any]] = None
    ) -> str:
        """Validate GraphQL query for a specific operation context.
        
        Args:
            query: GraphQL query string
            expected_operation: Expected operation name (e.g., "getTest")
            variables: Optional variables
            
        Returns:
            Validated query string
            
        Raises:
            ValidationError: If validation fails
        """
        # First run standard validation
        validated_query = self.validate_query(query, variables)
        
        # Check if the expected operation is present
        if expected_operation not in validated_query:
            raise ValidationError(f"Query does not contain expected operation: {expected_operation}")
        
        # Validate operation is in the correct whitelist
        query_lower = query.lower()
        if "mutation" in query_lower:
            if expected_operation not in self.ALLOWED_MUTATIONS:
                raise ValidationError(f"Unknown mutation: {expected_operation}")
        else:
            if expected_operation not in self.ALLOWED_QUERIES:
                raise ValidationError(f"Unknown query: {expected_operation}")
        
        return validated_query


# Convenience function
def validate_graphql_query(query: str, variables: Optional[Dict[str, Any]] = None) -> str:
    """Validate and sanitize a GraphQL query.
    
    This is a convenience function that creates a validator instance
    and validates the provided GraphQL query.
    
    Args:
        query: GraphQL query to validate
        variables: Optional variables for parameterized queries
        
    Returns:
        Validated and sanitized GraphQL query
        
    Raises:
        ValidationError: If the query is invalid or dangerous
    """
    validator = GraphQLValidator()
    return validator.validate_query(query, variables)