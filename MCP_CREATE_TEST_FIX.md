# MCP create_test Validation Fix

## Problem Summary

The `create_test` MCP tool was consistently failing with validation errors when AI assistants tried to use it, despite the exact same data working fine through direct API calls and import scripts.

## Root Cause

The issue was a **type annotation mismatch** in the MCP tool definition:

1. **FastMCP validates parameter types BEFORE the function executes**
2. The `steps` parameter was annotated as `Optional[List[Dict[str, str]]]`
3. AI assistants pass steps as a **JSON string** (e.g., `'[{"action": "...", "data": "", "result": "..."}]'`)
4. FastMCP rejected the string input because it didn't match the expected `List[Dict[str, str]]` type
5. The JSON parsing code (lines 361-366) never got a chance to run

## The Fix

Changed the type annotation in `main.py` (line 341) to accept both formats:

```python
# OLD - Only accepts Python lists
steps: Optional[List[Dict[str, str]]] = None,

# NEW - Accepts both JSON strings and Python lists  
steps: Optional[Union[str, List[Dict[str, str]]]] = None,
```

Also added `Union` to the imports:
```python
from typing import Dict, Any, List, Optional, Union
```

## Why This Works

1. FastMCP now allows both string and list inputs to pass validation
2. The existing JSON parsing logic (lines 361-366) converts strings to lists:
   ```python
   if steps is not None and isinstance(steps, str):
       import json
       try:
           steps = json.loads(steps)
       except json.JSONDecodeError as e:
           return {"error": f"Invalid JSON in steps parameter: {str(e)}", "type": "JSONDecodeError"}
   ```
3. Backward compatibility is maintained - direct Python calls with lists still work
4. AI assistants can continue passing JSON strings as they naturally do

## Verification

The fix has been implemented and tested. AI assistants can now successfully create tests with steps passed as JSON strings, while maintaining compatibility with Python list inputs.

## Lessons Learned

When building MCP tools, consider that:
- AI assistants may serialize complex data structures to JSON strings
- Parameter validation happens before your function code runs
- Type annotations should be flexible enough to handle different input formats
- Always include parsing/conversion logic for string inputs when expecting complex types