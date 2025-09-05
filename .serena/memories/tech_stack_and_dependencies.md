# Tech Stack and Dependencies

## Core Framework
- **FastMCP**: Model Context Protocol framework (>= 2.0.0) - Main MCP server framework
- **Python**: 3.8+ required
- **GraphQL**: Communication with Xray API

## Key Dependencies

### Production Dependencies
- **aiohttp** (>= 3.8.0): Async HTTP client for API communication
- **pydantic** (>= 2.0.0): Data validation and settings management
- **python-dotenv** (>= 1.0.0): Environment variable management
- **PyJWT** (>= 2.8.0): JWT token handling for authentication

### Testing Dependencies  
- **pytest** (>= 7.0.0): Primary testing framework
- **pytest-asyncio** (>= 0.21.0): Async test support
- **pytest-cov** (>= 4.0.0): Code coverage reporting
- **pytest-mock** (>= 3.10.0): Mocking capabilities

### Development Dependencies
- **black** (>= 23.0.0): Code formatting
- **isort** (>= 5.12.0): Import sorting
- **flake8** (>= 6.0.0): Linting
- **mypy** (>= 1.0.0): Type checking

## Architecture Patterns
- **Async/Await**: Full async support throughout
- **Dependency Injection**: GraphQL client injection
- **Repository Pattern**: Data access abstraction
- **Decorator Pattern**: Error handling and logging
- **Factory Pattern**: Tool instantiation
- **Type Safety**: Complete type annotations

## API Integration
- **Xray GraphQL API**: Primary integration point
- **JWT Authentication**: Token-based auth with auto-refresh
- **HTTP/HTTPS**: Standard web protocols