# Code Style and Conventions

## Code Formatting
- **Black**: Primary code formatter (>= 23.0.0)
- **isort**: Import sorting (>= 5.12.0)
- **Line Length**: Following Black defaults
- **Indentation**: 4 spaces (Python standard)

## Type Annotations  
- **Full Type Safety**: Complete type annotations throughout codebase
- **mypy**: Static type checking (>= 1.0.0)
- **Pydantic**: Runtime type validation for data models
- **Async Types**: Proper typing for async/await patterns

## Naming Conventions
- **Classes**: PascalCase (e.g., `XrayMCPServer`, `TestTools`)
- **Functions/Methods**: snake_case (e.g., `create_test`, `get_executions`)
- **Variables**: snake_case (e.g., `issue_id`, `test_type`)
- **Constants**: UPPER_SNAKE_CASE (e.g., `XRAY_BASE_URL`)
- **Private Members**: Leading underscore (e.g., `_register_tools`)

## Documentation Style
- **Docstrings**: Following Python standards
- **Type Hints**: Inline type annotations preferred
- **Comments**: Minimal, focus on why not what
- **README**: Comprehensive with examples

## Error Handling
- **Custom Exceptions**: Inherit from `XrayMCPError` base class
- **Structured Responses**: `{"error": "message", "type": "ErrorType"}` format
- **Async Error Handling**: Proper exception handling in async contexts
- **No Silent Failures**: All errors must be handled explicitly

## Architecture Patterns
- **Dependency Injection**: Constructor injection pattern
- **Single Responsibility**: Each class/module has one clear purpose
- **Interface Segregation**: Tool classes separated by functionality
- **Clean Architecture**: Clear separation between layers

## Import Organization
- **isort configured**: Automatic import sorting
- **Standard imports**: Python standard library first
- **Third-party imports**: Second group
- **Local imports**: Last group
- **Relative imports**: Used within package structure