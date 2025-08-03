"""Security tests for JQL validator.

This module contains comprehensive tests to ensure the JQL validator
properly prevents injection attacks and validates queries correctly.
"""

import pytest
from validators.jql_validator import JQLValidator, validate_jql
from exceptions import ValidationError


class TestJQLValidator:
    """Test suite for JQL validation security."""
    
    @pytest.fixture
    def validator(self):
        """Create a JQL validator instance."""
        return JQLValidator()
    
    # ========== Valid JQL Tests ==========
    
    def test_valid_simple_queries(self, validator):
        """Test that valid simple JQL queries pass validation."""
        valid_queries = [
            'project = "TEST"',
            'status = "Open"',
            'assignee = currentUser()',
            'created > -7d',
            'issuetype = "Test"',
            'labels in ("automated", "regression")',
            'priority in (High, Critical)',
            'testType = "Manual"'
        ]
        
        for jql in valid_queries:
            # Should not raise any exception
            result = validator.validate_and_sanitize(jql)
            assert result == jql.strip()
    
    def test_valid_complex_queries(self, validator):
        """Test that valid complex JQL queries pass validation."""
        valid_queries = [
            'project = "TEST" AND status = "Open"',
            'project = "TEST" OR project = "DEMO"',
            'assignee = currentUser() AND created > startOfWeek()',
            'project = "TEST" AND (status = "Open" OR status = "In Progress")',
            'testType = "Manual" AND testExecution is not EMPTY',
            'project = "TEST" ORDER BY created DESC',
            'labels = "automated" AND updated > -30d ORDER BY priority DESC'
        ]
        
        for jql in valid_queries:
            result = validator.validate_and_sanitize(jql)
            assert result == jql.strip()
    
    def test_valid_custom_fields(self, validator):
        """Test that valid custom field queries pass validation."""
        valid_queries = [
            'cf[10001] = "Value"',
            'cf[10002] ~ "test"',
            'cf[10003] is not EMPTY',
            'project = "TEST" AND cf[10004] = "Custom Value"'
        ]
        
        for jql in valid_queries:
            result = validator.validate_and_sanitize(jql)
            assert result == jql.strip()
    
    # ========== SQL Injection Tests ==========
    
    def test_sql_injection_attempts(self, validator):
        """Test that SQL injection attempts are blocked."""
        injection_queries = [
            'project = "TEST"; DROP TABLE users;--',
            'project = "TEST" UNION SELECT * FROM passwords',
            "status = 'Open' OR '1'='1'",
            'project = "TEST"; DELETE FROM issues WHERE 1=1;',
            'assignee = "user"; INSERT INTO users VALUES ("hacker", "password");',
            'project = "TEST" /* comment */ UNION SELECT * FROM users',
            'status = "Open"; EXEC xp_cmdshell("net user");',
            'project = "TEST" AND 1=1; UPDATE users SET admin=true;'
        ]
        
        for jql in injection_queries:
            with pytest.raises(ValidationError):
                validator.validate_and_sanitize(jql)
    
    def test_sql_keywords_blocked(self, validator):
        """Test that SQL keywords are blocked."""
        sql_queries = [
            'SELECT * FROM issues',
            'DELETE FROM tests WHERE project = "TEST"',
            'UPDATE issues SET status = "Closed"',
            'INSERT INTO tests VALUES ("test")',
            'DROP TABLE test_executions',
            'project = "TEST" AND SELECT count(*) FROM users'
        ]
        
        for jql in sql_queries:
            with pytest.raises(ValidationError):
                validator.validate_and_sanitize(jql)
    
    # ========== Script Injection Tests ==========
    
    def test_script_injection_attempts(self, validator):
        """Test that script injection attempts are blocked."""
        script_queries = [
            'project = "<script>alert("XSS")</script>"',
            'status = "Open<img src=x onerror=alert(1)>"',
            'assignee = "user${alert(1)}"',
            'project = "TEST${7*7}"',
            'status = "Open\\x3cscript\\x3ealert(1)\\x3c/script\\x3e"',
            'project = "TEST<iframe src=javascript:alert(1)>"'
        ]
        
        for jql in script_queries:
            with pytest.raises(ValidationError, match="dangerous patterns"):
                validator.validate_and_sanitize(jql)
    
    # ========== Input Validation Tests ==========
    
    def test_empty_query(self, validator):
        """Test that empty queries are rejected."""
        with pytest.raises(ValidationError, match="cannot be empty"):
            validator.validate_and_sanitize("")
        
        with pytest.raises(ValidationError, match="cannot be empty"):
            validator.validate_and_sanitize("   ")
    
    def test_query_length_limit(self, validator):
        """Test that overly long queries are rejected."""
        long_query = 'project = "TEST" AND ' * 100  # Creates >1000 char query
        
        with pytest.raises(ValidationError, match="too long"):
            validator.validate_and_sanitize(long_query)
    
    def test_unbalanced_quotes(self, validator):
        """Test that queries with unbalanced quotes are rejected."""
        invalid_queries = [
            'project = "TEST',
            'status = "Open" AND assignee = "user',
            'project = "TEST" AND status = "In Progress'
        ]
        
        for jql in invalid_queries:
            with pytest.raises(ValidationError, match="Unbalanced quotes"):
                validator.validate_and_sanitize(jql)
    
    def test_unbalanced_parentheses(self, validator):
        """Test that queries with unbalanced parentheses are rejected."""
        invalid_queries = [
            'project = "TEST" AND (status = "Open"',
            'project = "TEST" AND status = "Open")',
            '((project = "TEST") AND status = "Open"'
        ]
        
        for jql in invalid_queries:
            with pytest.raises(ValidationError, match="Unbalanced parentheses"):
                validator.validate_and_sanitize(jql)
    
    def test_nesting_depth_limit(self, validator):
        """Test that deeply nested queries are rejected."""
        # Create a query with 4 levels of nesting (exceeds limit of 3)
        deep_query = 'project = "TEST" AND (a = "1" AND (b = "2" AND (c = "3" AND (d = "4"))))'
        
        with pytest.raises(ValidationError, match="nesting too deep"):
            validator.validate_and_sanitize(deep_query)
    
    # ========== Field Validation Tests ==========
    
    def test_unknown_fields_rejected(self, validator):
        """Test that unknown fields are rejected."""
        invalid_queries = [
            'unknownField = "value"',
            'project = "TEST" AND badField = "value"',
            'maliciousField ~ "test"'
        ]
        
        for jql in invalid_queries:
            with pytest.raises(ValidationError, match="Unknown or disallowed field"):
                validator.validate_and_sanitize(jql)
    
    def test_invalid_custom_fields_rejected(self, validator):
        """Test that invalid custom field patterns are rejected."""
        invalid_queries = [
            'cf[abc] = "value"',  # Non-numeric ID
            'cf[99999] = "value"',  # Out of range
            'cf[] = "value"',  # Empty ID
            'cf[10001 = "value"'  # Malformed
        ]
        
        for jql in invalid_queries:
            with pytest.raises(ValidationError):
                validator.validate_and_sanitize(jql)
    
    # ========== Function Validation Tests ==========
    
    def test_unknown_functions_rejected(self, validator):
        """Test that unknown functions are rejected."""
        invalid_queries = [
            'assignee = maliciousFunction()',
            'created > dangerousFunc("param")',
            'project = "TEST" AND assignee = system("command")'
        ]
        
        for jql in invalid_queries:
            with pytest.raises(ValidationError, match="Unknown or disallowed function"):
                validator.validate_and_sanitize(jql)
    
    def test_valid_functions_allowed(self, validator):
        """Test that whitelisted functions are allowed."""
        valid_queries = [
            'assignee = currentUser()',
            'created > startOfDay()',
            'updated < endOfWeek()',
            'assignee in membersOf("developers")',
            'created >= startOfMonth() AND created <= endOfMonth()'
        ]
        
        for jql in valid_queries:
            result = validator.validate_and_sanitize(jql)
            assert result == jql.strip()
    
    # ========== Edge Cases ==========
    
    def test_case_sensitivity(self, validator):
        """Test that validation is case-insensitive for keywords."""
        valid_queries = [
            'PROJECT = "TEST" AND STATUS = "Open"',
            'Project = "TEST" Or Status = "Open"',
            'ASSIGNEE = currentUser() ORDER BY created DESC'
        ]
        
        for jql in valid_queries:
            result = validator.validate_and_sanitize(jql)
            assert result == jql.strip()
    
    def test_whitespace_handling(self, validator):
        """Test that whitespace is handled correctly."""
        queries = [
            ('  project = "TEST"  ', 'project = "TEST"'),
            ('project="TEST"', 'project="TEST"'),
            ('project   =   "TEST"', 'project   =   "TEST"')
        ]
        
        for input_jql, expected in queries:
            result = validator.validate_and_sanitize(input_jql)
            assert result == expected
    
    # ========== Escape Function Tests ==========
    
    def test_escape_string_value(self):
        """Test the string escaping function."""
        test_cases = [
            ('simple', 'simple'),
            ('with "quotes"', 'with \\"quotes\\"'),
            ('with\\backslash', 'with\\\\backslash'),
            ('with\nnewline', 'withnewline'),  # Control chars removed
            ('with\ttab', 'withtab'),  # Control chars removed
        ]
        
        for input_val, expected in test_cases:
            result = JQLValidator.escape_string_value(input_val)
            assert result == expected
    
    # ========== Integration Tests ==========
    
    def test_validate_jql_convenience_function(self):
        """Test the convenience function works correctly."""
        # Valid query should pass
        result = validate_jql('project = "TEST" AND status = "Open"')
        assert result == 'project = "TEST" AND status = "Open"'
        
        # Invalid query should raise
        with pytest.raises(ValidationError):
            validate_jql('project = "TEST"; DROP TABLE users;')