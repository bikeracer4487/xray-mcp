# Xray MCP Test Creation - Debug Log

## Summary
Successfully created a new Xray test in the FRAMED project with formatted description. Test was created with key `FRAMED-1670` but encountered some retrieval issues with certain API methods.

## Test Details Created
- **Project**: FRAMED
- **Test Key**: FRAMED-1670
- **Issue ID**: 1162822
- **Title**: "XRAY MCP TEST"
- **Test Type**: Generic
- **Status**: To Do

---

## Request/Response Log

### 1. ✅ CREATE TEST - SUCCESS
**Request**: `xray:create_test`
```json
{
  "project_key": "FRAMED",
  "summary": "XRAY MCP TEST", 
  "test_type": "Generic",
  "description": "## Test Description\n\nThis is a **test description** with *various formatting* to verify that the Xray MCP handles formatted text correctly.\n\n### Key Features to Test:\n- **Bold text** formatting\n- *Italic text* formatting  \n- `Code snippets` and inline code\n- [Links](https://example.com) functionality\n- Lists and bullet points\n\n### Test Scenarios:\n1. First scenario with numbered list\n2. Second scenario with **bold emphasis**\n3. Third scenario with *italic emphasis*\n\n#### Code Block Example:\n```javascript\nfunction testExample() {\n    console.log(\"Testing code block formatting\");\n    return true;\n}\n```\n\n### Additional Notes:\n> This is a blockquote to test quote formatting\n> \n> Multiple lines in blockquote\n\n**Important**: This test verifies that markdown formatting is preserved when submitted through the Xray MCP integration.\n\n---\n\n*End of test description*"
}
```

**Response**: ✅ SUCCESS
```json
{
  "test": {
    "issueId": "1162822",
    "testType": {
      "name": "Generic"
    },
    "unstructured": null,
    "jira": {
      "key": "FRAMED-1670",
      "summary": "XRAY MCP TEST"
    }
  },
  "warnings": []
}
```

### 2. ❌ GET TEST - ERROR
**Request**: `xray:get_test`
```json
{
  "issue_id": "FRAMED-1670"
}
```

**Response**: ❌ ERROR
```json
{
  "error": "Failed to retrieve test FRAMED-1670",
  "type": "GraphQLError"
}
```

### 3. ❌ GET EXPANDED TEST - ERROR  
**Request**: `xray:get_expanded_test`
```json
{
  "issue_id": "FRAMED-1670"
}
```

**Response**: ❌ ERROR
```json
{
  "error": "Failed to retrieve expanded test FRAMED-1670",
  "type": "GraphQLError"
}
```

### 4. ❌ GET TESTS WITH JQL - VALIDATION ERROR
**Request**: `xray:get_tests`
```json
{
  "jql": "project = FRAMED AND summary ~ \"XRAY MCP TEST\"",
  "limit": 10
}
```

**Response**: ❌ ERROR
```json
{
  "error": "Unknown or disallowed field: FRAMED",
  "type": "ValidationError"
}
```

### 5. ✅ GET TESTS (GENERAL) - SUCCESS
**Request**: `xray:get_tests`
```json
{
  "limit": 5
}
```

**Response**: ✅ SUCCESS (Returned 5 tests from different projects - WSTE project tests)

### 6. ✅ VALIDATE CONNECTION - SUCCESS
**Request**: `xray:validate_connection`

**Response**: ✅ SUCCESS
```json
{
  "status": "connected",
  "message": "Successfully connected to Xray API",
  "authenticated": true
}
```

### 7. ✅ JQL QUERY FOR SPECIFIC TEST - SUCCESS
**Request**: `xray:execute_jql_query`
```json
{
  "entity_type": "test",
  "jql": "key = \"FRAMED-1670\"",
  "limit": 1
}
```

**Response**: ✅ SUCCESS
```json
{
  "total": 1,
  "start": 0,
  "limit": 1,
  "results": [
    {
      "issueId": "1162822",
      "testType": {
        "name": "Generic"
      },
      "jira": {
        "key": "FRAMED-1670",
        "summary": "XRAY MCP TEST",
        "assignee": null,
        "status": {
          "self": "https://baseball.atlassian.net/rest/api/2/status/10018",
          "description": "A topic is an idea that anyone can bring to the table.",
          "iconUrl": "https://baseball.atlassian.net/images/icons/subtask.gif",
          "name": "To Do",
          "id": "10018",
          "statusCategory": {
            "self": "https://baseball.atlassian.net/rest/api/2/statuscategory/2",
            "id": 2,
            "key": "new",
            "colorName": "blue-gray",
            "name": "To Do"
          }
        }
      }
    }
  ]
}
```

---

## Issues Encountered

### 1. GraphQL Errors on Test Retrieval
- **Methods Affected**: `get_test` and `get_expanded_test`
- **Error Type**: GraphQLError
- **Possible Causes**: 
  - Permissions issue
  - Test not fully indexed yet
  - API endpoint limitations
- **Impact**: Cannot retrieve full test details including description

### 2. JQL Validation Error
- **Method Affected**: `get_tests` with project filter
- **Error Type**: ValidationError
- **Issue**: "Unknown or disallowed field: FRAMED"
- **Possible Cause**: Project key validation or permissions
- **Workaround**: Use `execute_jql_query` instead

### 3. Missing Description in Query Results
- **Issue**: The formatted description text is not returned in the JQL query results
- **Possible Causes**: 
  - API limitation in what fields are returned
  - Description stored differently than expected
  - Need different query parameters

---

## Successful Outcomes

✅ **Test Creation**: Successfully created test FRAMED-1670 with formatted description
✅ **Connection Validation**: API connection and authentication working properly  
✅ **Test Location**: Successfully found the created test using JQL query
✅ **Basic Test Info**: Retrieved test key, summary, issue ID, and status

---

## Recommendations for Further Testing

1. **Test Description Verification**: Try alternative methods to retrieve the full test description to verify formatting preservation
2. **Permission Review**: Check if the GraphQL errors are permission-related
3. **API Method Comparison**: Test different retrieval methods to find the most reliable approach
4. **Project Access**: Verify full access permissions to FRAMED project
5. **Formatting Verification**: Access the test through Jira UI to manually verify description formatting was preserved
