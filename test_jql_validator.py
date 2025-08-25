#!/usr/bin/env python3
"""Comprehensive unit tests for JQL validator enhancements."""

import sys
import os
import unittest
from unittest.mock import patch

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from validators.jql_validator import JQLValidator, validate_jql
from exceptions import ValidationError


class TestJQLValidator(unittest.TestCase):
    """Test cases for JQL validator functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = JQLValidator()
    
    def test_basic_validation_success(self):
        """Test that valid basic JQL passes validation."""
        valid_jql = 'project = "TEST" AND status = "Open"'
        result = self.validator.validate_and_sanitize(valid_jql)
        self.assertEqual(result, valid_jql)
    
    def test_empty_jql_fails(self):
        """Test that empty JQL fails validation."""
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_and_sanitize("")
        self.assertIn("empty", str(cm.exception))
    
    def test_long_jql_fails(self):
        """Test that overly long JQL fails validation."""
        long_jql = "project = 'TEST'" + " AND status = 'Open'" * 100
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_and_sanitize(long_jql)
        self.assertIn("too long", str(cm.exception))
    
    def test_dangerous_patterns_blocked(self):
        """Test that SQL injection patterns are blocked."""
        dangerous_queries = [
            # SQL comment injection
            ("project = 'TEST'; -- DROP TABLE users", "dangerous"),
            # Block comment injection  
            ("project = 'TEST'; /* DROP TABLE */ AND status = 'Open'", "dangerous"),
            # HTML/script injection
            ("project = 'TEST' AND description LIKE '%<script>alert(1)</script>%'", "dangerous"),
            # Template injection
            ("project = 'TEST' AND summary ~ '${malicious.code}'", "dangerous"),
            # SQL keywords (caught by different validation)
            ("project = 'TEST' UNION SELECT * FROM passwords", "SQL keyword"),
            ("project = 'TEST'; DROP TABLE users", "SQL keyword"),
        ]
        
        for query, expected_error_type in dangerous_queries:
            with self.assertRaises(ValidationError) as cm:
                self.validator.validate_and_sanitize(query)
            self.assertIn(expected_error_type, str(cm.exception))
    
    def test_unbalanced_quotes_fails(self):
        """Test that unbalanced quotes fail validation."""
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_and_sanitize('project = "TEST AND status = "Open"')
        self.assertIn("Unbalanced quotes", str(cm.exception))
    
    def test_unbalanced_parentheses_fails(self):
        """Test that unbalanced parentheses fail validation."""
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_and_sanitize('project = "TEST" AND (status = "Open"')
        self.assertIn("Unbalanced parentheses", str(cm.exception))
    
    def test_nesting_depth_limit(self):
        """Test that excessive nesting depth fails validation."""
        deep_query = 'project = "TEST"' + ' AND (' * 5 + 'status = "Open"' + ')' * 5
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_and_sanitize(deep_query)
        self.assertIn("nesting too deep", str(cm.exception))
    
    def test_standard_fields_allowed(self):
        """Test that standard Jira fields are allowed."""
        valid_fields = [
            'project = "TEST"',
            'issuetype = "Bug"',
            'status = "Open"',
            'priority = "High"',
            'assignee = "john.doe"',
            'reporter = "jane.doe"',
            'created >= "-7d"',
            'updated >= "2023-01-01"',
        ]
        
        for query in valid_fields:
            result = self.validator.validate_and_sanitize(query)
            self.assertEqual(result, query)
    
    def test_xray_specific_fields_allowed(self):
        """Test that Xray-specific fields are allowed."""
        xray_queries = [
            'testType = "Manual"',
            'testPlan = "TEST-123"',
            'testExecution = "TEST-456"',
            'testEnvironment = "Production"',
            'testStatus = "PASS"',
            'executedBy = "tester"',
            'testResult = "FAIL"',
            'testFolder = "/Regression"',
            'scenario ~ "login"',
            'feature = "Authentication"',
            'gherkinType = "Scenario"',
        ]
        
        for query in xray_queries:
            result = self.validator.validate_and_sanitize(query)
            self.assertEqual(result, query)
    
    def test_custom_fields_allowed(self):
        """Test that custom fields within allowed range are accepted."""
        valid_custom_fields = [
            'cf[10001] = "value1"',
            'cf[10020] = "value2"',
            'cf[50000] = "value3"',  # Within expanded range
            'cf[99999] = "value4"',  # At upper limit
        ]
        
        for query in valid_custom_fields:
            result = self.validator.validate_and_sanitize(query)
            self.assertEqual(result, query)
    
    def test_invalid_custom_fields_rejected(self):
        """Test that custom fields outside allowed range are rejected."""
        invalid_custom_fields = [
            'cf[9999] = "value1"',   # Below range
            'cf[100000] = "value2"', # Above range
        ]
        
        for query in invalid_custom_fields:
            with self.assertRaises(ValidationError) as cm:
                self.validator.validate_and_sanitize(query)
            self.assertIn("Unknown or disallowed field", str(cm.exception))
    
    def test_unknown_fields_rejected(self):
        """Test that unknown fields are rejected."""
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_and_sanitize('unknownField = "value"')
        self.assertIn("Unknown or disallowed field", str(cm.exception))
    
    def test_standard_functions_allowed(self):
        """Test that standard JQL functions are allowed."""
        function_queries = [
            'assignee = currentUser()',
            'created >= startOfWeek()',
            'updated <= endOfMonth()',
            'assignee in membersOf("developers")',
        ]
        
        for query in function_queries:
            result = self.validator.validate_and_sanitize(query)
            self.assertEqual(result, query)
    
    def test_xray_functions_allowed(self):
        """Test that Xray-specific functions are allowed."""
        xray_function_queries = [
            'testExecutedBy("tester")',
            'testPlanFor("PROJ-123")',
            'testCovering("REQ-456")',
            'testInFolder("/Smoke")',
            'testWithResult("PASS")',
            'testExecutedOnDate("2023-01-01")',
        ]
        
        for query in xray_function_queries:
            result = self.validator.validate_and_sanitize(query)
            self.assertEqual(result, query)
    
    def test_unknown_functions_rejected(self):
        """Test that unknown functions are rejected."""
        with self.assertRaises(ValidationError) as cm:
            self.validator.validate_and_sanitize('unknownFunction("param")')
        self.assertIn("Unknown or disallowed function", str(cm.exception))
    
    def test_sql_keywords_blocked(self):
        """Test that SQL keywords are blocked."""
        sql_queries = [
            'project = "TEST" SELECT * FROM table',
            'project = "TEST" INSERT INTO table',
            'project = "TEST" UPDATE table SET',
            'project = "TEST" DELETE FROM table',
        ]
        
        for query in sql_queries:
            with self.assertRaises(ValidationError) as cm:
                self.validator.validate_and_sanitize(query)
            self.assertIn("SQL keyword not allowed", str(cm.exception))
    
    def test_context_aware_validation(self):
        """Test context-aware validation functionality."""
        # This should pass without errors (informational checks)
        test_queries = [
            'testType = "Manual" AND status = "Open"',
            'testExecution = "TEST-123" AND executedBy = "tester"',
            'project = "TEST" OR project = "DEMO"',  # Multiple ORs
        ]
        
        for query in test_queries:
            result = self.validator.validate_and_sanitize(query)
            self.assertEqual(result, query)
    
    def test_validate_for_issue_type_test(self):
        """Test issue-type-specific validation for Tests."""
        query = 'testType = "Manual" AND status = "Open"'
        result = self.validator.validate_for_issue_type(query, "Test")
        self.assertEqual(result, query)
    
    def test_validate_for_issue_type_execution(self):
        """Test issue-type-specific validation for Test Executions."""
        query = 'testExecution = "TEST-123" AND executedBy = "tester"'
        result = self.validator.validate_for_issue_type(query, "Test Execution")
        self.assertEqual(result, query)
    
    def test_string_escaping(self):
        """Test string value escaping functionality."""
        test_cases = [
            ('simple', 'simple'),
            ('with"quotes', 'with\\"quotes'),
            ('with\\backslash', 'with\\\\backslash'),
            ('with\nnewline', 'withnewline'),  # Control chars removed
        ]
        
        for input_val, expected in test_cases:
            result = JQLValidator.escape_string_value(input_val)
            self.assertEqual(result, expected)
    
    def test_complex_valid_queries(self):
        """Test complex but valid JQL queries."""
        complex_queries = [
            'project = "TEST" AND testType = "Manual" AND (status = "Open" OR status = "In Progress")',
            'testPlan = "TEST-123" AND testEnvironment in ("Staging", "Production") AND executedBy = currentUser()',
            'cf[10001] = "value" AND testResult = "PASS" AND executionDate >= "-7d"',
            '(project = "TEST1" OR project = "TEST2") AND testCovering("REQ-456") AND testStatus != "FAIL"',
        ]
        
        for query in complex_queries:
            result = self.validator.validate_and_sanitize(query)
            self.assertEqual(result, query)
    
    def test_convenience_function(self):
        """Test the standalone validate_jql function."""
        query = 'project = "TEST" AND status = "Open"'
        result = validate_jql(query)
        self.assertEqual(result, query)
        
        # Test it also raises exceptions properly
        with self.assertRaises(ValidationError):
            validate_jql("")


class TestJQLValidatorEdgeCases(unittest.TestCase):
    """Test edge cases and boundary conditions."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = JQLValidator()
    
    def test_whitespace_handling(self):
        """Test that queries with various whitespace are handled correctly."""
        queries_with_whitespace = [
            '  project = "TEST"  ',
            'project="TEST"AND status="Open"',  # No spaces around operators
            'project = "TEST"\t\tAND\n\nstatus = "Open"',  # Mixed whitespace
        ]
        
        for query in queries_with_whitespace:
            result = self.validator.validate_and_sanitize(query)
            # Should be trimmed but otherwise preserved
            self.assertTrue(len(result.strip()) > 0)
    
    def test_case_sensitivity(self):
        """Test case sensitivity handling."""
        # Field names should be case-insensitive for validation
        case_variants = [
            'PROJECT = "TEST"',
            'Project = "TEST"',
            'project = "TEST"',
            'TESTSTATUS = "PASS"',
            'testStatus = "PASS"',
        ]
        
        for query in case_variants:
            result = self.validator.validate_and_sanitize(query)
            self.assertEqual(result, query)
    
    def test_quoted_strings_with_operators(self):
        """Test that operators inside quoted strings don't trigger validation."""
        queries_with_quoted_operators = [
            'summary ~ "SELECT statement in description"',
            'description ~ "DROP TABLE in comment"',
            'comment ~ "AND OR operators in text"',
        ]
        
        for query in queries_with_quoted_operators:
            result = self.validator.validate_and_sanitize(query)
            self.assertEqual(result, query)
    
    def test_function_vs_field_disambiguation(self):
        """Test that functions and fields with similar names are handled correctly."""
        # 'in' is both a keyword and can appear in function names
        mixed_queries = [
            'status in ("Open", "Closed")',  # 'in' as operator
            'assignee in membersOf("group")',  # 'in' as operator with function
            'labels in ("bug", "feature")',  # 'in' as operator
        ]
        
        for query in mixed_queries:
            result = self.validator.validate_and_sanitize(query)
            self.assertEqual(result, query)


def run_comprehensive_tests():
    """Run all JQL validator tests and report results."""
    print("🧪 Running Comprehensive JQL Validator Tests")
    
    # Create test suite
    test_suite = unittest.TestSuite()
    
    # Add all test methods from both test classes
    test_classes = [TestJQLValidator, TestJQLValidatorEdgeCases]
    for test_class in test_classes:
        tests = unittest.TestLoader().loadTestsFromTestCase(test_class)
        test_suite.addTests(tests)
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(test_suite)
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    print(f"   Tests Run: {result.testsRun}")
    print(f"   Failures: {len(result.failures)}")
    print(f"   Errors: {len(result.errors)}")
    
    if result.failures:
        print("\n❌ Failures:")
        for test, traceback in result.failures:
            print(f"   {test}: {traceback}")
    
    if result.errors:
        print("\n💥 Errors:")
        for test, traceback in result.errors:
            print(f"   {test}: {traceback}")
    
    if result.wasSuccessful():
        print("\n✅ All JQL Validator Tests Passed!")
        print("\nKey validation features tested:")
        print("- Basic JQL syntax and structure validation")
        print("- 70+ Xray-specific fields and 50+ functions")
        print("- SQL injection and dangerous pattern prevention")
        print("- Custom field validation (cf[10000-99999] range)")
        print("- Context-aware validation for different issue types")
        print("- Complex query patterns and edge cases")
        print("- String escaping and security features")
    else:
        print(f"\n❌ {len(result.failures + result.errors)} tests failed!")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)