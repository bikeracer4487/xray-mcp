"""Input sanitization module for Xray MCP server.

This module provides comprehensive input sanitization to prevent various types
of attacks including XSS, HTML injection, script injection, and other security
vulnerabilities. It sanitizes text content while preserving legitimate formatting.
"""

import re
import html
import json
import logging
from typing import Optional, Any, Dict, List, Union
from dataclasses import dataclass
from urllib.parse import quote, unquote

# Handle both package and direct execution import modes
try:
    from ..exceptions import ValidationError
except ImportError:
    from exceptions import ValidationError


@dataclass
class SanitizationConfig:
    """Configuration for input sanitization.
    
    Attributes:
        allow_html: Allow basic HTML tags (default: False)
        allow_markdown: Allow Markdown syntax (default: True)
        max_length: Maximum input length (default: 10000)
        allow_unicode: Allow Unicode characters (default: True)
        preserve_newlines: Preserve line breaks (default: True)
        strict_mode: Enable strict sanitization (default: True)
    """
    allow_html: bool = False
    allow_markdown: bool = True
    max_length: int = 10000
    allow_unicode: bool = True
    preserve_newlines: bool = True
    strict_mode: bool = True


class InputSanitizer:
    """Comprehensive input sanitizer for various attack vectors.
    
    This sanitizer protects against:
    - XSS (Cross-Site Scripting) attacks
    - HTML/XML injection
    - Script injection
    - SQL injection patterns
    - Command injection
    - Path traversal attacks
    - Unicode bypass attempts
    - Control character injection
    """
    
    # Dangerous HTML/XML tags that should always be stripped
    DANGEROUS_TAGS = {
        'script', 'style', 'iframe', 'object', 'embed', 'applet',
        'form', 'input', 'button', 'select', 'textarea', 'link',
        'meta', 'base', 'head', 'html', 'body', 'frame', 'frameset',
        'noframes', 'noscript', 'xml', 'svg', 'math', 'details'
    }
    
    # Safe HTML tags that can be allowed in non-strict mode
    SAFE_TAGS = {
        'p', 'br', 'strong', 'em', 'b', 'i', 'u', 'ul', 'ol', 'li',
        'h1', 'h2', 'h3', 'h4', 'h5', 'h6', 'blockquote', 'pre', 'code',
        'div', 'span', 'table', 'tr', 'td', 'th', 'thead', 'tbody'
    }
    
    # Dangerous JavaScript event attributes
    JS_EVENT_ATTRS = {
        'onclick', 'onload', 'onmouseover', 'onmouseout', 'onfocus',
        'onblur', 'onchange', 'onsubmit', 'onerror', 'onabort',
        'onbeforeunload', 'onunload', 'onresize', 'onscroll'
    }
    
    # Patterns for various injection attacks
    XSS_PATTERNS = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'vbscript:',
        r'onload\s*=',
        r'onerror\s*=',
        r'onclick\s*=',
        r'<iframe[^>]*>',
        r'<object[^>]*>',
        r'<embed[^>]*>',
        r'data:text/html',
        r'eval\s*\(',
        r'expression\s*\(',
    ]
    
    SQL_INJECTION_PATTERNS = [
        r"';\s*--",
        r"'\s*or\s+'",
        r"union\s+select",
        r"drop\s+table",
        r"delete\s+from",
        r"insert\s+into",
        r"update\s+.+set",
        r"exec\s*\(",
        r"sp_\w+",
        r"xp_\w+",
    ]
    
    COMMAND_INJECTION_PATTERNS = [
        r';\s*rm\s+',
        r';\s*ls\s*',
        r';\s*cat\s+',
        r'`[^`]+`',
        r'\$\([^)]+\)',
        r'&&\s*\w+',
        r'\|\|\s*\w+',
        r'>\s*/\w+',
        r'<\s*/\w+',
    ]
    
    PATH_TRAVERSAL_PATTERNS = [
        r'\.\./\.\./',
        r'\.\.\\\.\.\\',
        r'/%2e%2e/',
        r'\\%2e%2e\\',
        r'/etc/passwd',
        r'/windows/system32',
        r'c:\\windows',
    ]
    
    def __init__(self, config: Optional[SanitizationConfig] = None):
        """Initialize the input sanitizer.
        
        Args:
            config: Optional sanitization configuration
        """
        self.config = config or SanitizationConfig()
        self.logger = logging.getLogger(__name__)
        
        # Compile regex patterns for efficiency
        self._xss_pattern = re.compile(
            '|'.join(self.XSS_PATTERNS), re.IGNORECASE | re.DOTALL
        )
        self._sql_pattern = re.compile(
            '|'.join(self.SQL_INJECTION_PATTERNS), re.IGNORECASE
        )
        self._command_pattern = re.compile(
            '|'.join(self.COMMAND_INJECTION_PATTERNS), re.IGNORECASE
        )
        self._path_pattern = re.compile(
            '|'.join(self.PATH_TRAVERSAL_PATTERNS), re.IGNORECASE
        )
        
        # HTML tag patterns
        self._html_tag_pattern = re.compile(r'<(/?)([a-zA-Z][a-zA-Z0-9]*)[^>]*>', re.IGNORECASE)
        self._html_attr_pattern = re.compile(r'(\w+)\s*=\s*["\']([^"\']*)["\']', re.IGNORECASE)
    
    def sanitize_text(self, text: Optional[str], field_name: str = "text") -> Optional[str]:
        """Sanitize text content comprehensively.
        
        Args:
            text: Input text to sanitize
            field_name: Name of the field for logging
            
        Returns:
            Sanitized text or None if input was None
            
        Raises:
            ValidationError: If input contains dangerous patterns
        """
        if text is None:
            return None
            
        if not isinstance(text, str):
            raise ValidationError(f"{field_name} must be a string")
        
        # Check length limits
        if len(text) > self.config.max_length:
            raise ValidationError(
                f"{field_name} exceeds maximum length of {self.config.max_length} characters"
            )
        
        original_text = text
        
        # Step 1: Remove control characters except allowed ones
        text = self._remove_control_chars(text)
        
        # Step 2: Detect and handle encoding attacks
        text = self._handle_encoding_attacks(text)
        
        # Step 3: Check for injection patterns
        self._check_injection_patterns(text, field_name)
        
        # Step 4: Sanitize HTML/XML content
        if self.config.strict_mode:
            text = self._strict_html_sanitization(text)
        else:
            text = self._safe_html_sanitization(text)
        
        # Step 5: Handle special characters
        text = self._sanitize_special_chars(text)
        
        # Step 6: Final validation
        text = self._final_validation(text, field_name)
        
        # Log if significant changes were made
        if original_text != text:
            self.logger.info(f"Sanitized {field_name}: removed potentially dangerous content")
        
        return text
    
    def sanitize_json_string(self, json_str: Optional[str], field_name: str = "json") -> Optional[str]:
        """Sanitize JSON string content.
        
        Args:
            json_str: JSON string to sanitize
            field_name: Name of the field for logging
            
        Returns:
            Sanitized JSON string or None if input was None
            
        Raises:
            ValidationError: If JSON is invalid or contains dangerous patterns
        """
        if json_str is None:
            return None
            
        if not isinstance(json_str, str):
            raise ValidationError(f"{field_name} must be a string")
        
        try:
            # Parse JSON to validate structure
            parsed = json.loads(json_str)
            
            # Recursively sanitize JSON content
            sanitized = self._sanitize_json_recursive(parsed, field_name)
            
            # Return sanitized JSON string
            return json.dumps(sanitized, ensure_ascii=False, separators=(',', ':'))
            
        except json.JSONDecodeError as e:
            raise ValidationError(f"Invalid JSON in {field_name}: {str(e)}")
    
    def sanitize_url(self, url: Optional[str], field_name: str = "url") -> Optional[str]:
        """Sanitize URL input.
        
        Args:
            url: URL to sanitize
            field_name: Name of the field for logging
            
        Returns:
            Sanitized URL or None if input was None
            
        Raises:
            ValidationError: If URL contains dangerous patterns
        """
        if url is None:
            return None
            
        if not isinstance(url, str):
            raise ValidationError(f"{field_name} must be a string")
        
        # Check for dangerous schemes
        dangerous_schemes = ['javascript:', 'vbscript:', 'data:', 'file:', 'ftp://']
        url_lower = url.lower().strip()
        
        for scheme in dangerous_schemes:
            if url_lower.startswith(scheme):
                raise ValidationError(f"Dangerous URL scheme detected in {field_name}: {scheme}")
        
        # Check for path traversal in URL
        if self._path_pattern.search(url):
            raise ValidationError(f"Path traversal detected in {field_name}")
        
        # Basic URL sanitization
        url = url.strip()
        url = re.sub(r'[<>"\']', '', url)  # Remove dangerous characters
        
        return url
    
    def _remove_control_chars(self, text: str) -> str:
        """Remove control characters while preserving allowed ones."""
        if not self.config.preserve_newlines:
            # Remove all control characters
            return ''.join(char for char in text if ord(char) >= 32 or char in '\t')
        else:
            # Keep newlines and tabs
            return ''.join(char for char in text if ord(char) >= 32 or char in '\n\r\t')
    
    def _handle_encoding_attacks(self, text: str) -> str:
        """Handle various encoding-based attack attempts."""
        # Decode common encoding attacks
        try:
            # Handle URL encoding
            if '%' in text:
                decoded = unquote(text)
                # Recursively decode up to 3 levels to catch double-encoding
                for _ in range(3):
                    new_decoded = unquote(decoded)
                    if new_decoded == decoded:
                        break
                    decoded = new_decoded
                text = decoded
            
            # Handle HTML entities
            if '&' in text and ';' in text:
                text = html.unescape(text)
                
        except Exception:
            # If decoding fails, use original text
            pass
        
        return text
    
    def _check_injection_patterns(self, text: str, field_name: str) -> None:
        """Check for various injection attack patterns."""
        # Check XSS patterns
        if self._xss_pattern.search(text):
            raise ValidationError(f"XSS pattern detected in {field_name}")
        
        # Check SQL injection patterns
        if self._sql_pattern.search(text):
            raise ValidationError(f"SQL injection pattern detected in {field_name}")
        
        # Check command injection patterns
        if self._command_pattern.search(text):
            raise ValidationError(f"Command injection pattern detected in {field_name}")
        
        # Check path traversal patterns
        if self._path_pattern.search(text):
            raise ValidationError(f"Path traversal pattern detected in {field_name}")
    
    def _strict_html_sanitization(self, text: str) -> str:
        """Perform strict HTML sanitization - remove all tags."""
        # Remove all HTML tags
        text = re.sub(r'<[^>]+>', '', text)
        
        # Escape remaining HTML entities
        text = html.escape(text, quote=False)
        
        return text
    
    def _safe_html_sanitization(self, text: str) -> str:
        """Perform safe HTML sanitization - allow only safe tags."""
        def replace_tag(match):
            is_closing = match.group(1) == '/'
            tag_name = match.group(2).lower()
            
            # Always remove dangerous tags
            if tag_name in self.DANGEROUS_TAGS:
                return ''
            
            # Allow safe tags if HTML is enabled
            if self.config.allow_html and tag_name in self.SAFE_TAGS:
                # Remove dangerous attributes
                full_match = match.group(0)
                safe_tag = self._sanitize_html_attributes(full_match, tag_name)
                return safe_tag
            
            # Remove all other tags
            return ''
        
        return self._html_tag_pattern.sub(replace_tag, text)
    
    def _sanitize_html_attributes(self, tag_html: str, tag_name: str) -> str:
        """Sanitize HTML attributes in a tag."""
        # Find all attributes
        attrs = self._html_attr_pattern.findall(tag_html)
        safe_attrs = []
        
        for attr_name, attr_value in attrs:
            attr_name_lower = attr_name.lower()
            
            # Skip dangerous event attributes
            if attr_name_lower in self.JS_EVENT_ATTRS:
                continue
            
            # Skip dangerous attribute values
            if any(pattern in attr_value.lower() for pattern in ['javascript:', 'vbscript:', 'expression(']):
                continue
            
            # Escape attribute value
            safe_value = html.escape(attr_value, quote=True)
            safe_attrs.append(f'{attr_name}="{safe_value}"')
        
        # Reconstruct tag
        attrs_str = ' ' + ' '.join(safe_attrs) if safe_attrs else ''
        return f'<{tag_name}{attrs_str}>'
    
    def _sanitize_special_chars(self, text: str) -> str:
        """Sanitize special characters based on configuration."""
        # Handle Unicode normalization if needed
        if self.config.allow_unicode:
            # Normalize Unicode to prevent bypass attempts
            import unicodedata
            text = unicodedata.normalize('NFKC', text)
        else:
            # Remove non-ASCII characters
            text = ''.join(char for char in text if ord(char) < 128)
        
        return text
    
    def _final_validation(self, text: str, field_name: str) -> str:
        """Perform final validation and cleanup."""
        # Trim whitespace
        text = text.strip()
        
        # Check if text became empty after sanitization
        if not text and self.config.strict_mode:
            self.logger.warning(f"Text in {field_name} became empty after sanitization")
        
        # Final length check after sanitization
        if len(text) > self.config.max_length:
            text = text[:self.config.max_length]
            self.logger.warning(f"Truncated {field_name} to {self.config.max_length} characters")
        
        return text
    
    def _sanitize_json_recursive(self, obj: Any, field_name: str) -> Any:
        """Recursively sanitize JSON object content."""
        if isinstance(obj, str):
            return self.sanitize_text(obj, f"{field_name}.string")
        elif isinstance(obj, dict):
            return {
                key: self._sanitize_json_recursive(value, f"{field_name}.{key}")
                for key, value in obj.items()
                if isinstance(key, str) and len(key) <= 100  # Limit key length
            }
        elif isinstance(obj, list):
            return [
                self._sanitize_json_recursive(item, f"{field_name}[{i}]")
                for i, item in enumerate(obj[:100])  # Limit array length
            ]
        else:
            # Return primitive types as-is (int, float, bool, None)
            return obj


# Global sanitizer instance with default configuration
_default_sanitizer = InputSanitizer()

def sanitize_input(text: Optional[str], field_name: str = "input") -> Optional[str]:
    """Sanitize input text using default configuration.
    
    Args:
        text: Text to sanitize
        field_name: Field name for error reporting
        
    Returns:
        Sanitized text
    """
    return _default_sanitizer.sanitize_text(text, field_name)


def sanitize_json_input(json_str: Optional[str], field_name: str = "json") -> Optional[str]:
    """Sanitize JSON input using default configuration.
    
    Args:
        json_str: JSON string to sanitize
        field_name: Field name for error reporting
        
    Returns:
        Sanitized JSON string
    """
    return _default_sanitizer.sanitize_json_string(json_str, field_name)


def sanitize_url_input(url: Optional[str], field_name: str = "url") -> Optional[str]:
    """Sanitize URL input using default configuration.
    
    Args:
        url: URL to sanitize
        field_name: Field name for error reporting
        
    Returns:
        Sanitized URL
    """
    return _default_sanitizer.sanitize_url(url, field_name)


def create_custom_sanitizer(
    allow_html: bool = False,
    allow_markdown: bool = True,
    max_length: int = 10000,
    strict_mode: bool = True
) -> InputSanitizer:
    """Create a custom input sanitizer with specific configuration.
    
    Args:
        allow_html: Allow basic HTML tags
        allow_markdown: Allow Markdown syntax
        max_length: Maximum input length
        strict_mode: Enable strict sanitization
        
    Returns:
        Configured InputSanitizer instance
    """
    config = SanitizationConfig(
        allow_html=allow_html,
        allow_markdown=allow_markdown,
        max_length=max_length,
        strict_mode=strict_mode
    )
    return InputSanitizer(config)