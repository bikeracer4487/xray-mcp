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
        # Xray-specific fields
        "testType",
        "testPlan",
        "testExecution",
        "testEnvironment",
        "requirement",
        "testSet",
        "defect",
        "testRun",
        "testCycle",
        # Custom field patterns (safely matched)
        "cf[10001]",
        "cf[10002]",
        "cf[10003]",
        "cf[10004]",
        "cf[10005]",
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
    }

    # Maximum allowed nesting depth for subqueries
    MAX_NESTING_DEPTH = 3

    # Pattern for detecting potentially dangerous constructs
    DANGEROUS_PATTERNS = [
        r";\s*--",  # SQL comment injection
        r";\s*\/\*",  # SQL block comment
        r"\bunion\b",  # SQL UNION
        r"\bselect\b",  # SQL SELECT
        r"\bdrop\b",  # SQL DROP
        r"\bdelete\b",  # SQL DELETE
        r"\binsert\b",  # SQL INSERT
        r"\bupdate\b",  # SQL UPDATE
        r"\bexec\b",  # SQL EXEC
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

        # Check for dangerous patterns
        if self._dangerous_pattern.search(jql):
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
                    if (
                        10000 <= field_num <= 20000
                    ):  # Reasonable range for custom fields
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
        # This is a simplified check - in production, consider using
        # a proper JQL parser for complete validation
        jql_lower = jql.lower()

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
        ]
        for keyword in sql_keywords:
            if f" {keyword} " in f" {jql_lower} ":
                raise ValidationError(f"SQL keyword not allowed in JQL: {keyword}")

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
