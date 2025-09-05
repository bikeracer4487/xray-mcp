# Task Completion Guidelines

## When a Task is Completed

### Required Code Quality Checks
1. **Format Code**: Run `black .` and `isort .` to ensure consistent formatting
2. **Lint Code**: Run `flake8 .` to check for style violations
3. **Type Check**: Run `mypy .` to verify type annotations
4. **Combined**: `black . && isort . && flake8 . && mypy .`

### Testing Requirements
1. **Run Tests**: Execute `python test_server.py` or `pytest`
2. **Coverage Check**: Ensure coverage meets minimum 80% (`pytest --cov=.`)
3. **Test Categories**: Run relevant test markers (`pytest -m unit`, `-m security`, etc.)
4. **Integration Tests**: Run full test suite if external dependencies changed

### Documentation Updates
1. **Update TOOLSET.md**: If adding/modifying MCP tools
2. **Update README.md**: If changing major functionality
3. **Update CLAUDE.md**: If changing development workflow
4. **Code Comments**: Only add if absolutely necessary for complex logic

### Security Verification  
1. **JQL Validation**: Ensure all JQL inputs use whitelist validation
2. **Error Sanitization**: Verify no sensitive data in error responses
3. **Input Validation**: Check all tool parameters are validated
4. **Credential Safety**: No secrets in code or logs

### Architecture Compliance
1. **Type Annotations**: All new code must have complete type hints
2. **Error Handling**: Use structured error responses with XrayMCPError hierarchy
3. **Async Patterns**: Maintain async/await throughout
4. **Dependency Injection**: Follow existing DI patterns

### Commit Guidelines  
1. **No Claude Co-authorship**: Never add Claude as co-author
2. **Professional Messages**: Clear, descriptive commit messages
3. **Logical Commits**: Each commit should be a logical unit of work
4. **No Secrets**: Ensure no credentials or secrets in commits

## Before Marking Task Complete
- [ ] Code formatted and linted
- [ ] Type checking passes
- [ ] All tests pass with adequate coverage
- [ ] Security considerations addressed
- [ ] Documentation updated if needed
- [ ] Architecture patterns followed

## Common Gotchas
- **Tool Count Limit**: Keep MCP tools ≤ 40 for IDE compatibility
- **JQL Limit**: All JQL queries limited to 100 results max
- **Auth Tokens**: Handled automatically, don't manually manage
- **Error Responses**: Always return structured `{"error": "...", "type": "..."}` format