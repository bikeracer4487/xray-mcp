#!/usr/bin/env python3
"""Test suite for security features of Xray MCP server.

This test suite validates the security implementations including:
- Input sanitization against various attack vectors
- GraphQL injection protection
- Response size limiting
- Credential management security
- Connection pool security

Run tests with: python test_security_features.py
"""

import unittest
import asyncio
import json
from unittest.mock import Mock, patch, AsyncMock
import sys
import os

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from security.input_sanitizer import InputSanitizer, SanitizationConfig, sanitize_input
from security.response_limiter import ResponseLimiter, ResponseLimits, ResponseSizeLimitError
from security.credential_manager import SecureCredentials, CredentialManager, validate_environment_credentials
from validators.graphql_validator import GraphQLValidator
from exceptions import ValidationError


class TestInputSanitizer(unittest.TestCase):
    """Test input sanitization functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.sanitizer = InputSanitizer()
        self.strict_sanitizer = InputSanitizer(SanitizationConfig(strict_mode=True))
    
    def test_xss_protection(self):
        """Test XSS attack prevention."""
        # Test script tag blocking
        malicious_input = "<script>alert('XSS')</script>Hello World"
        with self.assertRaises(ValidationError) as context:
            self.sanitizer.sanitize_text(malicious_input)
        self.assertIn("XSS pattern detected", str(context.exception))
        
        # Test javascript: URL blocking  
        malicious_input = "javascript:alert('XSS')"
        with self.assertRaises(ValidationError):
            self.sanitizer.sanitize_text(malicious_input)
        
        # Test event handler blocking
        malicious_input = "<div onclick='alert()'>Click me</div>"
        with self.assertRaises(ValidationError):
            self.sanitizer.sanitize_text(malicious_input)
    
    def test_sql_injection_protection(self):
        """Test SQL injection pattern blocking."""
        # Test union select
        malicious_input = "test'; UNION SELECT * FROM users; --"
        with self.assertRaises(ValidationError) as context:
            self.sanitizer.sanitize_text(malicious_input)
        self.assertIn("SQL injection pattern detected", str(context.exception))
        
        # Test OR injection
        malicious_input = "test' OR '1'='1"
        with self.assertRaises(ValidationError):
            self.sanitizer.sanitize_text(malicious_input)
    
    def test_command_injection_protection(self):
        """Test command injection pattern blocking."""
        # Test command chaining
        malicious_input = "test; rm -rf /"
        with self.assertRaises(ValidationError) as context:
            self.sanitizer.sanitize_text(malicious_input)
        self.assertIn("Command injection pattern detected", str(context.exception))
        
        # Test command substitution
        malicious_input = "test `cat /etc/passwd`"
        with self.assertRaises(ValidationError):
            self.sanitizer.sanitize_text(malicious_input)
    
    def test_path_traversal_protection(self):
        """Test path traversal attack blocking."""
        malicious_input = "../../../etc/passwd"
        with self.assertRaises(ValidationError) as context:
            self.sanitizer.sanitize_text(malicious_input)
        self.assertIn("Path traversal pattern detected", str(context.exception))
        
        # Test URL encoded traversal
        malicious_input = "/%2e%2e/%2e%2e/etc/passwd"
        with self.assertRaises(ValidationError):
            self.sanitizer.sanitize_text(malicious_input)
    
    def test_legitimate_content_preservation(self):
        """Test that legitimate content is preserved."""
        # Test normal text
        clean_text = "This is a normal test summary for JIRA-123"
        result = self.sanitizer.sanitize_text(clean_text)
        self.assertEqual(result, clean_text)
        
        # Test allowed Markdown
        markdown_text = "**Bold text** and *italic text* with `code`"
        result = self.sanitizer.sanitize_text(markdown_text)
        self.assertEqual(result, markdown_text)
        
        # Test Unicode characters
        unicode_text = "Testing with émojis 🚀 and ñoñó"
        result = self.sanitizer.sanitize_text(unicode_text)
        self.assertEqual(result, unicode_text)
    
    def test_html_sanitization(self):
        """Test HTML content sanitization."""
        # Test dangerous tag removal
        html_input = "<script>evil()</script><p>Good content</p>"
        result = self.strict_sanitizer.sanitize_text(html_input)
        self.assertNotIn("<script>", result)
        self.assertNotIn("evil()", result)
        
        # Test safe HTML with non-strict mode
        config = SanitizationConfig(allow_html=True, strict_mode=False)
        lenient_sanitizer = InputSanitizer(config)
        safe_html = "<p>Safe content</p><strong>Bold</strong>"
        result = lenient_sanitizer.sanitize_text(safe_html)
        self.assertIn("<p>", result)
        self.assertIn("<strong>", result)
    
    def test_json_sanitization(self):
        """Test JSON content sanitization."""
        # Test valid JSON
        valid_json = '{"name": "test", "value": 123}'
        result = self.sanitizer.sanitize_json_string(valid_json)
        self.assertIsInstance(result, str)
        parsed = json.loads(result)
        self.assertEqual(parsed["name"], "test")
        
        # Test JSON with dangerous content
        malicious_json = '{"script": "<script>alert()</script>"}'
        with self.assertRaises(ValidationError):
            self.sanitizer.sanitize_json_string(malicious_json)
    
    def test_url_sanitization(self):
        """Test URL sanitization."""
        # Test safe URL
        safe_url = "https://example.com/path?param=value"
        result = self.sanitizer.sanitize_url(safe_url)
        self.assertEqual(result, safe_url)
        
        # Test dangerous schemes
        dangerous_urls = [
            "javascript:alert('xss')",
            "vbscript:msgbox('xss')",
            "data:text/html,<script>alert()</script>",
        ]
        
        for url in dangerous_urls:
            with self.assertRaises(ValidationError):
                self.sanitizer.sanitize_url(url)
    
    def test_length_limits(self):
        """Test input length limiting."""
        # Test within limits
        normal_text = "A" * 100
        result = self.sanitizer.sanitize_text(normal_text)
        self.assertEqual(result, normal_text)
        
        # Test exceeding limits
        long_text = "A" * 20000
        with self.assertRaises(ValidationError) as context:
            self.sanitizer.sanitize_text(long_text)
        self.assertIn("exceeds maximum length", str(context.exception))


class TestGraphQLValidator(unittest.TestCase):
    """Test GraphQL injection protection."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.validator = GraphQLValidator()
    
    def test_allowed_queries(self):
        """Test that legitimate queries are allowed."""
        valid_queries = [
            "query { getTest(issueId: \"TEST-123\") { issueId } }",
            "query { getTests(jql: \"project = TEST\") { total } }",
            "mutation { createTest(testIssueFields: { summary: \"Test\" }) { test { issueId } } }",
        ]
        
        for query in valid_queries:
            try:
                result = self.validator.validate_query(query)
                self.assertIsInstance(result, str)
                self.assertGreater(len(result), 0)
            except Exception as e:
                self.fail(f"Valid query was rejected: {query}, Error: {e}")
    
    def test_blocked_queries(self):
        """Test that dangerous queries are blocked."""
        dangerous_queries = [
            "query { __schema { types { name } } }",  # Schema introspection
            "query { evilField }",  # Non-whitelisted field
            "query { getTest(issueId: \"'; DROP TABLE users; --\") { issueId } }",  # SQL-like injection
        ]
        
        for query in dangerous_queries:
            with self.assertRaises(Exception):
                self.validator.validate_query(query)
    
    def test_query_depth_limiting(self):
        """Test query depth limiting."""
        # Test deep nesting (should be limited)
        deep_query = "query { " + "getTest { " * 20 + "issueId" + " }" * 21
        with self.assertRaises(Exception):
            self.validator.validate_query(deep_query)
    
    def test_variable_validation(self):
        """Test GraphQL variable validation."""
        query = "query GetTest($id: String!) { getTest(issueId: $id) { issueId } }"
        
        # Test with valid variables
        valid_vars = {"id": "TEST-123"}
        result = self.validator.validate_query(query, valid_vars)
        self.assertIsInstance(result, str)
        
        # Test with dangerous variables
        dangerous_vars = {"id": "<script>alert()</script>"}
        with self.assertRaises(Exception):
            self.validator.validate_query(query, dangerous_vars)


class TestResponseLimiter(unittest.TestCase):
    """Test response size limiting."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.limiter = ResponseLimiter()
    
    @patch('aiohttp.ClientResponse')
    def test_json_size_limit(self, mock_response):
        """Test JSON response size limiting."""
        # Test normal size response
        normal_data = {"result": "success"}
        mock_response.json = AsyncMock(return_value=normal_data)
        mock_response.headers = {"content-length": "100"}
        
        async def test_normal():
            result = await self.limiter.read_json_response(mock_response)
            self.assertEqual(result, normal_data)
        
        asyncio.run(test_normal())
        
        # Test oversized response
        mock_response.headers = {"content-length": str(self.limiter.limits.max_response_size + 1000)}
        
        async def test_oversized():
            with self.assertRaises(ResponseSizeLimitError):
                await self.limiter.read_json_response(mock_response)
        
        asyncio.run(test_oversized())
    
    @patch('aiohttp.ClientResponse')
    def test_text_size_limit(self, mock_response):
        """Test text response size limiting."""
        # Test normal size response
        normal_text = "Success response"
        mock_response.text = AsyncMock(return_value=normal_text)
        mock_response.headers = {"content-length": "100"}
        
        async def test_normal():
            result = await self.limiter.read_text_response(mock_response)
            self.assertEqual(result, normal_text)
        
        asyncio.run(test_normal())


class TestCredentialManager(unittest.TestCase):
    """Test secure credential management."""
    
    def test_credential_validation(self):
        """Test credential validation."""
        # Test valid credentials
        valid_creds = SecureCredentials("valid_client_id", "valid_secret_key_12345")
        self.assertEqual(valid_creds.client_id, "valid_client_id")
        
        # Test credential masking in string representation
        cred_str = str(valid_creds)
        self.assertIn("valid_cl...", cred_str)  # Client ID should be partially masked
        self.assertIn("*" * 8, cred_str)  # Secret should be masked
        self.assertNotIn("valid_secret_key_12345", cred_str)  # Full secret should not appear
    
    def test_weak_credential_detection(self):
        """Test detection of weak credentials."""
        weak_credentials = [
            ("client", "password"),  # Too simple
            ("test", "123456"),  # Numeric
            ("user", "user"),  # Same as client_id
        ]
        
        for client_id, client_secret in weak_credentials:
            with self.assertRaises(ValueError):
                SecureCredentials(client_id, client_secret)
    
    @patch.dict(os.environ, {
        'XRAY_CLIENT_ID': 'test_client_id_12345',
        'XRAY_CLIENT_SECRET': 'secure_secret_key_67890'
    })
    def test_environment_validation(self):
        """Test environment variable validation."""
        result = validate_environment_credentials()
        self.assertIsInstance(result, SecureCredentials)
        self.assertEqual(result.client_id, 'test_client_id_12345')
    
    @patch.dict(os.environ, {}, clear=True)
    def test_missing_environment_vars(self):
        """Test handling of missing environment variables."""
        with self.assertRaises(ValueError) as context:
            validate_environment_credentials()
        self.assertIn("XRAY_CLIENT_ID", str(context.exception))


class TestSecurityIntegration(unittest.TestCase):
    """Test integration of security features."""
    
    def test_sanitizer_global_functions(self):
        """Test global sanitizer functions."""
        # Test global sanitize_input function
        clean_text = "Normal test input"
        result = sanitize_input(clean_text)
        self.assertEqual(result, clean_text)
        
        # Test with malicious content
        malicious_text = "<script>alert('xss')</script>"
        with self.assertRaises(ValidationError):
            sanitize_input(malicious_text)
    
    def test_security_configuration(self):
        """Test security configuration options."""
        # Test custom sanitization config
        config = SanitizationConfig(
            allow_html=False,
            max_length=500,
            strict_mode=True
        )
        sanitizer = InputSanitizer(config)
        
        # Test length limit enforcement
        long_text = "A" * 600
        with self.assertRaises(ValidationError):
            sanitizer.sanitize_text(long_text)
        
        # Test HTML blocking in strict mode
        html_text = "<p>Paragraph</p>"
        result = sanitizer.sanitize_text(html_text)
        self.assertNotIn("<p>", result)


def run_security_tests():
    """Run all security tests and return results."""
    print("🔒 Running Xray MCP Security Feature Tests...")
    print("=" * 50)
    
    # Create test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    test_classes = [
        TestInputSanitizer,
        TestGraphQLValidator,
        TestResponseLimiter,
        TestCredentialManager,
        TestSecurityIntegration,
    ]
    
    for test_class in test_classes:
        tests = loader.loadTestsFromTestCase(test_class)
        suite.addTests(tests)
    
    # Run tests
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All security tests passed!")
        print(f"Ran {result.testsRun} tests successfully")
    else:
        print("❌ Some security tests failed!")
        print(f"Tests run: {result.testsRun}")
        print(f"Failures: {len(result.failures)}")
        print(f"Errors: {len(result.errors)}")
    
    return result.wasSuccessful()


if __name__ == "__main__":
    success = run_security_tests()
    sys.exit(0 if success else 1)