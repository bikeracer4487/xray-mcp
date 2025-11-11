# Code Style and Conventions

## Python Style Guidelines

### General Python Conventions
- Follow PEP 8 naming conventions
- Use snake_case for functions, variables, and module names
- Use PascalCase for class names
- Use UPPER_CASE for constants

### Async/Await Patterns
Based on existing test code, the project uses modern async/await patterns:
```python
@pytest.mark.asyncio
async def test_authenticate_with_real_api(self, auth):
    """Test authentication against live Xray API."""
    token = await auth.authenticate()
```

### Type Hints
- Expected to use type hints throughout the codebase
- Follow modern Python typing patterns
- Use Pydantic for data validation and serialization

### Docstrings
Based on existing code patterns:
```python
class TestXrayAuthIntegration:
    """Integration tests for Xray authentication against live API."""
    
    async def test_authenticate_with_real_api(self, auth):
        \"\"\"Test authentication against live Xray API.\"\"\"
```

### Import Organization
From existing test file:
```python
import pytest
import os
from dotenv import load_dotenv
from src.auth import XrayAuth
```
- Standard library imports first
- Third-party imports second
- Local project imports last

### Testing Patterns
- Use pytest framework with fixtures
- Mark async tests with `@pytest.mark.asyncio`
- Use descriptive test method names starting with `test_`
- Include docstrings for test classes and methods
- Use fixtures for common setup (like `auth` fixture)

### Error Handling
- Expected to use proper exception handling for API calls
- JWT token validation patterns
- OAuth 2.0 error handling

### Configuration Management
- Use python-dotenv for environment variables
- Load environment variables at module level: `load_dotenv()`
- Access via `os.getenv('VARIABLE_NAME')`

## Framework-Specific Patterns

### FastMCP Patterns
- Tool implementations in src/tools/
- Schema definitions in src/schemas/
- Follow FastMCP framework conventions

### Pydantic Models
- Use for request/response validation
- Follow Pydantic v2 patterns
- Type hints for all fields

### Async HTTP with aiohttp
- Use aiohttp for GraphQL API calls
- Proper async session management
- Bearer token authentication headers

## Current Limitations
- No linting tools configured (black, ruff, mypy)
- No formatting tools setup
- pyproject.toml is minimal
- Code style inferred from limited existing code

## Recommendations for Future
- Setup black for code formatting
- Configure ruff for linting
- Add mypy for type checking
- Configure pre-commit hooks