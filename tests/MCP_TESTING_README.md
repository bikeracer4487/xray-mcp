# MCP Protocol Testing Framework

This comprehensive testing framework validates the Xray MCP server as an actual MCP (Model Context Protocol) server, testing the same communication patterns that real MCP clients like Claude Desktop and Cursor use.

## 🎯 Problem Solved

**Previous tests** imported the server directly and called internal functions, which **missed protocol-level issues** that only occur when clients communicate via JSON-RPC over stdio.

**This framework** tests the server exactly how MCP clients use it:
- Spawns server as subprocess
- Communicates via JSON-RPC 2.0 over stdio
- Tests full protocol lifecycle (initialize → list_tools → call_tool)
- Validates all responses against MCP specification

## 🏗️ Framework Architecture

```
tests/
├── mcp_protocol/           # Core protocol tests
│   ├── test_initialization.py      # Server startup & handshake
│   ├── test_tool_discovery.py      # Tools listing & schemas
│   ├── test_tool_invocation.py     # Tool execution via JSON-RPC
│   ├── test_error_handling.py      # Error scenarios & edge cases
│   ├── test_resource_access.py     # Resource operations
│   └── test_prompts.py             # Prompt functionality
├── mcp_integration/        # Integration tests
│   ├── test_with_mock_api.py       # Deterministic testing with mocks
│   ├── test_subprocess_spawning.py # Process lifecycle management
│   └── test_client_compatibility.py # FastMCP Client integration
├── mcp_compliance/         # Specification compliance
│   ├── test_mcp_spec.py            # MCP protocol compliance
│   └── test_jsonrpc_spec.py        # JSON-RPC 2.0 compliance
├── conftest.py             # Test fixtures & utilities
├── run_mcp_tests.py        # Test runner script
└── MCP_TESTING_README.md   # This documentation
```

## 🚀 Quick Start

### Run All Tests
```bash
python tests/run_mcp_tests.py
```

### Run Specific Test Categories
```bash
# Protocol tests only
python tests/run_mcp_tests.py --category protocol

# Integration tests only
python tests/run_mcp_tests.py --category integration

# Compliance tests only
python tests/run_mcp_tests.py --category compliance

# Quick smoke test
python tests/run_mcp_tests.py --smoke
```

### Run with Options
```bash
# Verbose output with fail-fast
python tests/run_mcp_tests.py --verbose --fail-fast

# Run tests in parallel
python tests/run_mcp_tests.py --parallel

# Generate coverage report
python tests/run_mcp_tests.py --coverage
```

## 🧪 Test Categories

### 1. Protocol Tests (`mcp_protocol/`)
Tests core MCP protocol functionality:

- **Initialization**: Server startup, handshake, protocol negotiation
- **Tool Discovery**: Tool listing, schema validation, parameter checking
- **Tool Invocation**: Actual tool calls via JSON-RPC, response validation
- **Error Handling**: Parameter validation, authentication failures, API errors
- **Resources & Prompts**: Static content and guided workflows

### 2. Integration Tests (`mcp_integration/`)
Tests realistic usage scenarios:

- **Mock API Testing**: Deterministic tests without hitting live Xray API
- **Subprocess Management**: Process lifecycle, startup/shutdown, recovery
- **Client Compatibility**: FastMCP Client integration patterns

### 3. Compliance Tests (`mcp_compliance/`)
Ensures specification adherence:

- **MCP Specification**: Server info, capabilities, content types, authentication flows
- **JSON-RPC 2.0**: Request/response structure, error codes, ID handling, notifications

## 🔧 Key Features

### Real Protocol Testing
- ✅ Spawns server as subprocess (like real clients)
- ✅ Communicates via stdio using JSON-RPC 2.0
- ✅ Tests full initialization handshake
- ✅ Validates tool discovery and execution
- ✅ Proper error response handling

### Deterministic Testing
- ✅ Mock Xray API responses for consistent results
- ✅ No dependency on live API credentials
- ✅ Comprehensive test scenarios and edge cases
- ✅ Performance and load testing

### Specification Compliance
- ✅ MCP protocol compliance validation
- ✅ JSON-RPC 2.0 specification adherence
- ✅ Tool schema validation
- ✅ Error code and message validation

### Developer Experience
- ✅ Clear test categorization with pytest markers
- ✅ Detailed failure reporting
- ✅ Coverage reporting with HTML output
- ✅ Parallel test execution support
- ✅ Comprehensive documentation

## 📊 Test Markers

Use pytest markers to run specific test types:

```bash
# Protocol communication tests
pytest -m mcp_protocol

# FastMCP Client tests
pytest -m mcp_client

# Subprocess communication tests
pytest -m mcp_subprocess

# Performance tests
pytest -m performance

# Error handling tests
pytest -m error_handling

# Compliance tests
pytest -m mcp_compliance

# JSON-RPC compliance
pytest -m jsonrpc

# Integration tests
pytest -m mcp_integration

# Slow tests (for CI exclusion)
pytest -m "not slow"
```

## 🛠️ Configuration

### Environment Variables
Tests use these environment variables (with safe defaults):

```bash
# For live API testing (optional)
XRAY_CLIENT_ID=your_client_id
XRAY_CLIENT_SECRET=your_client_secret
XRAY_BASE_URL=https://xray.cloud.getxray.app
XRAY_PROJECT_KEY=DEMO

# For mock testing (no credentials needed)
# Tests automatically use mocks when credentials unavailable
```

### Test Configuration
Key configuration in `conftest.py`:

- **Server timeout**: 30 seconds for subprocess startup
- **Request timeout**: 60 seconds for slow operations
- **Mock responses**: Comprehensive fixtures for all entity types
- **Resource cleanup**: Automatic cleanup of test resources

## 🔍 What This Framework Catches

### Issues Missed by Direct Function Testing:
1. **JSON-RPC parsing errors** - Malformed messages, wrong content types
2. **Protocol handshake failures** - Missing initialize, wrong capabilities
3. **Tool discovery issues** - Invalid schemas, missing descriptions
4. **Parameter serialization problems** - Array formatting, Unicode handling
5. **Error response format issues** - Wrong error codes, missing fields
6. **Process communication failures** - Stdout/stderr mixing, connection drops
7. **Authentication timing issues** - When auth happens in the flow
8. **Resource cleanup problems** - Process zombies, file handle leaks

### Real-World Scenarios Tested:
- Multiple concurrent clients
- Rapid request sequences
- Large message handling
- Unicode character support
- Network timeout simulation
- Authentication failure recovery
- Graceful shutdown handling

## 📈 Running in CI/CD

### GitHub Actions Example:
```yaml
- name: Run MCP Protocol Tests
  run: |
    python tests/run_mcp_tests.py --category protocol --fail-fast

- name: Run Integration Tests
  run: |
    python tests/run_mcp_tests.py --category integration

- name: Compliance Check
  run: |
    python tests/run_mcp_tests.py --compliance
```

### Performance Testing:
```yaml
- name: Performance Tests
  run: |
    pytest -m performance --tb=short
```

## 🐛 Debugging Failed Tests

### Common Issues and Solutions:

1. **Server startup timeout**
   ```bash
   # Check server starts manually
   python main.py
   ```

2. **JSON-RPC communication issues**
   ```bash
   # Test with verbose output
   pytest tests/mcp_protocol/test_initialization.py -v -s
   ```

3. **Authentication errors in live tests**
   ```bash
   # Check environment variables
   echo $XRAY_CLIENT_ID

   # Run with mocks only
   pytest -m "not slow" tests/mcp_integration/test_with_mock_api.py
   ```

4. **Permission issues**
   ```bash
   # Make sure script is executable
   chmod +x tests/run_mcp_tests.py
   ```

## 🎯 Best Practices

### Writing New Tests:
1. **Use appropriate base class**: Inherit from `BaseMCPTest`
2. **Add proper markers**: Use `@pytest.mark.mcp_protocol` etc.
3. **Mock external APIs**: Use fixtures from `conftest.py`
4. **Test error conditions**: Don't just test happy path
5. **Follow naming conventions**: `test_<functionality>_<scenario>`

### Test Organization:
- **Protocol tests**: Focus on MCP spec compliance
- **Integration tests**: Test realistic workflows
- **Compliance tests**: Validate against specifications
- **Mock extensively**: Avoid dependencies on live APIs

## 🔄 Continuous Improvement

This framework enables confident development by catching issues that would only surface when real MCP clients connect to your server. As the MCP ecosystem evolves, these tests ensure your server remains compatible.

### Future Enhancements:
- [ ] HTTP transport testing (in addition to stdio)
- [ ] Performance benchmarking and regression detection
- [ ] Cross-platform compatibility testing
- [ ] Client compatibility matrix testing
- [ ] Automated compliance reporting

---

**Remember**: These tests validate that your MCP server works correctly with real MCP clients, not just that your internal functions work in isolation. This approach catches the subtle but critical issues that only emerge during actual client-server communication.