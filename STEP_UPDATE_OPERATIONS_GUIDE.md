# Step Update Operations Guide

This guide provides comprehensive examples and best practices for working with test steps in the Xray MCP server, addressing the QA finding about step update limitations.

## 🎯 **Key Understanding**

**Manual test steps cannot be updated in bulk through Xray GraphQL API.** This is an API design limitation, not a server bug. However, there are effective workarounds.

---

## 📋 **Step Operations by Test Type**

### **1. Manual Tests - LIMITED UPDATE CAPABILITY**

#### **✅ Creating Manual Tests with Steps**
```python
# WORKS: Create manual test with initial steps
result = xray_test(
    entity="test",
    action="create",
    project_key="DEMO",
    summary="User Login Test",
    test_type="Manual",
    description="Test user authentication workflow",
    steps=[
        {
            "action": "Navigate to login page",
            "data": "URL: https://app.example.com/login",
            "result": "Login page displays with username and password fields"
        },
        {
            "action": "Enter valid credentials",
            "data": "Username: testuser@example.com, Password: ValidPass123!",
            "result": "Credentials are accepted and user is logged in"
        },
        {
            "action": "Verify dashboard access",
            "data": "Navigate to dashboard",
            "result": "User dashboard displays with welcome message"
        }
    ]
)
```

#### **❌ Updating Manual Test Steps (NOT SUPPORTED)**
```python
# DOES NOT WORK: Cannot bulk update manual test steps
result = xray_test(
    entity="test",
    action="update_content",
    issue_id="1192649",
    steps=[  # This will be ignored with warning
        {
            "action": "Updated step 1",
            "data": "New data",
            "result": "New expected result"
        }
    ]
)
# Result: Warning message about step updates requiring individual operations
```

#### **✅ Workarounds for Manual Test Step Updates**

**Option 1: Delete and Recreate (Recommended for major changes)**
```python
# 1. Get existing test details
existing_test = xray_test(
    entity="test",
    action="get",
    issue_id="1192649"
)

# 2. Extract current data
current_summary = existing_test['data']['summary']
current_description = existing_test['data']['description']
current_project = existing_test['data']['project']['key']

# 3. Delete the existing test
delete_result = xray_test(
    entity="test",
    action="delete",
    issue_id="1192649"
)

# 4. Create new test with updated steps
new_test = xray_test(
    entity="test",
    action="create",
    project_key=current_project,
    summary=current_summary,
    test_type="Manual",
    description=current_description,
    steps=[
        {
            "action": "Updated: Navigate to new login page",
            "data": "URL: https://app.example.com/v2/login",
            "result": "New login page displays with enhanced security features"
        },
        {
            "action": "Updated: Enter credentials with 2FA",
            "data": "Username: testuser@example.com, Password: ValidPass123!, 2FA: 123456",
            "result": "Credentials and 2FA are accepted, user is logged in"
        },
        {
            "action": "Updated: Verify enhanced dashboard",
            "data": "Navigate to new dashboard",
            "result": "Enhanced dashboard displays with personalized content"
        }
    ]
)

print(f"Test recreated with new ID: {new_test['data']['issueId']}")
```

**Option 2: Convert to Cucumber (Recommended for flexible tests)**
```python
# 1. Convert test type to Cucumber
conversion_result = xray_test(
    entity="test",
    action="update_type",
    issue_id="1192649",
    test_type="Cucumber"
)

# 2. Update with Gherkin content (which CAN be updated)
gherkin_content = '''
Feature: User Authentication
  As a registered user
  I want to log into the application
  So that I can access my account

Scenario: Successful login with updated workflow
  Given I am on the updated login page
  When I enter valid credentials "testuser@example.com" and "ValidPass123!"
  And I complete 2FA verification
  Then I should be logged in successfully
  And I should see the enhanced dashboard
'''

update_result = xray_test(
    entity="test",
    action="update_content",
    issue_id="1192649",
    gherkin=gherkin_content
)
```

### **2. Cucumber Tests - FLEXIBLE UPDATE CAPABILITY**

#### **✅ Creating Cucumber Tests**
```python
# WORKS: Create Cucumber test with Gherkin
gherkin_content = '''
Feature: User Registration
  As a new user
  I want to register for an account
  So that I can access the application

Background:
  Given the registration page is available

Scenario: Successful registration
  Given I am on the registration page
  When I enter valid personal information
    | Field     | Value                |
    | Email     | newuser@example.com  |
    | Password  | SecurePass123!       |
    | FirstName | John                 |
    | LastName  | Doe                  |
  And I accept the terms of service
  Then my account should be created
  And I should receive a confirmation email

Scenario: Registration with existing email
  Given I am on the registration page
  When I enter an email that already exists "existing@example.com"
  Then I should see an error message "Email already registered"
'''

result = xray_test(
    entity="test",
    action="create",
    project_key="DEMO",
    summary="User Registration Feature",
    test_type="Cucumber",
    gherkin=gherkin_content
)
```

#### **✅ Updating Cucumber Test Content**
```python
# WORKS: Update Gherkin content easily
updated_gherkin = '''
Feature: User Registration (Enhanced)
  As a new user
  I want to register for an account with enhanced security
  So that I can safely access the application

Background:
  Given the registration page is available
  And enhanced security features are enabled

Scenario: Successful registration with email verification
  Given I am on the registration page
  When I enter valid personal information
    | Field     | Value                |
    | Email     | newuser@example.com  |
    | Password  | SecurePass123!       |
    | FirstName | John                 |
    | LastName  | Doe                  |
    | Phone     | +1-555-0123          |
  And I accept the terms of service
  And I verify my email address
  Then my account should be created
  And I should receive a welcome email

Scenario: Registration with weak password
  Given I am on the registration page
  When I enter a weak password "123456"
  Then I should see a password strength warning
  And registration should be blocked

Scenario: Registration with existing email
  Given I am on the registration page
  When I enter an email that already exists "existing@example.com"
  Then I should see an error message "Email already registered"
  And I should be offered to reset password
'''

update_result = xray_test(
    entity="test",
    action="update_content",
    issue_id="1192649",
    gherkin=updated_gherkin
)
```

### **3. Generic Tests - SIMPLE OPERATIONS**

#### **✅ Creating Generic Tests**
```python
# WORKS: Create simple generic test
result = xray_test(
    entity="test",
    action="create",
    project_key="DEMO",
    summary="API Response Time Test",
    test_type="Generic",
    description="Verify API responds within acceptable time limits"
)
```

---

## 🔄 **Step Migration Strategies**

### **Strategy 1: Manual to Cucumber Conversion**

#### **Step 1: Analyze Manual Test Structure**
```python
# Get existing manual test
manual_test = xray_test(entity="test", action="get", issue_id="1192649")
steps = manual_test['data']['steps']

# Analyze step structure
for i, step in enumerate(steps):
    print(f"Step {i+1}:")
    print(f"  Action: {step['action']}")
    print(f"  Data: {step['data']}")
    print(f"  Expected: {step['result']}")
```

#### **Step 2: Convert to Gherkin Format**
```python
def convert_manual_steps_to_gherkin(steps, test_summary):
    """Convert manual test steps to Gherkin format."""

    # Extract feature name from summary
    feature_name = test_summary.replace(" Test", "").replace(" test", "")

    gherkin = f'''
Feature: {feature_name}
  As a user
  I want to {feature_name.lower()}
  So that I can achieve my goal

Scenario: {test_summary}
'''

    for i, step in enumerate(steps):
        action = step['action']
        data = step['data']
        result = step['result']

        # Convert action to Gherkin step
        if i == 0:
            gherkin += f"  Given {action.lower()}\n"
        elif "verify" in action.lower() or "check" in action.lower():
            gherkin += f"  Then {result.lower()}\n"
        else:
            gherkin += f"  When {action.lower()}\n"

        # Add data as step details if present
        if data and data.strip():
            gherkin += f"    # Data: {data}\n"

    return gherkin

# Usage example
manual_test = xray_test(entity="test", action="get", issue_id="1192649")
gherkin_content = convert_manual_steps_to_gherkin(
    manual_test['data']['steps'],
    manual_test['data']['summary']
)

# Convert test type and update content
xray_test(entity="test", action="update_type", issue_id="1192649", test_type="Cucumber")
xray_test(entity="test", action="update_content", issue_id="1192649", gherkin=gherkin_content)
```

### **Strategy 2: Bulk Test Modernization**

```python
def modernize_test_suite(project_key):
    """Convert all manual tests in a project to Cucumber format."""

    # Get all manual tests
    manual_tests = xray_test(
        entity="test",
        action="list",
        project_key=project_key,
        jql="'Test Type' = Manual"
    )

    conversion_results = []

    for test in manual_tests['data']:
        test_id = test['issueId']

        try:
            # Get full test details
            full_test = xray_test(entity="test", action="get", issue_id=test_id)

            # Check if test has steps
            if 'steps' in full_test['data'] and full_test['data']['steps']:
                # Convert to Gherkin
                gherkin = convert_manual_steps_to_gherkin(
                    full_test['data']['steps'],
                    full_test['data']['summary']
                )

                # Update test type
                type_result = xray_test(
                    entity="test",
                    action="update_type",
                    issue_id=test_id,
                    test_type="Cucumber"
                )

                # Update content
                content_result = xray_test(
                    entity="test",
                    action="update_content",
                    issue_id=test_id,
                    gherkin=gherkin
                )

                conversion_results.append({
                    'test_id': test_id,
                    'summary': full_test['data']['summary'],
                    'status': 'converted',
                    'type_update': type_result['success'],
                    'content_update': content_result['success']
                })
            else:
                conversion_results.append({
                    'test_id': test_id,
                    'summary': full_test['data']['summary'],
                    'status': 'skipped_no_steps'
                })

        except Exception as e:
            conversion_results.append({
                'test_id': test_id,
                'status': 'error',
                'error': str(e)
            })

    return conversion_results

# Usage
results = modernize_test_suite("DEMO")
for result in results:
    print(f"Test {result['test_id']}: {result['status']}")
```

---

## 📊 **Step Operation Comparison**

| Operation | Manual Tests | Cucumber Tests | Generic Tests |
|-----------|-------------|----------------|---------------|
| Create with steps | ✅ | ✅ (Gherkin) | ❌ (N/A) |
| Update steps | ❌ | ✅ (Gherkin) | ❌ (N/A) |
| Add single step | ❌ | ✅ (Edit Gherkin) | ❌ (N/A) |
| Reorder steps | ❌ | ✅ (Edit Gherkin) | ❌ (N/A) |
| Delete steps | ❌ | ✅ (Edit Gherkin) | ❌ (N/A) |
| Bulk operations | ❌ | ✅ | ❌ (N/A) |

---

## 🎯 **Best Practices**

### **1. Test Design Decisions**

#### **Choose Manual Tests When:**
- Steps will rarely change
- Simple test procedures
- Legacy test migration
- Documentation-heavy tests

#### **Choose Cucumber Tests When:**
- Steps change frequently
- Multiple scenarios per feature
- Behavior-driven development
- Parameterized testing

#### **Choose Generic Tests When:**
- Simple pass/fail validation
- API/performance testing
- Automated test placeholders

### **2. Step Update Planning**

#### **Before Creating Tests:**
```python
# Plan for future updates
test_strategy = {
    "test_type": "Cucumber" if steps_likely_to_change else "Manual",
    "documentation": "Include comprehensive descriptions",
    "maintenance": "Plan conversion strategy if needed"
}
```

#### **When Steps Need Updates:**
```python
# Decision tree
if test_type == "Manual":
    if major_changes:
        # Delete and recreate
        recreate_test_with_new_steps()
    elif frequent_updates_expected:
        # Convert to Cucumber
        convert_to_cucumber_format()
    else:
        # Accept limitation and document workaround
        document_manual_process()
```

### **3. Maintenance Workflows**

#### **Weekly Test Review:**
```python
def review_test_maintenance_needs(project_key):
    """Identify tests that might benefit from format conversion."""

    # Find manual tests that were recently modified multiple times
    manual_tests = xray_test(
        entity="test",
        action="list",
        project_key=project_key,
        jql="'Test Type' = Manual AND updated >= -30d"
    )

    recommendations = []

    for test in manual_tests['data']:
        # Check modification frequency (would need additional API calls)
        # This is pseudocode for the concept
        recommendations.append({
            'test_id': test['issueId'],
            'summary': test['summary'],
            'recommendation': 'Consider converting to Cucumber for easier updates'
        })

    return recommendations
```

---

## ⚠️ **Important Considerations**

### **Data Loss Risks**
- **Delete/Recreate**: Loses test history, comments, and linked issues
- **Type Conversion**: Preserves history but may affect reporting

### **Impact on Test Executions**
- Recreated tests will have new IDs and won't appear in existing executions
- Type conversion maintains test ID but may affect execution behavior

### **Team Coordination**
- Communicate test changes to team members
- Update test execution plans after major modifications
- Consider impact on automated test scripts that reference test IDs

---

## 🏁 **Summary**

Step operations in Xray MCP server are constrained by API limitations, but effective workarounds exist:

1. **For flexible tests**: Use Cucumber format from the start
2. **For existing manual tests**: Plan conversion strategy based on update frequency
3. **For major updates**: Delete/recreate when step history isn't critical
4. **For minor updates**: Consider using test descriptions (updateable via JIRA API)

**The key is choosing the right test format for your update requirements and having a clear migration strategy when needs change.**