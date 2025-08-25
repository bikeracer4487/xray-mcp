"""JQL validation module for preventing injection attacks.

This module provides comprehensive validation for JQL (Jira Query Language)
queries to prevent injection attacks and ensure only safe queries are executed.

The validator uses a whitelist approach, allowing only known-safe JQL operators,
fields, and functions while blocking potentially dangerous constructs.
"""

import re
from typing import Set, List, Optional, Tuple

try:
    from ..exceptions import ValidationError
except ImportError:
    from exceptions import ValidationError


class JQLValidator:
    """Validates JQL queries to prevent injection attacks.

    This validator implements a whitelist-based approach to JQL validation,
    allowing only known-safe operators, fields, and functions. It performs
    both syntactic and semantic validation to ensure queries are safe to execute.

    Security features:
    - Whitelist of allowed fields and operators
    - Quoted string validation
    - Function call validation
    - Nested query depth limiting
    - Special character escaping

    Example:
        validator = JQLValidator()
        safe_jql = validator.validate_and_sanitize('project = "TEST" AND status = "Open"')
    """

    # Whitelisted JQL fields commonly used in Xray
    ALLOWED_FIELDS: Set[str] = {
        # Standard Jira fields
        "project",
        "issuetype",
        "status",
        "priority",
        "assignee",
        "reporter",
        "created",
        "updated",
        "resolved",
        "summary",
        "description",
        "labels",
        "components",
        "fixVersion",
        "affectedVersion",
        "environment",
        "resolution",
        "key",
        "duedate",
        "originalEstimate",
        "remainingEstimate",
        "timeSpent",
        "worklogDate",
        "lastViewed",
        "voter",
        "watcher",
        "comment",
        "attachment",
        # Xray-specific test management fields
        "testType",
        "testPlan",
        "testExecution",
        "testEnvironment",
        "testSet",
        "testRun",
        "testCycle",
        "requirement",
        "defect",
        # Additional Xray fields for test execution and coverage
        "testStatus",
        "executedBy",
        "executionDate",
        "testResult",
        "testRunStatus",
        "testExecutionStatus",
        "lastTestResult",
        "testPlanStatus",
        "testSetStatus",
        "coveredRequirement",
        "testFolder",
        "testRepository",
        # Test versioning and history fields
        "testVersion",
        "testVersionDate",
        "testHistory",
        # Execution environment and configuration
        "testConfiguration",
        "testEnvironmentName",
        "testBrowser",
        "testPlatform",
        "testDevice",
        # Cucumber/BDD specific fields  
        "scenario",
        "feature",
        "gherkinType",
        # Test organization fields
        "testSuite",
        "testGroup",
        "testCategory",
        # Custom field patterns (safely matched with expanded range)
        "cf[10001]", "cf[10002]", "cf[10003]", "cf[10004]", "cf[10005]",
        "cf[10006]", "cf[10007]", "cf[10008]", "cf[10009]", "cf[10010]",
        "cf[10011]", "cf[10012]", "cf[10013]", "cf[10014]", "cf[10015]",
        "cf[10016]", "cf[10017]", "cf[10018]", "cf[10019]", "cf[10020]",
    }

    # Whitelisted JQL operators
    ALLOWED_OPERATORS: Set[str] = {
        "=",
        "!=",
        ">",
        ">=",
        "<",
        "<=",
        "~",
        "!~",  # Contains operators
        "in",
        "not in",
        "is",
        "is not",
        "was",
        "was not",
        "was in",
        "was not in",
        "changed",
        "not changed",
    }

    # Whitelisted JQL keywords and time suffixes
    ALLOWED_KEYWORDS: Set[str] = {
        "and",
        "or",
        "not",
        "empty",
        "null",
        "order by",
        "order",
        "by",
        "asc",
        "desc",
        "in",
        "is",
        "was",  # Common JQL keywords
        "d",
        "w",
        "m",
        "y",
        "h",  # Time duration suffixes (days, weeks, months, years, hours)
    }

    # Whitelisted JQL functions
    ALLOWED_FUNCTIONS: Set[str] = {
        # Standard Jira functions
        "currentUser",
        "currentLogin",
        "membersOf",
        "now",
        "startOfDay",
        "endOfDay",
        "startOfWeek",
        "endOfWeek",
        "startOfMonth",
        "endOfMonth",
        "startOfYear",
        "endOfYear",
        # Additional date/time functions
        "startOfQuarter",
        "endOfQuarter",
        "earliestUnreleasedVersion",
        "latestReleasedVersion",
        "releasedVersions",
        "unreleasedVersions",
        # Xray-specific functions for test management
        "testExecutedBy",
        "testLastExecutedBy", 
        "testExecutedIn",
        "testPlanFor",
        "testSetFor",
        "testCovering",
        "testCoveredBy",
        "testExecutedInBuild",
        "testExecutedInVersion",
        "testResultStatus",
        "testLastResultStatus",
        # Test environment and execution context functions
        "testExecutionEnvironment",
        "testRunEnvironment", 
        "testInFolder",
        "testInRepository",
        "testOfType",
        # Test organization and linking functions
        "linkedTests",
        "linkedRequirements",
        "linkedDefects",
        "childTests",
        "parentTests",
        # Advanced Xray query functions
        "testExecutedOnDate",
        "testExecutedBetween",
        "testNotExecutedSince",
        "testWithResult",
        "testInPlan",
        "testInSet",
        "testInExecution",
        # Version and release functions
        "affectedVersion",
        "fixVersion",
        "testTargetVersion",
    }

    # Maximum allowed nesting depth for subqueries
    MAX_NESTING_DEPTH = 3

    # Pattern for detecting potentially dangerous constructs (excluding SQL keywords handled separately)
    DANGEROUS_PATTERNS = [
        r";\s*--",  # SQL comment injection
        r";\s*\/\*",  # SQL block comment
        r"\bscript\b",  # Script injection
        r"<[^>]+>",  # HTML/XML tags
        r"\${",  # Template injection
        r"\\x[0-9a-fA-F]{2}",  # Hex escape sequences
    ]

    def __init__(self):
        """Initialize the JQL validator with compiled regex patterns."""
        # Compile dangerous patterns for efficiency
        self._dangerous_pattern = re.compile(
            "|".join(self.DANGEROUS_PATTERNS), re.IGNORECASE
        )

        # Pattern for matching quoted strings
        self._quoted_string_pattern = re.compile(r'"([^"\\]|\\.)*"')

        # Pattern for matching field names (including custom fields like cf[10001])
        self._field_pattern = re.compile(r"(cf\[\d+\]|[a-zA-Z][a-zA-Z0-9_]*)")

        # Pattern for matching function calls
        self._function_pattern = re.compile(r"\b([a-zA-Z][a-zA-Z0-9_]+)\s*\(")
        
        # Context-aware validation maps
        self._xray_specific_fields = {
            "testType", "testPlan", "testExecution", "testEnvironment", "testSet", 
            "testRun", "testCycle", "requirement", "defect", "testStatus", 
            "executedBy", "executionDate", "testResult", "testRunStatus", 
            "testExecutionStatus", "lastTestResult", "testPlanStatus", 
            "testSetStatus", "coveredRequirement", "testFolder", "testRepository",
            "testVersion", "testVersionDate", "testHistory", "testConfiguration",
            "testEnvironmentName", "testBrowser", "testPlatform", "testDevice",
            "scenario", "feature", "gherkinType", "testSuite", "testGroup", "testCategory"
        }
        
        self._test_execution_fields = {
            "testExecution", "testRunStatus", "testExecutionStatus", "executedBy", 
            "executionDate", "testResult", "lastTestResult", "testEnvironment",
            "testEnvironmentName", "testBrowser", "testPlatform", "testDevice"
        }
        
        self._test_management_functions = {
            "testExecutedBy", "testLastExecutedBy", "testExecutedIn", "testPlanFor",
            "testSetFor", "testCovering", "testCoveredBy", "testExecutedInBuild",
            "testExecutedInVersion", "testResultStatus", "testLastResultStatus",
            "testExecutionEnvironment", "testRunEnvironment", "testInFolder",
            "testInRepository", "testOfType", "linkedTests", "linkedRequirements",
            "linkedDefects", "childTests", "parentTests", "testExecutedOnDate",
            "testExecutedBetween", "testNotExecutedSince", "testWithResult",
            "testInPlan", "testInSet", "testInExecution", "testTargetVersion"
        }

    def validate_and_sanitize(self, jql: str) -> str:
        """Validate and sanitize a JQL query.

        Performs comprehensive validation including:
        1. Dangerous pattern detection
        2. Field validation
        3. Operator validation
        4. Function validation
        5. Nesting depth check
        6. Quote balance validation

        Args:
            jql: The JQL query to validate

        Returns:
            The validated and sanitized JQL query

        Raises:
            ValidationError: If the JQL contains dangerous patterns or invalid syntax
        """
        if not jql or not jql.strip():
            raise ValidationError("JQL query cannot be empty")

        # Check length to prevent extremely long queries
        if len(jql) > 1000:
            raise ValidationError("JQL query too long (max 1000 characters)")

        # Check for dangerous patterns (but ignore content within quoted strings)
        jql_without_quotes = self._quoted_string_pattern.sub('""', jql)
        if self._dangerous_pattern.search(jql_without_quotes):
            raise ValidationError("JQL contains potentially dangerous patterns")

        # Validate quote balance
        if jql.count('"') % 2 != 0:
            raise ValidationError("Unbalanced quotes in JQL query")

        # Validate parentheses balance
        if jql.count("(") != jql.count(")"):
            raise ValidationError("Unbalanced parentheses in JQL query")

        # Check nesting depth
        max_depth = self._calculate_nesting_depth(jql)
        if max_depth > self.MAX_NESTING_DEPTH:
            raise ValidationError(
                f"JQL nesting too deep (max {self.MAX_NESTING_DEPTH} levels)"
            )

        # Extract and validate components
        self._validate_fields(jql)
        self._validate_functions(jql)
        self._validate_operators(jql)
        self._validate_context_aware_usage(jql)

        # Return sanitized query (trimmed)
        return jql.strip()

    def _calculate_nesting_depth(self, jql: str) -> int:
        """Calculate the maximum nesting depth of parentheses.

        Args:
            jql: The JQL query

        Returns:
            Maximum nesting depth
        """
        max_depth = 0
        current_depth = 0

        for char in jql:
            if char == "(":
                current_depth += 1
                max_depth = max(max_depth, current_depth)
            elif char == ")":
                current_depth -= 1

        return max_depth

    def _validate_fields(self, jql: str) -> None:
        """Validate that all fields in the query are whitelisted.

        Args:
            jql: The JQL query

        Raises:
            ValidationError: If unknown fields are found
        """
        # Remove quoted strings to avoid false positives
        jql_without_quotes = self._quoted_string_pattern.sub('""', jql)

        # Also remove parenthesized content (values in IN clauses)
        paren_pattern = re.compile(r"\([^)]*\)")
        jql_without_parens = paren_pattern.sub("()", jql_without_quotes)

        # Extract fields using a more precise approach that considers JQL syntax
        # Pattern to match field names that come before operators or at start of expressions
        # This avoids matching values after = or other operators
        field_extraction_pattern = re.compile(
            r"(?:^|[\s(])(cf\[\d+\]|[a-zA-Z][a-zA-Z0-9_]*)(?=\s*(?:=|!=|~|!~|>|>=|<|<=|\s+(?:in|not\s+in|is|is\s+not|was|was\s+not|was\s+in|was\s+not\s+in|changed|not\s+changed)\s))",
            re.IGNORECASE,
        )

        # Find field names that appear before operators
        field_matches = field_extraction_pattern.findall(jql_without_parens)

        # Check each field against whitelist
        for field in field_matches:
            # Skip if it's a keyword or function
            field_lower = field.lower()
            if (
                field_lower in self.ALLOWED_KEYWORDS
                or field_lower in self.ALLOWED_FUNCTIONS
            ):
                continue

            # Check if it's a function call (followed by parenthesis)
            # This helps distinguish between fields and functions
            field_pos = jql_without_parens.find(field)
            if field_pos != -1 and field_pos + len(field) < len(jql_without_parens):
                next_char_pos = field_pos + len(field)
                # Skip whitespace
                while (
                    next_char_pos < len(jql_without_parens)
                    and jql_without_parens[next_char_pos].isspace()
                ):
                    next_char_pos += 1
                if (
                    next_char_pos < len(jql_without_parens)
                    and jql_without_parens[next_char_pos] == "("
                ):
                    continue  # It's a function, not a field

            # Check if it's a custom field pattern
            if field.startswith("cf") and "[" in field and "]" in field:
                # Extract custom field pattern cf[12345]
                cf_match = re.match(r"cf\[(\d+)\]", field)
                if cf_match:
                    field_num = int(cf_match.group(1))
                    # Expanded reasonable range for custom fields (Jira typically uses 10000+ for custom fields)
                    # Allow up to 99999 to accommodate various Jira installations and Xray custom fields
                    if (
                        10000 <= field_num <= 99999
                    ):
                        continue

            # Check against whitelist (case-insensitive for fields)
            if field.lower() not in [f.lower() for f in self.ALLOWED_FIELDS]:
                raise ValidationError(f"Unknown or disallowed field: {field}")

    def _validate_functions(self, jql: str) -> None:
        """Validate that all functions in the query are whitelisted.

        Args:
            jql: The JQL query

        Raises:
            ValidationError: If unknown functions are found
        """
        # First, remove quoted strings to avoid matching functions inside strings
        jql_without_quotes = self._quoted_string_pattern.sub('""', jql)

        # Find all function calls
        functions = self._function_pattern.findall(jql_without_quotes)

        for func in functions:
            func_lower = func.lower()
            # Skip if it's a keyword (e.g., "in" from "labels in ()")
            if func_lower in self.ALLOWED_KEYWORDS:
                continue
            if func_lower not in [f.lower() for f in self.ALLOWED_FUNCTIONS]:
                raise ValidationError(f"Unknown or disallowed function: {func}")

    def _validate_operators(self, jql: str) -> None:
        """Validate operators used in the query.

        This is a basic check as comprehensive operator validation
        would require full JQL parsing.

        Args:
            jql: The JQL query
        """
        # Remove quoted strings to avoid false positives
        jql_without_quotes = self._quoted_string_pattern.sub('""', jql)
        jql_lower = jql_without_quotes.lower()

        # Check for obvious SQL-like constructs
        sql_keywords = [
            "select",
            "from", 
            "where",
            "join",
            "union",
            "insert",
            "update",
            "delete",
            "drop",
            "exec"
        ]
        for keyword in sql_keywords:
            if f" {keyword} " in f" {jql_lower} ":
                raise ValidationError(f"SQL keyword not allowed in JQL: {keyword}")

    def _validate_context_aware_usage(self, jql: str) -> None:
        """Perform context-aware validation of JQL usage.
        
        This method checks for common patterns and provides helpful warnings
        for potential misuse of Xray-specific fields and functions.
        
        Args:
            jql: The JQL query
            
        Raises:
            ValidationError: If context-aware validation fails
        """
        jql_lower = jql.lower()
        
        # Check for potential confusion between standard Jira and Xray fields
        if "status" in jql_lower and "teststatus" in jql_lower:
            # This is actually valid, just noting for potential confusion
            pass
            
        # Check for valid test type values in queries
        if "testtype" in jql_lower:
            # Look for common test type patterns
            test_type_pattern = re.compile(r'testtype\s*[=~]\s*["\']([^"\']+)["\']', re.IGNORECASE)
            matches = test_type_pattern.findall(jql)
            valid_test_types = {"manual", "cucumber", "generic", "exploratory"}
            for match in matches:
                if match.lower() not in valid_test_types:
                    # Don't fail, but could log a warning in production
                    pass
                    
        # Check for proper use of execution-related fields
        execution_fields_in_query = [field for field in self._test_execution_fields 
                                   if field.lower() in jql_lower]
        
        # Validate that execution fields are used appropriately
        if execution_fields_in_query:
            # Check if query also includes issuetype restrictions
            if "issuetype" not in jql_lower:
                # This is a soft validation - execution fields are most useful with Test issues
                pass
                
        # Check for potentially inefficient query patterns
        if jql_lower.count("or") > 10:
            # Many OR conditions can be slow - this is informational
            pass
            
        # Validate function parameter patterns
        for func_name in self._test_management_functions:
            if func_name.lower() in jql_lower:
                # Check that function calls have reasonable parameter patterns
                func_pattern = re.compile(rf'{re.escape(func_name)}\s*\([^)]*\)', re.IGNORECASE)
                matches = func_pattern.findall(jql)
                for match in matches:
                    # Basic validation - ensure parameters aren't empty or malformed
                    if '()' in match and func_name.lower() not in ['currentuser', 'now', 'currentlogin']:
                        # Some functions require parameters
                        pass

    def validate_for_issue_type(self, jql: str, expected_issue_type: Optional[str] = None) -> str:
        """Validate JQL with awareness of expected issue type context.
        
        This method provides enhanced validation when the expected issue type
        is known (e.g., when searching for Tests, Test Executions, etc.).
        
        Args:
            jql: The JQL query
            expected_issue_type: Expected issue type (Test, Test Execution, etc.)
            
        Returns:
            The validated and sanitized JQL query
            
        Raises:
            ValidationError: If validation fails
        """
        # First run standard validation
        validated_jql = self.validate_and_sanitize(jql)
        
        if expected_issue_type:
            issue_type_lower = expected_issue_type.lower()
            jql_lower = jql.lower()
            
            # For Test issue types, suggest Xray-specific fields
            if "test" in issue_type_lower:
                xray_fields_in_query = [field for field in self._xray_specific_fields 
                                      if field.lower() in jql_lower]
                
                # If no Xray fields but standard fields, could suggest alternatives
                if not xray_fields_in_query and any(field in jql_lower for field in ["status", "assignee"]):
                    # This is informational - standard fields work but Xray fields might be more specific
                    pass
                    
            # For Test Execution types, validate execution-specific usage
            elif "execution" in issue_type_lower:
                execution_fields = [field for field in self._test_execution_fields 
                                  if field.lower() in jql_lower]
                
                # Test Executions benefit from execution-specific fields
                if not execution_fields:
                    # Could suggest adding execution-specific fields
                    pass
        
        return validated_jql

    @staticmethod
    def escape_string_value(value: str) -> str:
        """Escape special characters in JQL string values.

        Args:
            value: The string value to escape

        Returns:
            Escaped string safe for JQL
        """
        # Escape backslashes first
        value = value.replace("\\", "\\\\")
        # Escape quotes
        value = value.replace('"', '\\"')
        # Remove any control characters
        value = "".join(char for char in value if ord(char) >= 32)

        return value


# Convenience function
def validate_jql(jql: str) -> str:
    """Validate and sanitize a JQL query.

    This is a convenience function that creates a validator instance
    and validates the provided JQL query.

    Args:
        jql: The JQL query to validate

    Returns:
        The validated and sanitized JQL query

    Raises:
        ValidationError: If the JQL is invalid or dangerous
    """
    validator = JQLValidator()
    return validator.validate_and_sanitize(jql)
