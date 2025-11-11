# Task Completion Checklist

## Standard Development Task Completion Steps

### 1. Code Quality Checks
Since no linting/formatting tools are configured yet:
- **Manual code review**: Ensure code follows project conventions
- **Type hints**: Verify proper type annotations
- **Docstrings**: Add docstrings for new classes and methods
- **Import organization**: Follow standard library → third-party → local pattern

### 2. Testing Requirements
```bash
# Run unit tests (when they exist)
pytest

# Run integration tests (requires .env setup with Xray credentials)
pytest tests/integration/

# Run specific test files if changes are targeted
pytest tests/integration/test_auth_integration.py

# Verbose output for debugging
pytest -v
```

### 3. Environment Setup Verification
```bash
# Ensure virtual environment is active
source venv/bin/activate

# Verify dependencies are installed
pip list | grep -E "(fastmcp|aiohttp|pytest|pydantic)"

# Check environment variables if integration tests are needed
echo $XRAY_CLIENT_ID  # Should be set for integration tests
```

### 4. Integration Test Requirements
For tasks involving Xray API integration:
- **Environment variables**: Ensure `.env` file has valid Xray credentials
- **API connectivity**: Integration tests must pass against live Xray API
- **Token validation**: Authentication tests should succeed
- **Error handling**: Test both success and failure scenarios

### 5. Documentation Updates
```bash
# Update API documentation if schema changes occurred
cd xray-docs/
python3 download_xray_docs_v2.py
```

### 6. Code Structure Validation
- **MCP tools**: New tools should go in src/tools/
- **Schemas**: Pydantic models should go in src/schemas/
- **Tests**: Integration tests in tests/integration/, unit tests in tests/unit/
- **Imports**: Verify all imports work correctly

### 7. Async Pattern Compliance
- **Async functions**: Use `async def` for I/O operations
- **Await calls**: Properly await async function calls
- **aiohttp sessions**: Manage HTTP sessions correctly
- **Exception handling**: Handle async exceptions properly

## Pre-Commit Checklist (Manual)
Since no automated tools are setup:

- [ ] Code follows Python PEP 8 conventions
- [ ] All functions have appropriate type hints
- [ ] New classes/methods have docstrings
- [ ] Import statements are organized correctly
- [ ] Async patterns are used correctly
- [ ] Tests pass: `pytest`
- [ ] Integration tests pass (if applicable): `pytest tests/integration/`
- [ ] No hardcoded credentials or secrets
- [ ] Environment variables are properly configured

## Future Improvements Needed
- Setup pre-commit hooks
- Configure black for automatic formatting
- Add ruff for linting
- Setup mypy for type checking
- Add automated test coverage reporting

## Critical Requirements
- **Never commit credentials**: Always use environment variables
- **Test API integration**: Changes affecting Xray API must be tested against live API
- **Maintain async patterns**: All I/O operations should be async
- **Follow MCP patterns**: Adhere to FastMCP framework conventions