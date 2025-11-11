# Suggested Commands for Xray MCP Server Development

## Environment Setup Commands
```bash
# Run the comprehensive setup script (cross-platform)
./install-server.sh

# Manually activate virtual environment (after install-server.sh)
source venv/bin/activate

# Install dependencies manually
pip install -r requirements.txt

# Configure environment variables
cp .env.example .env
# Then edit .env with your Xray credentials
```

## Testing Commands
```bash
# Run all tests
pytest

# Run integration tests (requires Xray credentials in .env)
pytest tests/integration/

# Run specific test file
pytest tests/integration/test_auth_integration.py

# Run tests with verbose output
pytest -v

# Run tests with specific markers (if added)
pytest -m integration
```

## Documentation Commands
```bash
# Update Xray API documentation (from xray-docs/)
cd xray-docs/
python3 download_xray_docs_v2.py
```

## Darwin System Utilities
```bash
# File operations
ls -la                    # List files with details
find . -name "*.py"      # Find Python files
grep -r "pattern" src/   # Search in source code
cat filename.py          # Display file contents

# Git operations
git status               # Check repository status
git add .               # Stage all changes
git commit -m "message" # Commit changes
git push origin branch  # Push to remote
git log --oneline       # View commit history
```

## Development Workflow Commands
```bash
# 1. Setup environment
./install-server.sh
source venv/bin/activate

# 2. Make changes to code
# 3. Run tests
pytest

# 4. Run integration tests (optional, requires credentials)
pytest tests/integration/

# 5. Commit changes
git add .
git commit -m "descriptive message"
```

## Environment Variables Required
```bash
XRAY_CLIENT_ID=your_xray_client_id_here
XRAY_CLIENT_SECRET=your_xray_client_secret_here
XRAY_BASE_URL=https://xray.cloud.getxray.app  # Optional, defaults to cloud
```

## Project-Specific Notes
- No linting/formatting tools configured yet (pyproject.toml is minimal)
- Virtual environment is named `.xray-mcp_venv` by the install script
- Integration tests require real Xray API credentials
- Darwin system commands work on macOS (which this project is developed on)