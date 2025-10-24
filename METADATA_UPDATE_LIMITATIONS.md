# Metadata Update Limitations and Workarounds

This document addresses the critical QA finding about metadata update limitations in the Xray MCP server and provides practical workarounds for common scenarios.

## 🚨 **Critical Understanding**

**The Xray GraphQL API has intentional limitations on what metadata can be updated.** This is not a bug in our MCP server, but rather constraints in Xray's API design.

---

## 📋 **What CAN Be Updated**

### ✅ **Test Content Updates - WORKS**
```python
# Update Cucumber test Gherkin content
xray_test(
    entity="test",
    action="update_content",
    issue_id="1192649",
    gherkin="""
Feature: Updated feature
  Scenario: Updated scenario
    Given I have updated content
    When I save the test
    Then the content should be updated
"""
)
```

### ✅ **Test Type Changes - WORKS**
```python
# Change test type (Manual → Generic, etc.)
xray_test(
    entity="test",
    action="update_type",
    issue_id="1192649",
    test_type="Generic"
)
```

### ✅ **Test Run Status Updates - WORKS**
```python
# Update test run status and comments
xray_test(
    entity="test_run",
    action="update_status",
    id="run_id_here",
    status="PASS",
    comment="Test completed successfully"
)
```

### ✅ **Association Management - WORKS**
```python
# Add/remove tests from executions and plans
xray_test(entity="test_execution", action="add_tests", issue_id="1192649", test_issue_ids=["1192650"])
xray_test(entity="test_plan", action="remove_tests", issue_id="1192649", test_issue_ids=["1192650"])
```

---

## ❌ **What CANNOT Be Updated (API Limitations)**

### **1. Manual Test Steps (Bulk Updates)**

**❌ LIMITATION:**
```python
# This does NOT work - cannot bulk update manual test steps
xray_test(
    entity="test",
    action="update_content",
    issue_id="1192649",
    steps=[
        {"action": "Updated step 1", "data": "New data", "result": "New result"},
        {"action": "Updated step 2", "data": "New data", "result": "New result"}
    ]
)
```

**✅ WORKAROUND:**
```python
# Option 1: Delete and recreate the test
# 1. Get existing test details
existing_test = xray_test(entity="test", action="get", issue_id="1192649")

# 2. Delete the test
xray_test(entity="test", action="delete", issue_id="1192649")

# 3. Create new test with updated steps
new_test = xray_test(
    entity="test",
    action="create",
    project_key="DEMO",
    summary=existing_test['data']['summary'],
    test_type="Manual",
    steps=[
        {"action": "Updated step 1", "data": "New data", "result": "New result"},
        {"action": "Updated step 2", "data": "New data", "result": "New result"}
    ]
)

# Option 2: Convert to Cucumber format
xray_test(
    entity="test",
    action="update_type",
    issue_id="1192649",
    test_type="Cucumber"
)
# Then update Gherkin content (which DOES work)
xray_test(
    entity="test",
    action="update_content",
    issue_id="1192649",
    gherkin="Feature: Updated test..."
)
```

### **2. JIRA Custom Fields**

**❌ LIMITATION:**
```python
# Cannot update JIRA custom fields through GraphQL
xray_test(
    entity="test",
    action="update",
    issue_id="1192649",
    custom_field_12345="New value"  # Not supported
)
```

**✅ WORKAROUND:**
```python
# Use JIRA REST API directly (separate integration required)
import requests

jira_response = requests.put(
    f"https://your-instance.atlassian.net/rest/api/3/issue/{jira_key}",
    headers={"Authorization": "Bearer your-jira-token"},
    json={
        "fields": {
            "customfield_12345": "New value"
        }
    }
)
```

### **3. Test Summary and Description**

**❌ LIMITATION:**
```python
# Cannot update basic JIRA fields like summary through Xray GraphQL
xray_test(
    entity="test",
    action="update",
    issue_id="1192649",
    summary="New test summary"  # Not supported in Xray GraphQL
)
```

**✅ WORKAROUND:**
```python
# Option 1: Use JIRA REST API (recommended)
# See custom fields example above

# Option 2: Delete and recreate (loses history)
# Get existing test details, delete, recreate with new summary
```

---

## 🎯 **Best Practices for Metadata Updates**

### **1. Plan Your Test Structure**
- **Design tests with minimal need for bulk step updates**
- **Use Cucumber format for tests that change frequently** (Gherkin content CAN be updated)
- **Use Generic tests for simple pass/fail scenarios**

### **2. Update Strategy by Test Type**

#### **For Cucumber Tests - ✅ Flexible**
```python
# Easy to update - just change the Gherkin
updated_gherkin = """
Feature: User Login
  Scenario: Successful login with new requirements
    Given I am on the updated login page
    When I enter valid credentials with 2FA
    Then I should be logged in successfully
"""

xray_test(
    entity="test",
    action="update_content",
    issue_id="1192649",
    gherkin=updated_gherkin
)
```

#### **For Manual Tests - ⚠️ Limited**
```python
# If you need frequent step updates, consider:
# 1. Convert to Cucumber format first
xray_test(entity="test", action="update_type", issue_id="1192649", test_type="Cucumber")

# 2. Or use description field for detailed steps (updateable via JIRA REST API)
```

### **3. Integration Patterns**

#### **Hybrid Approach - Xray MCP + JIRA REST**
```python
# Use Xray MCP for test management operations
test_result = xray_test(entity="test", action="create", ...)

# Use JIRA REST API for metadata updates
jira_update = update_jira_fields(
    issue_key=test_result['data']['issueKey'],
    fields={"summary": "Updated summary", "customfield_123": "value"}
)
```

---

## 📊 **Update Capability Matrix**

| Operation | Xray GraphQL (MCP) | JIRA REST API | Workaround Available |
|-----------|-------------------|---------------|---------------------|
| Test Type | ✅ | ✅ | N/A |
| Gherkin Content | ✅ | ✅ | N/A |
| Manual Steps (Bulk) | ❌ | ❌ | Delete/Recreate |
| Test Summary | ❌ | ✅ | Use JIRA REST |
| Description | ❌ | ✅ | Use JIRA REST |
| Custom Fields | ❌ | ✅ | Use JIRA REST |
| Labels | ❌ | ✅ | Use JIRA REST |
| Priority | ❌ | ✅ | Use JIRA REST |
| Test Run Status | ✅ | ✅ | N/A |
| Test Associations | ✅ | ❌ | N/A |

---

## 🔄 **Migration Strategies**

### **Convert Manual to Cucumber Tests**
```python
# Step 1: Get existing manual test
manual_test = xray_test(entity="test", action="get", issue_id="1192649")

# Step 2: Convert steps to Gherkin format
steps = manual_test['data']['steps']
gherkin = convert_steps_to_gherkin(steps)  # Your conversion logic

# Step 3: Update to Cucumber type
xray_test(entity="test", action="update_type", issue_id="1192649", test_type="Cucumber")

# Step 4: Set Gherkin content
xray_test(entity="test", action="update_content", issue_id="1192649", gherkin=gherkin)
```

### **Bulk Test Updates**
```python
# For multiple tests needing updates
test_ids = ["1192649", "1192650", "1192651"]

for test_id in test_ids:
    # Get existing test
    existing = xray_test(entity="test", action="get", issue_id=test_id)

    # Update what's possible through MCP
    if existing['data']['testType'] != 'Cucumber':
        xray_test(entity="test", action="update_type", issue_id=test_id, test_type="Cucumber")

    # Update metadata through JIRA REST API
    update_jira_metadata(existing['data']['issueKey'], new_metadata)

    # Update test content
    xray_test(entity="test", action="update_content", issue_id=test_id, gherkin=new_gherkin)
```

---

## ⚠️ **Important Considerations**

1. **Data Loss Risk**: Delete/recreate operations lose test history and comments
2. **API Rate Limits**: JIRA REST API has different rate limits than GraphQL
3. **Permission Requirements**: JIRA REST API may require different permissions
4. **Consistency**: Ensure updates through multiple APIs maintain data consistency

---

## 🎯 **Summary**

The Xray MCP server provides excellent coverage for test management operations, but metadata updates are intentionally limited by Xray's GraphQL API design. For comprehensive metadata management:

1. **Use Xray MCP for**: Test content, types, associations, run status
2. **Use JIRA REST API for**: Summaries, descriptions, custom fields, labels
3. **Consider test design**: Choose Cucumber format for frequently changing tests
4. **Plan workarounds**: Delete/recreate for major step changes

**This is not a limitation of our MCP server, but an architectural decision by Xray to separate test-specific operations (GraphQL) from general issue operations (REST API).**