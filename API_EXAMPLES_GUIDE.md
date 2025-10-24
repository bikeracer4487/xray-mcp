# Xray MCP Server - Comprehensive API Examples Guide

## ⚠️ CRITICAL: ID Format Requirements

**IMPORTANT:** Many examples in this guide use JIRA keys (e.g., "FTEST-123") which **DO NOT WORK** with the Xray GraphQL API. The API requires **numeric issue IDs** only.

### ✅ Correct Pattern
```json
// Step 1: List to get numeric IDs
{
  "entity": "test",
  "action": "list",
  "project_key": "FTEST"
}
// Returns: {"issueId": "1192649", "issueKey": "FTEST-123", ...}

// Step 2: Use numeric ID for operations
{
  "entity": "test",
  "action": "get",
  "issue_id": "1192649"  // ✅ Use this (numeric)
}
```

### ❌ Incorrect Pattern
```json
{
  "entity": "test",
  "action": "get",
  "issue_id": "FTEST-123"  // ❌ This will fail
}
```

**📖 For complete details, see [ID_FORMAT_REQUIREMENTS.md](./ID_FORMAT_REQUIREMENTS.md)**

---

## Overview

This guide provides comprehensive examples for using the Xray MCP server, covering all entities, operations, and real-world use cases. Examples are organized by complexity and use case type.

**⚠️ Note:** Examples below use JIRA key format for readability, but remember to use numeric IDs in actual implementation.

---

## 🧪 Test Management Examples

### Basic Test Operations

#### Create Manual Test - Simple

```json
{
  "entity": "test",
  "action": "create",
  "project_key": "FTEST",
  "summary": "User Login Test",
  "test_type": "Manual",
  "priority": "High",
  "steps": [
    {
      "action": "Navigate to login page",
      "data": "https://app.example.com/login",
      "result": "Login page displays"
    },
    {
      "action": "Enter valid credentials",
      "data": "user@test.com / password123",
      "result": "Credentials accepted"
    },
    {
      "action": "Click Login button",
      "data": "Login button",
      "result": "Successfully logged in"
    }
  ],
  "description": "Verify user can log in with valid credentials"
}
```

#### Create Manual Test - Complex

```json
{
  "entity": "test",
  "action": "create",
  "project_key": "FTEST",
  "summary": "E-commerce Checkout Flow - Complete Transaction",
  "test_type": "Manual",
  "priority": "Critical",
  "steps": [
    {
      "action": "Add products to cart",
      "data": "Product A ($29.99), Product B ($49.99)",
      "result": "Cart shows 2 items, total $79.98"
    },
    {
      "action": "Proceed to checkout",
      "data": "Checkout button",
      "result": "Checkout page loads with cart summary"
    },
    {
      "action": "Enter shipping information",
      "data": "Name: John Doe, Address: 123 Main St, City: Anytown, ZIP: 12345",
      "result": "Shipping information accepted and validated"
    },
    {
      "action": "Select shipping method",
      "data": "Standard shipping ($5.99)",
      "result": "Shipping cost added, total $85.97"
    },
    {
      "action": "Enter payment information",
      "data": "Card: 4111111111111111, Exp: 12/25, CVV: 123",
      "result": "Payment information validated"
    },
    {
      "action": "Apply discount code",
      "data": "SAVE10 (10% off)",
      "result": "Discount applied, total $77.37"
    },
    {
      "action": "Review and confirm order",
      "data": "Order confirmation button",
      "result": "Order placed successfully"
    },
    {
      "action": "Verify confirmation email",
      "data": "Check email inbox",
      "result": "Order confirmation email received with tracking number"
    }
  ],
  "description": "End-to-end test of complete e-commerce checkout process including cart management, shipping, payment, discounts, and confirmation"
}
```

#### Create BDD/Cucumber Test

```json
{
  "entity": "test",
  "action": "create",
  "project_key": "FTEST",
  "summary": "User Authentication API - BDD Test",
  "test_type": "Cucumber",
  "priority": "High",
  "gherkin": "Feature: User Authentication API\n\n  As a client application\n  I want to authenticate users via API\n  So that users can access protected resources\n\n  Background:\n    Given the API service is running\n    And the user database is accessible\n\n  @authentication @api @smoke\n  Scenario: Successful authentication with valid credentials\n    Given I have valid user credentials\n    When I send a POST request to \"/api/auth/login\"\n    And the request body contains:\n      \"\"\"\n      {\n        \"username\": \"testuser@example.com\",\n        \"password\": \"SecurePass123\"\n      }\n      \"\"\"\n    Then I should receive a 200 status code\n    And the response should contain an authentication token\n    And the token should be valid for 24 hours\n\n  @authentication @api @error-handling\n  Scenario: Failed authentication with invalid credentials\n    Given I have invalid user credentials\n    When I send a POST request to \"/api/auth/login\"\n    And the request body contains:\n      \"\"\"\n      {\n        \"username\": \"invalid@example.com\",\n        \"password\": \"wrongpassword\"\n      }\n      \"\"\"\n    Then I should receive a 401 status code\n    And the response should contain an error message\n    And no authentication token should be provided\n\n  @authentication @api @validation\n  Scenario Outline: Authentication with various invalid inputs\n    Given I am testing input validation\n    When I send a POST request to \"/api/auth/login\"\n    And the request body contains \"<request_body>\"\n    Then I should receive a <status_code> status code\n    And the response should contain \"<error_message>\"\n\n    Examples:\n      | request_body                                           | status_code | error_message           |\n      | {}                                                     | 400         | Username is required    |\n      | {\"username\": \"test@example.com\"}                      | 400         | Password is required    |\n      | {\"username\": \"invalid-email\", \"password\": \"pass\"}    | 400         | Invalid email format    |\n      | {\"username\": \"test@example.com\", \"password\": \"123\"}  | 400         | Password too short      |",
  "description": "Comprehensive BDD test for user authentication API covering success scenarios, error handling, and input validation"
}
```

### Test Update Operations

#### Update Test Content

```json
{
  "entity": "test",
  "action": "update_content",
  "issue_id": "FTEST-123",
  "gherkin": "Feature: Updated User Registration\n\n@registration @v2\nScenario: Enhanced user registration with email verification\n    Given I am on the registration page\n    When I complete the registration form\n    And I verify my email address\n    Then my account should be activated\n    And I should receive a welcome email"
}
```

#### Change Test Type

```json
{
  "entity": "test",
  "action": "update_type",
  "issue_id": "FTEST-124",
  "test_type": "Cucumber"
}
```

### Test Querying

#### List Tests with Filtering

```json
{
  "entity": "test",
  "action": "list",
  "project_key": "FTEST",
  "limit": 50,
  "jql": "priority = High AND labels = 'regression'"
}
```

#### Get Specific Test

```json
{
  "entity": "test",
  "action": "get",
  "issue_id": "FTEST-123"
}
```

---

## 🚀 Test Execution Management Examples

### Execution Creation and Management

#### Create Test Execution - Regression Suite

```json
{
  "entity": "test_execution",
  "action": "create",
  "project_key": "FTEST",
  "summary": "Release 2.0 Regression Test Execution",
  "description": "Comprehensive regression testing for Release 2.0 covering all critical functionality including authentication, payment processing, user management, and reporting features",
  "test_environments": ["Staging", "UAT", "Pre-Production"]
}
```

#### Create Test Execution - Smoke Test

```json
{
  "entity": "test_execution",
  "action": "create",
  "project_key": "FTEST",
  "summary": "Daily Smoke Test Execution",
  "description": "Daily smoke test execution for critical path validation including login, core API endpoints, and basic user workflows",
  "test_environments": ["Production"]
}
```

#### Add Tests to Execution

```json
{
  "entity": "test_execution",
  "action": "add_tests",
  "issue_id": "FTEST-500",
  "test_issue_ids": ["FTEST-101", "FTEST-102", "FTEST-103", "FTEST-104"]
}
```

#### Remove Tests from Execution

```json
{
  "entity": "test_execution",
  "action": "remove_tests",
  "issue_id": "FTEST-500",
  "test_issue_ids": ["FTEST-104"]
}
```

#### Add Environments to Execution

```json
{
  "entity": "test_execution",
  "action": "add_environments",
  "issue_id": "FTEST-500",
  "test_environments": ["Performance", "Security"]
}
```

---

## 📋 Test Planning Examples

### Test Plan Creation

#### Release Test Plan

```json
{
  "entity": "test_plan",
  "action": "create",
  "project_key": "FTEST",
  "summary": "Release 3.0 Master Test Plan",
  "description": "Comprehensive test plan for Release 3.0 covering:\n\n**New Features:**\n- Advanced user authentication (SSO, MFA)\n- Real-time notifications system\n- Enhanced reporting dashboard\n- Mobile API improvements\n\n**Testing Phases:**\n1. Unit testing (Development team)\n2. Integration testing (QA team)\n3. System testing (QA team)\n4. User acceptance testing (Business team)\n5. Performance testing (DevOps team)\n6. Security testing (Security team)\n\n**Success Criteria:**\n- All critical and high priority tests pass\n- Performance benchmarks met\n- Security scan passes\n- User acceptance criteria satisfied\n\n**Timeline:**\n- Testing Phase: 3 weeks\n- UAT Phase: 1 week\n- Production Deployment: Week 5"
}
```

#### Sprint Test Plan

```json
{
  "entity": "test_plan",
  "action": "create",
  "project_key": "FTEST",
  "summary": "Sprint 25 Test Plan - User Profile Enhancement",
  "description": "Sprint 25 testing plan focusing on user profile enhancements:\n\n**User Stories Covered:**\n- US-451: Enhanced profile picture upload\n- US-452: Two-factor authentication setup\n- US-453: Privacy settings management\n- US-454: Account linking (social media)\n\n**Testing Approach:**\n- BDD scenarios for each user story\n- Cross-browser compatibility testing\n- Mobile responsiveness validation\n- API integration testing\n\n**Definition of Done:**\n- All acceptance criteria tests pass\n- No critical or high severity bugs\n- Performance impact within acceptable limits\n- Documentation updated"
}
```

#### Feature Test Plan

```json
{
  "entity": "test_plan",
  "action": "create",
  "project_key": "FTEST",
  "summary": "Payment Gateway Integration - Feature Test Plan",
  "description": "Comprehensive test plan for new payment gateway integration:\n\n**Scope:**\n- Payment processing workflows\n- Multiple payment methods (cards, digital wallets)\n- Currency conversion\n- Refund processing\n- Security compliance (PCI DSS)\n\n**Test Types:**\n- Functional testing\n- Security testing\n- Performance testing\n- Error handling and recovery\n- Integration testing with existing systems\n\n**Risk Areas:**\n- Payment failures and recovery\n- Data security and encryption\n- Third-party service dependencies\n- Currency calculation accuracy\n\n**Entry Criteria:**\n- Development complete\n- Unit tests passing\n- Integration environment ready\n- Test data prepared\n\n**Exit Criteria:**\n- All test cases executed\n- Critical bugs resolved\n- Performance benchmarks met\n- Security scan clean\n- User acceptance complete"
}
```

### Test Plan Management

#### Add Tests to Plan

```json
{
  "entity": "test_plan",
  "action": "add_tests",
  "issue_id": "FTEST-600",
  "test_issue_ids": ["FTEST-201", "FTEST-202", "FTEST-203", "FTEST-204", "FTEST-205"]
}
```

#### Add Executions to Plan

```json
{
  "entity": "test_plan",
  "action": "add_executions",
  "issue_id": "FTEST-600",
  "test_exec_issue_ids": ["FTEST-501", "FTEST-502", "FTEST-503"]
}
```

#### Remove Tests from Plan

```json
{
  "entity": "test_plan",
  "action": "remove_tests",
  "issue_id": "FTEST-600",
  "test_issue_ids": ["FTEST-205"]
}
```

---

## 🏃‍♂️ Test Run Management Examples

### Test Run Status Updates

#### Update Test Run - Passed

```json
{
  "entity": "test_run",
  "action": "update_status",
  "test_execution_id": "FTEST-500",
  "test_issue_id": "FTEST-101",
  "status": "PASS",
  "comment": "Login functionality working correctly. All test steps completed successfully:\n\n✅ Login page loads within 2 seconds\n✅ Valid credentials accepted\n✅ User redirected to dashboard\n✅ Session maintained across browser refresh\n✅ Logout functionality works correctly\n\nEnvironment: UAT\nBrowser: Chrome 118.0\nExecution Time: 3.5 minutes\nTester: QA Team Member"
}
```

#### Update Test Run - Failed

```json
{
  "entity": "test_run",
  "action": "update_status",
  "test_execution_id": "FTEST-500",
  "test_issue_id": "FTEST-102",
  "status": "FAIL",
  "comment": "Payment processing failed during checkout:\n\n❌ **FAILURE POINT:** Credit card validation step\n\n**Steps Executed:**\n✅ Added items to cart successfully\n✅ Proceeded to checkout\n✅ Entered shipping information\n❌ Payment processing - Error: 'Invalid merchant account'\n\n**Error Details:**\n- Error Code: PMT-500\n- Error Message: 'Merchant account configuration invalid'\n- Timestamp: 2024-01-15 14:32:18 UTC\n\n**Impact:** Critical - blocks all payment transactions\n\n**Recommended Action:** \n1. Check payment gateway configuration\n2. Verify merchant account settings\n3. Test with different payment methods\n\n**Environment:** Staging\n**Browser:** Chrome 118.0\n**Defect Logged:** FTEST-BUG-789"
}
```

#### Update Test Run - Blocked

```json
{
  "entity": "test_run",
  "action": "update_status",
  "test_execution_id": "FTEST-500",
  "test_issue_id": "FTEST-103",
  "status": "TODO",
  "comment": "Test execution blocked due to environment issues:\n\n🚫 **BLOCKING ISSUE:** Database connectivity problems\n\n**Details:**\n- Cannot connect to test database\n- Error: Connection timeout after 30 seconds\n- Database server appears to be down\n\n**Impact:** Cannot execute any tests requiring database access\n\n**Action Required:**\n- Infrastructure team notified\n- Ticket opened: INFRA-456\n- ETA for resolution: 2 hours\n\n**Next Steps:**\n- Will retry once database is restored\n- May need to reschedule dependent tests\n\n**Environment:** UAT\n**Reported by:** QA Team Lead\n**Reported at:** 2024-01-15 15:45:00 UTC"
}
```

### Test Run with Evidence and Defects

#### Add Comment to Test Run

```json
{
  "entity": "test_run",
  "action": "update_comment",
  "test_execution_id": "FTEST-500",
  "test_issue_id": "FTEST-104",
  "comment": "Additional testing notes:\n\n**Performance Observations:**\n- Page load time: 2.3 seconds (within acceptable range <3s)\n- API response time: 450ms (excellent)\n- Memory usage: 85MB (normal)\n\n**Cross-browser Results:**\n✅ Chrome 118.0 - All features working\n✅ Firefox 119.0 - All features working  \n✅ Safari 17.0 - All features working\n⚠️ Edge 118.0 - Minor CSS alignment issue (non-critical)\n\n**Mobile Testing:**\n✅ iOS Safari - Responsive design working\n✅ Android Chrome - Touch interactions working\n\n**Recommendations:**\n- Edge CSS issue documented as minor enhancement\n- Performance is excellent, no optimization needed\n- Ready for production deployment\n\n**Attachments:**\n- Performance_Report_2024-01-15.pdf\n- Cross_Browser_Screenshots.zip\n- Mobile_Test_Results.xlsx"
}
```

---

## 🔍 Advanced Query Examples

### Complex Test Filtering

#### Find Tests by Multiple Criteria

```json
{
  "entity": "test",
  "action": "list",
  "project_key": "FTEST",
  "limit": 100,
  "jql": "priority IN (High, Critical) AND labels IN ('automation-candidate', 'regression') AND created >= -30d"
}
```

#### Find Failed Tests in Recent Executions

```json
{
  "entity": "test_execution",
  "action": "list",
  "project_key": "FTEST",
  "limit": 50,
  "jql": "created >= -7d AND summary ~ 'regression'"
}
```

---

## 🌍 Multilingual Content Examples

### Tests with International Content

#### Chinese Language Test

```json
{
  "entity": "test",
  "action": "create",
  "project_key": "FTEST",
  "summary": "用户登录测试 - Chinese User Login Test",
  "test_type": "Manual",
  "priority": "High",
  "steps": [
    {
      "action": "导航到登录页面",
      "data": "URL: https://app.example.com/zh/login",
      "result": "登录页面正确显示中文界面"
    },
    {
      "action": "输入有效的中文用户名",
      "data": "用户名: 测试用户@example.com",
      "result": "中文用户名被正确接受"
    },
    {
      "action": "验证登录成功",
      "data": "点击登录按钮",
      "result": "用户成功登录并跳转到中文仪表板"
    }
  ],
  "description": "验证系统对中文用户界面和中文输入的支持，确保本地化功能正常工作"
}
```

#### Arabic Language Test

```json
{
  "entity": "test",
  "action": "create",
  "project_key": "FTEST",
  "summary": "اختبار تسجيل الدخول - Arabic Login Test",
  "test_type": "Manual",
  "priority": "High",
  "steps": [
    {
      "action": "التنقل إلى صفحة تسجيل الدخول",
      "data": "الرابط: https://app.example.com/ar/login",
      "result": "تظهر صفحة تسجيل الدخول باللغة العربية بشكل صحيح"
    },
    {
      "action": "إدخال بيانات صحيحة بالعربية",
      "data": "اسم المستخدم: مستخدم.تجريبي@example.com",
      "result": "يتم قبول البيانات العربية بشكل صحيح"
    },
    {
      "action": "التحقق من نجاح تسجيل الدخول",
      "data": "النقر على زر تسجيل الدخول",
      "result": "ينجح المستخدم في تسجيل الدخول ويتم توجيهه للوحة الرئيسية العربية"
    }
  ],
  "description": "اختبار دعم النظام للواجهة العربية والإدخال باللغة العربية، والتأكد من عمل ميزات التعريب بشكل صحيح"
}
```

#### Emoji and Special Characters Test

```json
{
  "entity": "test",
  "action": "create",
  "project_key": "FTEST",
  "summary": "🧪 Emoji Support Test - Special Characters 🚀✨",
  "test_type": "Manual",
  "priority": "Medium",
  "steps": [
    {
      "action": "Test emoji input in text fields 📝",
      "data": "Input: Hello World! 🌍 👋 How are you? 😊 ✅ 🎉",
      "result": "Emojis display correctly in all text fields 👍"
    },
    {
      "action": "Test special characters input 🔤",
      "data": "Characters: àáâãäåæçèéêëìíîïñòóôõöøùúûüýÿ",
      "result": "All accented characters display properly ✅"
    },
    {
      "action": "Test mixed content with emojis 🌐",
      "data": "Text: Testing 🧪 with emojis 😀 and symbols ⚡ works! 🎯",
      "result": "Mixed content with emojis renders correctly 🎊"
    }
  ],
  "description": "Comprehensive test for emoji and special character support across the application 🔍 Ensures unicode compatibility and proper rendering 🎨"
}
```

---

## ⚡ Performance Testing Examples

### Bulk Operations

#### Bulk Test Creation

```python
# Example for creating multiple tests efficiently
tests_to_create = [
    {
        "entity": "test",
        "action": "create",
        "project_key": "FTEST",
        "summary": f"Performance Test {i:03d}",
        "test_type": "Manual",
        "priority": "Medium",
        "steps": [
            {
                "action": f"Execute performance test step {i}",
                "data": f"Test data for iteration {i}",
                "result": f"Expected result for test {i}"
            }
        ]
    }
    for i in range(1, 101)  # Create 100 tests
]

# Execute concurrently for better performance
import asyncio
results = await asyncio.gather(*[tool.execute(test) for test in tests_to_create])
```

#### Large Test Execution

```json
{
  "entity": "test_execution",
  "action": "create",
  "project_key": "FTEST",
  "summary": "Large Scale Performance Test Execution",
  "description": "Performance test execution containing 500+ test cases to validate system performance under load",
  "test_environments": ["Performance", "Load-Testing"]
}
```

---

## 🚨 Error Handling Examples

### Common Error Scenarios

#### Invalid Entity Error

```json
{
  "entity": "invalid_entity",
  "action": "create",
  "project_key": "FTEST",
  "summary": "This will fail"
}

// Response:
{
  "success": false,
  "errors": [
    "Invalid entity: 'invalid_entity'",
    "Valid entities are: test, test_execution, test_plan, test_run",
    "Example: entity='test' for test operations"
  ]
}
```

#### Missing Required Fields

```json
{
  "entity": "test",
  "action": "create",
  "project_key": "FTEST"
  // Missing summary field
}

// Response:
{
  "success": false,
  "errors": [
    "Missing required parameter: summary"
  ]
}
```

#### Non-existent Resource

```json
{
  "entity": "test",
  "action": "get",
  "issue_id": "FTEST-99999"
}

// Response:
{
  "success": false,
  "errors": [
    "Test with ID 'FTEST-99999' not found"
  ]
}
```

---

## 🔄 Complex Workflow Examples

### Complete Release Testing Workflow

```python
async def complete_release_testing_workflow():
    """Example of a complete release testing workflow."""

    # 1. Create comprehensive test suite
    test_types = ['authentication', 'payment', 'reporting', 'api', 'mobile']
    created_tests = []

    for test_type in test_types:
        for complexity in ['smoke', 'regression', 'edge-case']:
            test = await tool.execute({
                'entity': 'test',
                'action': 'create',
                'project_key': 'FTEST',
                'summary': f'Release 3.0 - {test_type.title()} {complexity.title()} Test',
                'test_type': 'Manual',
                'priority': 'High' if complexity == 'smoke' else 'Medium'
            })
            if test['success']:
                created_tests.append(test['data']['test']['issueId'])

    # 2. Create test executions for different phases
    executions = []
    phases = [
        ('Smoke Test', created_tests[:5]),
        ('Regression Test', created_tests[5:]),
        ('Performance Test', created_tests[::2])  # Every other test
    ]

    for phase_name, test_subset in phases:
        execution = await tool.execute({
            'entity': 'test_execution',
            'action': 'create',
            'project_key': 'FTEST',
            'summary': f'Release 3.0 - {phase_name}',
            'test_environments': ['UAT', 'Staging']
        })

        if execution['success']:
            exec_id = execution['data']['testExecution']['issueId']
            executions.append(exec_id)

            # Add tests to execution
            await tool.execute({
                'entity': 'test_execution',
                'action': 'add_tests',
                'issue_id': exec_id,
                'test_issue_ids': test_subset
            })

    # 3. Create master test plan
    plan = await tool.execute({
        'entity': 'test_plan',
        'action': 'create',
        'project_key': 'FTEST',
        'summary': 'Release 3.0 Master Test Plan',
        'description': 'Comprehensive test plan covering all aspects of Release 3.0'
    })

    if plan['success']:
        plan_id = plan['data']['testPlan']['issueId']

        # Add all tests and executions to plan
        await tool.execute({
            'entity': 'test_plan',
            'action': 'add_tests',
            'issue_id': plan_id,
            'test_issue_ids': created_tests
        })

        await tool.execute({
            'entity': 'test_plan',
            'action': 'add_executions',
            'issue_id': plan_id,
            'test_exec_issue_ids': executions
        })

    # 4. Execute tests and update statuses
    for exec_id in executions:
        execution_details = await tool.execute({
            'entity': 'test_execution',
            'action': 'get',
            'issue_id': exec_id
        })

        if execution_details['success']:
            test_runs = execution_details['data']['testExecution']['testRuns']

            for test_run in test_runs:
                test_id = test_run['test']['issueId']

                # Simulate test execution with realistic results
                status = 'PASS' if random.random() > 0.1 else 'FAIL'  # 90% pass rate

                await tool.execute({
                    'entity': 'test_run',
                    'action': 'update_status',
                    'test_execution_id': exec_id,
                    'test_issue_id': test_id,
                    'status': status,
                    'comment': f'Test executed for Release 3.0 validation - Status: {status}'
                })

    return {
        'tests_created': len(created_tests),
        'executions_created': len(executions),
        'plan_created': plan_id if plan['success'] else None
    }
```

---

## 🔧 Best Practices and Tips

### 1. Efficient Test Creation

**Use Batch Operations:**
```python
# Instead of creating tests one by one
for i in range(100):
    await tool.execute({...})  # Slow

# Create them concurrently
tasks = [tool.execute({...}) for i in range(100)]
results = await asyncio.gather(*tasks)  # Fast
```

### 2. Effective Error Handling

**Always Check Response Status:**
```python
result = await tool.execute({...})
if result['success']:
    # Process successful result
    data = result['data']
else:
    # Handle errors appropriately
    errors = result.get('errors', [])
    logging.error(f"Operation failed: {errors}")
```

### 3. Resource Management

**Track Created Resources:**
```python
created_resources = []

try:
    # Create resources
    test_result = await tool.execute({...})
    if test_result['success']:
        test_id = test_result['data']['test']['issueId']
        created_resources.append(('test', test_id))
finally:
    # Cleanup
    for resource_type, resource_id in reversed(created_resources):
        await tool.execute({
            'entity': resource_type,
            'action': 'delete',
            'issue_id': resource_id
        })
```

### 4. Performance Optimization

**Use Appropriate Limits:**
```json
{
  "entity": "test",
  "action": "list",
  "project_key": "FTEST",
  "limit": 50  // Don't request more than needed
}
```

**Filter Results:**
```json
{
  "entity": "test",
  "action": "list",
  "project_key": "FTEST",
  "jql": "priority = High"  // Use JQL to filter server-side
}
```

### 5. Content Best Practices

**Structure Gherkin Properly:**
```gherkin
Feature: Clear, descriptive feature name

  Background:
    Given common setup steps
    And shared preconditions

  @tag1 @tag2
  Scenario: Descriptive scenario name
    Given clear initial state
    When specific action is taken
    Then expected outcome occurs
    And additional verification steps

  Scenario Outline: Template for data-driven tests
    Given I have "<input>"
    When I process it
    Then I get "<output>"

    Examples:
      | input | output |
      | data1 | result1 |
      | data2 | result2 |
```

**Write Clear Test Steps:**
```json
{
  "action": "Clear, specific action description",
  "data": "Concrete test data or input values",
  "result": "Specific, measurable expected outcome"
}
```

---

## 📊 Response Format Reference

### Successful Response Format

```json
{
  "success": true,
  "data": {
    "test": {
      "issueId": "FTEST-123",
      "testType": {
        "name": "Manual"
      },
      "jira": {
        "key": "FTEST-123",
        "summary": "Test Summary",
        "description": "Test Description"
      }
    }
  }
}
```

### Error Response Format

```json
{
  "success": false,
  "errors": [
    "Specific error message",
    "Additional context or suggestions"
  ]
}
```

This comprehensive guide covers all major use cases and provides practical examples for implementing robust test management workflows with the Xray MCP server.