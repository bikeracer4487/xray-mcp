# Xray MCP E2E Tests

Comprehensive end-to-end testing for the Xray MCP server combining MCP contract testing with Playwright visual verification.

## Test Structure

### Contract Tests (`contracts/`)
Validate MCP tool call arguments and Xray GraphQL API payloads:
- Test management operations (create, update, delete tests)
- Test execution lifecycle (create executions, add tests, update results)  
- Test organization (plans, sets, folders)
- Gherkin scenario management
- Coverage and status queries

### Visual Tests (`visual/`)
Use Playwright to verify test content renders correctly in Xray UI:
- Test display with all fields and metadata
- Manual test steps table formatting
- Gherkin scenario syntax highlighting
- Execution status indicators and history
- Test repository folder structure

### Integration Tests (`integration/`)
End-to-end workflow validation:
- Complete test lifecycle (create → execute → report)
- Bulk operations and batch imports
- Cross-linking between tests, executions, plans
- Complex JQL query scenarios
- Error handling and recovery

## Setup

1. Install Python dependencies:
```bash
pip install -r requirements.txt
```

2. Install Node.js dependencies for Playwright:
```bash
npm install
npx playwright install
```

3. Configure environment variables:
```bash
cp .env.example .env
# Edit .env with your Xray credentials and test configuration
```

## Running Tests

```bash
# Run all E2E tests
pytest tests/e2e/ -v

# Run only contract tests
pytest tests/e2e/contracts/ -v

# Run only visual tests
pytest tests/e2e/visual/ -v --headed

# Run with different markers
pytest tests/e2e/ -m "contract" -v
pytest tests/e2e/ -m "visual" -v
pytest tests/e2e/ -m "integration" -v
```

## Test Data Management

Tests use unique naming with timestamps and automatically clean up created resources:
- Tests are tracked during creation
- Cleanup happens in test teardown
- Failed test artifacts are preserved for debugging

## Visual Test Screenshots

Visual tests capture screenshots for:
- Test verification evidence
- Failure debugging
- Regression comparison

Screenshots are saved to `tests/e2e/.artifacts/screenshots/`

## Configuration

Key environment variables:
- `XRAY_CLIENT_ID`: Xray API client ID
- `XRAY_CLIENT_SECRET`: Xray API client secret
- `XRAY_BASE_URL`: Xray instance URL (defaults to cloud)
- `JIRA_BASE_URL`: Base Jira URL for UI navigation
- `TEST_PROJECT`: Jira project key for test creation
- `BROWSER_HEADLESS`: Run visual tests in headless mode (default: true)

See `.env.example` for full configuration options.