# Cursor MCP Integration Debug Guide

## Problem Summary

**Issue:** Cursor can read MCP resources (`xray://documentation`, `xray://capabilities`) but cannot see or invoke MCP tools (`xray_test`, `test_ping`).

**Evidence from Claude's thoughts in Cursor:**
- ✅ Resources work: Claude successfully fetches documentation
- ❌ Tools don't work: Claude reports "I don't have access to Xray MCP server tools"
- Claude expects tools named like `mcp_xray_xray_test` but sees nothing

## Changes Made

### 1. Comprehensive Logging (`main.py` and `src/server.py`)

Added extensive logging to track:
- Server startup sequence
- Environment variable detection
- Authentication initialization
- Tool registration (both `xray_test` and `test_ping`)
- Resource and prompt registration
- Any errors during initialization

**Log file location:** `./xray_mcp_server.log`

### 2. Simple Test Tool (`test_ping`)

Added a diagnostic tool that:
- Requires NO authentication (eliminates auth as a variable)
- Has minimal complexity (just echoes back a message)
- Logs every call for verification

**Purpose:** If Claude can see `test_ping` but not `xray_test`, the issue is with the complex tool. If Claude can't see either tool, it's a fundamental tool registration/exposure issue.

### 3. Enhanced Error Handling

- Authentication errors in `xray_test` are now caught and returned as proper error responses instead of crashing
- All initialization steps wrapped in try/catch with detailed logging

## How to Diagnose

### Step 1: Restart Cursor and Check Logs

1. **Quit Cursor completely** (Cmd+Q on Mac, not just close window)
2. **Delete old log file:**
   ```bash
   rm /Users/douglas.mason/Documents/GitHub/xray-mcp.worktrees/groundup-rebuild/xray_mcp_server.log
   ```
3. **Start Cursor**
4. **Wait 10 seconds** for MCP servers to initialize
5. **Check the log file:**
   ```bash
   tail -100 /Users/douglas.mason/Documents/GitHub/xray-mcp.worktrees/groundup-rebuild/xray_mcp_server.log
   ```

### Step 2: Analyze Log Output

Look for these key indicators:

**✅ Success Indicators:**
```
Server configuration complete!
Total tools registered: 2
  ✓ Tool: xray_test
  ✓ Tool: test_ping
Total resources registered: 3
  ✓ Resource: xray://documentation
  ✓ Resource: xray://capabilities
  ✓ Resource: xray://project/{project_key}/tests
```

**❌ Failure Indicators:**
```
Failed to initialize XrayAuth: ...
Authentication failed: ...
XRAY_CLIENT_ID present: False
XRAY_CLIENT_SECRET present: False
```

### Step 3: Test in Cursor

Try these prompts in Cursor to test different scenarios:

**Test 1: Can Claude see tools at all?**
```
List all available MCP tools from the xray server
```

**Test 2: Can Claude use the simple test tool?**
```
Use the test_ping tool with message "Hello World"
```

**Test 3: Can Claude use the xray tool?**
```
Use the xray_test tool to list tests in project MLBMOB
```

### Step 4: Check Cursor Logs

Cursor may have its own logs showing MCP communication issues:

```bash
# Mac/Linux
tail -f ~/Library/Logs/Cursor/*.log | grep -i mcp

# Look for errors related to:
# - Tool invocation failures
# - Protocol errors
# - Timeout issues
```

## Diagnostic Scenarios

### Scenario A: Server Never Starts
**Symptoms:** Log file is empty or shows early errors
**Likely Causes:**
- Python environment issues
- Missing dependencies
- Path problems in mcp.json

**Fix:**
1. Test server manually:
   ```bash
   /Users/douglas.mason/Documents/GitHub/xray-mcp.worktrees/groundup-rebuild/.xray-mcp_venv/bin/python \
   /Users/douglas.mason/Documents/GitHub/xray-mcp.worktrees/groundup-rebuild/main.py
   ```
2. Check for errors in terminal output
3. Verify virtual environment is intact

### Scenario B: Server Starts But Tools Not Registered
**Symptoms:** Log shows server startup but tool count is 0
**Likely Causes:**
- FastMCP version compatibility issue
- Tool decorator not working
- Python async issues

**Fix:**
1. Check FastMCP version: `pip list | grep fastmcp`
2. Update FastMCP: `pip install --upgrade fastmcp`
3. Test with FastMCP CLI (see below)

### Scenario C: Tools Registered But Cursor Can't See Them
**Symptoms:** Log shows "Total tools registered: 2" but Cursor reports no tools
**Likely Causes:**
- Cursor MCP protocol compatibility
- Tool metadata format issues
- Cursor-specific requirements not met

**Fix:**
1. Compare with working MCP servers (sequential-thinking works in your setup)
2. Check Cursor MCP documentation
3. May need to adjust tool registration format

### Scenario D: Authentication Fails During Tool Call
**Symptoms:** Log shows tool registered, but every call fails with auth error
**Likely Causes:**
- .env file not accessible to Cursor-launched process
- Environment variables not loaded
- Xray API credentials invalid/expired

**Fix:**
1. Verify .env file location:
   ```bash
   cat /Users/douglas.mason/Documents/GitHub/xray-mcp.worktrees/groundup-rebuild/.env
   ```
2. Test authentication manually:
   ```bash
   cd /Users/douglas.mason/Documents/GitHub/xray-mcp.worktrees/groundup-rebuild
   source .xray-mcp_venv/bin/activate
   python -c "from src.auth import XrayAuth; import os; from dotenv import load_dotenv; load_dotenv(); auth = XrayAuth(os.getenv('XRAY_CLIENT_ID'), os.getenv('XRAY_CLIENT_SECRET'), os.getenv('XRAY_BASE_URL')); import asyncio; asyncio.run(auth.authenticate()); print('Success!')"
   ```

## Independent Testing (FastMCP CLI)

Test the server outside of Cursor to isolate issues:

```bash
cd /Users/douglas.mason/Documents/GitHub/xray-mcp.worktrees/groundup-rebuild

# Activate virtual environment
source .xray-mcp_venv/bin/activate

# Run with FastMCP CLI
fastmcp run main.py:create_mcp

# Or run in dev mode
fastmcp dev main.py:create_mcp
```

This will:
- Start the server in a controlled environment
- Show you exactly what tools/resources are registered
- Let you test tool invocation directly
- Eliminate Cursor as a variable

## What to Share When Asking for Help

If issues persist, share:

1. **Last 200 lines of log file:**
   ```bash
   tail -200 xray_mcp_server.log
   ```

2. **Cursor MCP config:**
   ```bash
   cat ~/.cursor/mcp.json
   ```

3. **FastMCP version:**
   ```bash
   pip list | grep fastmcp
   ```

4. **Test results:**
   - Can Claude see resources? (yes/no)
   - Can Claude see tools? (yes/no)
   - Can Claude call `test_ping`? (yes/no + error message)
   - Can Claude call `xray_test`? (yes/no + error message)

5. **Comparison with working server:**
   - Does `sequential-thinking` MCP server work? (yes/no)
   - What does Claude see from that server?

## Next Steps Based on Findings

**If tools ARE registered but Cursor can't see them:**
→ This is a Cursor-specific MCP protocol issue. We need to:
  1. Study how sequential-thinking server registers tools
  2. Compare tool metadata formats
  3. Adjust our registration to match Cursor's expectations

**If tools are NOT being registered:**
→ This is a FastMCP or server initialization issue. We need to:
  1. Update FastMCP to latest version
  2. Check Python/async compatibility
  3. Simplify tool registration further

**If authentication is failing:**
→ This is an environment/credential issue. We need to:
  1. Fix .env loading for Cursor-launched processes
  2. Verify Xray API credentials are valid
  3. Consider alternative auth approaches

## Immediate Action Items

1. ✅ Follow "Step 1: Restart Cursor and Check Logs" above
2. ✅ Share the log file contents (last 200 lines)
3. ✅ Test the three Cursor prompts from Step 3
4. ✅ Report what Claude says in response to each prompt

This will tell us exactly where the problem is and what to fix next.
