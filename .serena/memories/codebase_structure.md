# Codebase Structure and Organization

## Root Directory Structure
```
xray-mcp/
├── .claude/                 # Claude Code configuration
├── .serena/                # Serena MCP memories and state
├── src/                    # Main source code
│   ├── schemas/           # Pydantic models (empty - to be implemented)
│   └── tools/             # MCP tool implementations (empty - to be implemented)
├── tests/                  # Test suite
│   └── integration/       # Integration tests against live API
│       └── test_auth_integration.py
├── xray-docs/             # Comprehensive Xray API documentation
├── docs/                  # Project documentation (empty)
├── install-server.sh      # Cross-platform setup script
├── requirements.txt       # Python dependencies
├── pyproject.toml         # Project configuration (minimal)
├── .env.example          # Environment variable template
├── .gitignore           # Git ignore patterns
├── CLAUDE.md            # Claude Code instructions
├── README.md            # Project README (minimal)
└── LICENSE.md           # License file
```

## Source Code Structure (src/)

### schemas/ Directory
**Status**: Empty - awaiting implementation
**Purpose**: Pydantic models for data validation and serialization
**Expected contents**:
- Request/response models for Xray GraphQL API
- Data validation schemas
- Type definitions for MCP tool parameters

### tools/ Directory  
**Status**: Empty - awaiting implementation
**Purpose**: Individual MCP tool implementations
**Expected contents**:
- Test case management tools
- Test execution tools
- Test planning tools
- Authentication tools

## Test Structure (tests/)

### integration/ Directory
**Current contents**:
- `test_auth_integration.py` - Live Xray API authentication tests

**Test class structure**:
```python
class TestXrayAuthIntegration:
    """Integration tests for Xray authentication against live API."""
    
    @pytest.fixture
    def auth(self):
        """Create XrayAuth instance with real credentials."""
        
    @pytest.mark.asyncio
    async def test_authenticate_with_real_api(self, auth):
        """Test authentication against live Xray API."""
```

### unit/ Directory
**Status**: Planned but not yet created
**Purpose**: Unit tests for individual components

## Documentation Structure (xray-docs/)

### API Documentation Files
- `xray_schema.graphql` - Complete GraphQL schema
- `download_xray_docs_v2.py` - Documentation update script
- Multiple reference files:
  - `TESTS_COMPLETE_REFERENCE.md`
  - `TESTEXECUTION_COMPLETE_REFERENCE.md`
  - `TESTPLANS_COMPLETE_REFERENCE.md`
  - `TESTRUN_COMPLETE_REFERENCE.md`
  - And more...

### GraphQL Schema Organization
```
xray-docs/
├── objects/           # GraphQL object type definitions
├── queries/           # Available GraphQL queries
├── mutations/         # GraphQL mutation operations
├── input_objects/     # Input type definitions
├── enums/            # Enumeration definitions
└── scalars/          # Scalar type definitions
```

## Configuration Files

### dependencies and Environment
- `requirements.txt` - Core Python dependencies (fastmcp, aiohttp, pytest, etc.)
- `.env.example` - Template for required environment variables
- `pyproject.toml` - Minimal project configuration (no tool configs yet)

### Development Tools
- `install-server.sh` - Comprehensive setup script for all platforms
- `.gitignore` - Standard Python gitignore patterns

## File Naming Conventions
- Python files: snake_case (e.g., `test_auth_integration.py`)
- Classes: PascalCase (e.g., `TestXrayAuthIntegration`, `XrayAuth`)
- Methods/functions: snake_case (e.g., `test_authenticate_with_real_api`)
- Constants: UPPER_CASE
- Directories: lowercase with underscores if needed

## Import Structure Pattern
Based on existing code:
```python
# Standard library
import os
import pytest

# Third-party
from dotenv import load_dotenv

# Local imports
from src.auth import XrayAuth
```

## Key Missing Components (To Be Implemented)
- Authentication module (`src.auth.XrayAuth` referenced but missing)
- All MCP tool implementations
- All Pydantic schemas
- Unit test structure
- Linting/formatting configuration
- Main entry point/server implementation

## Development State
- **Phase**: Groundup rebuild
- **Working**: Integration test framework, documentation, setup scripts
- **Missing**: Most core source code, but framework and patterns are established