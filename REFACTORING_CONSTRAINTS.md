# Refactoring Constraints for Xray MCP Server

## ⚠️ CRITICAL: FastMCP Tool Registration Limitations

**Date**: 2025-08-05  
**Research Finding**: The existing "refactored" abstraction layer violates FastMCP's required patterns and would break the MCP server.

## FastMCP Requirements

### ✅ **Supported Pattern (Current main.py)**
```python
# CORRECT: Direct decorator registration at function definition time
@self.mcp.tool()
async def get_test(issue_id: str) -> Dict[str, Any]:
    """Get test by issue ID"""
    try:
        return await self.test_tools.get_test(issue_id)
    except Exception as e:
        return {"error": str(e), "type": type(e).__name__}
```

### ❌ **Unsupported Pattern (Attempted Refactoring)**
```python
# INCORRECT: Dynamic/factory registration at runtime
class ToolFactory:
    def register_tool_class(self, tool_class):
        # This CANNOT work - decorators must be applied at definition time
        for method in inspect.getmembers(tool_class):
            self.mcp.tool()(method)  # ❌ FastMCP doesn't support this
```

## Key Constraints

1. **Decorator-Only Registration**: FastMCP requires `@mcp.tool()` at function definition time
2. **No Reflection API**: No documented way to programmatically register methods as tools  
3. **Import-Time Binding**: Tools are bound when decorators are processed, not at runtime
4. **No Factory Pattern Support**: Cannot use factory or registry patterns for tool registration

## Files to Remove

The following files contain non-functional patterns and should be removed:
- `main_refactored.py` - Uses unsupported ToolFactory pattern
- `abstractions/factory.py` - ToolFactory that cannot work with FastMCP
- `tools/tests_refactored.py` - Depends on factory pattern
- `abstractions/` directory - Entire abstraction layer is incompatible

## Correct Refactoring Approach

Instead of factory patterns, focus on:

1. **Code Organization**: Group related tools into sections with clear comments
2. **Helper Functions**: Extract common logic into private methods
3. **Configuration**: Move repetitive parameters to constants
4. **Documentation**: Improve docstrings and type hints
5. **Error Handling**: Standardize but don't abstract the try/catch pattern

## The "Verbose" Pattern is Correct

The 1,386-line `main.py` with repetitive `@self.mcp.tool()` decorators is **not** poorly designed - it's following FastMCP's required architecture. The repetition is necessary for proper MCP tool registration.

## Research Sources

- FastMCP Documentation: https://gofastmcp.com/servers/tools
- FastMCP GitHub: https://github.com/jlowin/fastmcp
- MCP Python SDK: https://github.com/modelcontextprotocol/python-sdk

## Action Items

- [x] Document constraints
- [ ] Remove incompatible refactored files
- [ ] Update CODE_REVIEW_FINDINGS.md to reflect correct assessment
- [ ] Focus future refactoring on FastMCP-compatible patterns only