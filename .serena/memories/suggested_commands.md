# Suggested Development Commands

## Essential Commands for macOS (Darwin)

### Setup and Installation
```bash
# Install dependencies
pip install -r requirements.txt

# Set up environment (copy and edit with your credentials)
cp .env.example .env
# Edit .env with your XRAY_CLIENT_ID and XRAY_CLIENT_SECRET
```

### Running the Server
```bash
# Direct execution (primary method)
python main.py

# Using FastMCP CLI (alternative)
fastmcp run main.py:mcp

# Test the server functionality
python example.py

# Install for MCP client integration
./install-server.sh
```

### Testing Commands
```bash
# Run all tests
python test_server.py

# Run with pytest (more detailed)
pytest

# Run with coverage reporting
pytest --cov=. --cov-report=html

# Run specific test categories
pytest -m unit
pytest -m integration  
pytest -m security
pytest -m slow

# Run specific test files
pytest tests/test_auth_race_condition.py -v
pytest tests/test_error_handling.py -v
```

### Code Quality Commands  
```bash
# Format code (required before commits)
black .
isort .

# Lint code
flake8 .

# Type checking
mypy .

# Run all quality checks together
black . && isort . && flake8 . && mypy .
```

### Development Utilities
```bash
# Check git status
git status

# List project structure
ls -la
find . -name "*.py" | head -20

# Search for patterns in code  
grep -r "pattern" --include="*.py" .

# Find files by name
find . -name "*test*.py"
```

### Environment Testing
```bash
# Test API connection
python -c "from main import create_server_from_env; import asyncio; asyncio.run(create_server_from_env().utils_tools.validate_connection())"
```

## Darwin-Specific Notes
- Use standard Unix commands (ls, grep, find, cd)
- Python typically available as `python3` and `python`
- File paths use forward slashes
- Case-sensitive filesystem
- Use `./script.sh` for shell script execution