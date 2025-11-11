"""
Test data generators and fixtures for comprehensive Xray MCP testing.

Provides realistic test data for various testing scenarios including:
- Manual test cases with steps
- BDD/Cucumber scenarios
- Test executions and plans
- Performance testing data
- Edge case data
- Multilingual content
"""

import random
import string
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional
import json


class TestDataGenerator:
    """Generates realistic test data for various testing scenarios."""

    def __init__(self, prefix: Optional[str] = None):
        """Initialize with optional prefix for generated data."""
        self.prefix = prefix or f"TestData_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        self.counter = 0

    def _get_unique_id(self) -> str:
        """Generate unique identifier."""
        self.counter += 1
        return f"{self.prefix}_{self.counter:04d}"

    def generate_manual_test_case(self, complexity: str = "medium") -> Dict[str, Any]:
        """
        Generate manual test case data.

        Args:
            complexity: "simple", "medium", "complex"
        """
        test_templates = {
            "simple": {
                "step_count": (2, 4),
                "priorities": ["Low", "Medium"],
                "descriptions": [
                    "Basic functionality test",
                    "Simple user interaction test",
                    "Basic validation test"
                ]
            },
            "medium": {
                "step_count": (4, 8),
                "priorities": ["Medium", "High"],
                "descriptions": [
                    "Comprehensive functionality test covering multiple scenarios",
                    "End-to-end workflow validation with error handling",
                    "Integration test with external dependencies"
                ]
            },
            "complex": {
                "step_count": (8, 15),
                "priorities": ["High", "Critical"],
                "descriptions": [
                    "Complex multi-step workflow with conditional logic and error recovery",
                    "Comprehensive integration test covering multiple systems and edge cases",
                    "Advanced scenario testing with performance and security validation"
                ]
            }
        }

        template = test_templates[complexity]
        step_count = random.randint(*template["step_count"])

        # Generate test steps
        steps = []
        for i in range(step_count):
            step = {
                "action": self._generate_test_action(i + 1),
                "data": self._generate_test_data(i + 1),
                "result": self._generate_expected_result(i + 1)
            }
            steps.append(step)

        return {
            "summary": f"{self._get_unique_id()}_{complexity.title()}_Test",
            "test_type": "Manual",
            "priority": random.choice(template["priorities"]),
            "description": random.choice(template["descriptions"]),
            "steps": steps
        }

    def generate_bdd_test_case(self, feature_type: str = "web") -> Dict[str, Any]:
        """
        Generate BDD/Cucumber test case data.

        Args:
            feature_type: "web", "api", "mobile", "integration"
        """
        feature_templates = {
            "web": {
                "features": ["User Authentication", "Shopping Cart", "Product Search", "User Profile"],
                "backgrounds": [
                    "Given I am on the website homepage\nAnd the page is fully loaded",
                    "Given I am logged in as a registered user\nAnd I have access to all features"
                ],
                "scenarios": [
                    self._generate_web_scenarios,
                    self._generate_form_scenarios
                ]
            },
            "api": {
                "features": ["REST API Authentication", "Data Retrieval", "CRUD Operations"],
                "backgrounds": [
                    "Given I have access to the API\nAnd I have valid authentication credentials",
                    "Given the API service is running\nAnd the database is accessible"
                ],
                "scenarios": [
                    self._generate_api_scenarios,
                    self._generate_crud_scenarios
                ]
            },
            "mobile": {
                "features": ["Mobile Navigation", "Touch Interactions", "Device Features"],
                "backgrounds": [
                    "Given I have the mobile app installed\nAnd I have granted necessary permissions",
                    "Given the device is connected to the internet\nAnd the app is logged in"
                ],
                "scenarios": [
                    self._generate_mobile_scenarios,
                    self._generate_device_scenarios
                ]
            }
        }

        template = feature_templates[feature_type]
        feature_name = random.choice(template["features"])
        background = random.choice(template["backgrounds"])
        scenario_generator = random.choice(template["scenarios"])

        scenarios = scenario_generator()

        gherkin = f'''Feature: {feature_name}

Background:
    {background}

{scenarios}'''

        return {
            "summary": f"{self._get_unique_id()}_{feature_type.title()}_BDD_Test",
            "test_type": "Cucumber",
            "priority": "High",
            "gherkin": gherkin,
            "description": f"BDD test for {feature_name} functionality in {feature_type} context"
        }

    def generate_test_execution_data(self, test_count: int = 5) -> Dict[str, Any]:
        """Generate test execution with specified number of tests."""
        environments = [
            ["Development"],
            ["Staging", "UAT"],
            ["Production"],
            ["Development", "Staging", "UAT"],
            ["Integration", "Performance"]
        ]

        execution_types = [
            ("Smoke Test", "Quick validation of critical functionality"),
            ("Regression Test", "Comprehensive testing of existing functionality"),
            ("Feature Test", "Focused testing of new feature implementation"),
            ("Integration Test", "End-to-end testing of integrated systems"),
            ("Performance Test", "Load and performance validation"),
            ("Security Test", "Security vulnerability assessment")
        ]

        exec_type, description = random.choice(execution_types)

        return {
            "summary": f"{self._get_unique_id()}_{exec_type.replace(' ', '_')}",
            "description": f"{description} - Execution containing {test_count} test cases",
            "test_environments": random.choice(environments)
        }

    def generate_test_plan_data(self, plan_type: str = "release") -> Dict[str, Any]:
        """
        Generate test plan data.

        Args:
            plan_type: "release", "sprint", "feature", "maintenance"
        """
        plan_templates = {
            "release": {
                "summary_templates": [
                    "Release {version} Test Plan",
                    "Version {version} Validation Plan",
                    "Release {version} QA Strategy"
                ],
                "descriptions": [
                    "Comprehensive test plan for major release covering all features and regression testing",
                    "Full validation plan including functional, performance, and security testing",
                    "End-to-end testing strategy for production release readiness"
                ]
            },
            "sprint": {
                "summary_templates": [
                    "Sprint {number} Test Plan",
                    "Sprint {number} QA Plan",
                    "Iteration {number} Testing"
                ],
                "descriptions": [
                    "Focused test plan for sprint deliverables and user stories",
                    "Agile testing plan covering new features and bug fixes",
                    "Sprint validation including acceptance criteria testing"
                ]
            },
            "feature": {
                "summary_templates": [
                    "{feature} Feature Test Plan",
                    "{feature} Implementation Testing",
                    "{feature} Validation Plan"
                ],
                "descriptions": [
                    "Comprehensive testing plan for new feature implementation",
                    "Feature-specific test plan covering all acceptance criteria",
                    "Detailed validation plan for feature functionality and integration"
                ]
            }
        }

        template = plan_templates[plan_type]

        # Generate context-specific variables
        if plan_type == "release":
            version = f"{random.randint(1, 5)}.{random.randint(0, 9)}"
            summary = random.choice(template["summary_templates"]).format(version=version)
        elif plan_type == "sprint":
            number = random.randint(1, 20)
            summary = random.choice(template["summary_templates"]).format(number=number)
        else:  # feature
            features = ["Authentication", "Payment", "Search", "Reporting", "Integration"]
            feature = random.choice(features)
            summary = random.choice(template["summary_templates"]).format(feature=feature)

        return {
            "summary": f"{self._get_unique_id()}_{summary.replace(' ', '_')}",
            "description": random.choice(template["descriptions"])
        }

    def generate_performance_test_data(self) -> List[Dict[str, Any]]:
        """Generate test data for performance testing scenarios."""
        test_data = []

        # Create tests with varying complexity
        for i in range(10):
            complexity = ["simple", "medium", "complex"][i % 3]
            test_data.append(self.generate_manual_test_case(complexity))

        return test_data

    def generate_multilingual_test_data(self) -> List[Dict[str, Any]]:
        """Generate test data with various languages and special characters."""
        multilingual_data = [
            {
                "language": "Chinese",
                "summary": f"{self._get_unique_id()}_测试用例_中文",
                "description": "这是一个包含中文字符的测试用例，用于验证系统对多语言的支持",
                "steps": [
                    {
                        "action": "验证中文输入功能",
                        "data": "输入中文字符：你好世界",
                        "result": "系统正确处理中文输入"
                    }
                ]
            },
            {
                "language": "Arabic",
                "summary": f"{self._get_unique_id()}_اختبار_عربي",
                "description": "هذه حالة اختبار تحتوي على أحرف عربية للتحقق من دعم النظام للغات المختلفة",
                "steps": [
                    {
                        "action": "التحقق من وظيفة الإدخال العربي",
                        "data": "إدخال نص عربي: مرحبا بالعالم",
                        "result": "النظام يعالج الإدخال العربي بشكل صحيح"
                    }
                ]
            },
            {
                "language": "Emoji",
                "summary": f"{self._get_unique_id()}_🧪_Test_With_Emojis_🚀",
                "description": "Test case with various emojis: 👍 👎 ⚠️ 🔥 💡 📝 ✅ ❌ 🎯 🔍",
                "steps": [
                    {
                        "action": "Test emoji handling 🧪",
                        "data": "Input: Hello World! 🌍 👋",
                        "result": "Emojis displayed correctly ✅"
                    }
                ]
            },
            {
                "language": "Special Characters",
                "summary": f"{self._get_unique_id()}_Special_Chars_<>&\"'",
                "description": "Test with HTML/XML special characters: < > & \" ' and accented: àáâãäåæçèéêë",
                "steps": [
                    {
                        "action": "Input special characters: <script>alert('test')</script>",
                        "data": "Data with quotes: \"double\" and 'single'",
                        "result": "Special characters handled safely"
                    }
                ]
            }
        ]

        for data in multilingual_data:
            data.update({
                "test_type": "Manual",
                "priority": "Medium"
            })

        return multilingual_data

    def generate_edge_case_test_data(self) -> List[Dict[str, Any]]:
        """Generate test data for edge cases and boundary conditions."""
        edge_cases = [
            {
                "case": "empty_content",
                "summary": f"{self._get_unique_id()}_Empty_Content_Test",
                "description": "",
                "steps": []
            },
            {
                "case": "minimal_content",
                "summary": "X",  # Single character
                "description": "Minimal test case with single character summary",
                "steps": [{"action": "A", "data": "B", "result": "C"}]
            },
            {
                "case": "maximum_content",
                "summary": f"{self._get_unique_id()}_" + "X" * 200,  # Long summary
                "description": "Very long description. " * 100,  # ~2KB description
                "steps": [
                    {
                        "action": f"Long action description. " * 20,
                        "data": f"Long test data. " * 30,
                        "result": f"Long expected result. " * 25
                    }
                ]
            },
            {
                "case": "special_formatting",
                "summary": f"{self._get_unique_id()}_Formatting_Test",
                "description": """Test with various formatting:

                - Bullet points
                - Multiple lines

                1. Numbered lists
                2. More items

                **Bold text** and *italic text*

                Code blocks:
                ```javascript
                function test() {
                    return "formatted content";
                }
                ```

                Links: https://example.com
                """,
                "steps": [
                    {
                        "action": "Test formatting preservation",
                        "data": "Input: **bold**, *italic*, `code`",
                        "result": "Formatting preserved correctly"
                    }
                ]
            }
        ]

        for case in edge_cases:
            case.update({
                "test_type": "Manual",
                "priority": "Low"
            })

        return edge_cases

    def generate_realistic_project_data(self) -> Dict[str, List[Dict[str, Any]]]:
        """Generate a complete realistic project dataset."""
        project_data = {
            "tests": [],
            "executions": [],
            "plans": []
        }

        # Generate diverse test cases
        for _ in range(5):
            project_data["tests"].append(self.generate_manual_test_case("simple"))
        for _ in range(3):
            project_data["tests"].append(self.generate_manual_test_case("medium"))
        for _ in range(2):
            project_data["tests"].append(self.generate_manual_test_case("complex"))

        # Generate BDD tests
        for feature_type in ["web", "api", "mobile"]:
            project_data["tests"].append(self.generate_bdd_test_case(feature_type))

        # Generate multilingual tests
        project_data["tests"].extend(self.generate_multilingual_test_data()[:2])

        # Generate executions
        for _ in range(3):
            project_data["executions"].append(self.generate_test_execution_data())

        # Generate plans
        for plan_type in ["release", "sprint", "feature"]:
            project_data["plans"].append(self.generate_test_plan_data(plan_type))

        return project_data

    # Helper methods for generating specific content

    def _generate_test_action(self, step_number: int) -> str:
        """Generate realistic test action."""
        actions = [
            f"Navigate to page {step_number}",
            f"Click on button {step_number}",
            f"Enter data in field {step_number}",
            f"Verify element {step_number} is displayed",
            f"Submit form {step_number}",
            f"Select option {step_number}",
            f"Upload file {step_number}",
            f"Download report {step_number}",
            f"Validate data {step_number}",
            f"Check response {step_number}"
        ]
        return random.choice(actions)

    def _generate_test_data(self, step_number: int) -> str:
        """Generate realistic test data."""
        data_options = [
            f"test_data_{step_number}@example.com",
            f"Sample text for step {step_number}",
            f"File_{step_number}.pdf",
            f"Value: {random.randint(1, 100)}",
            f"Option {step_number}",
            f"URL: https://example.com/page{step_number}",
            f"JSON: {{\"id\": {step_number}, \"name\": \"test\"}}",
            f"Query: SELECT * FROM table WHERE id = {step_number}"
        ]
        return random.choice(data_options)

    def _generate_expected_result(self, step_number: int) -> str:
        """Generate realistic expected result."""
        results = [
            f"Page {step_number} loads successfully",
            f"Button {step_number} action completes",
            f"Data saved correctly in step {step_number}",
            f"Element {step_number} displayed as expected",
            f"Form {step_number} submission successful",
            f"Option {step_number} selected correctly",
            f"File {step_number} uploaded successfully",
            f"Report {step_number} downloaded",
            f"Data {step_number} validation passes",
            f"Response {step_number} contains expected values"
        ]
        return random.choice(results)

    def _generate_web_scenarios(self) -> str:
        """Generate web-specific BDD scenarios."""
        return '''@web @authentication
Scenario: User login with valid credentials
    Given I am on the login page
    When I enter valid username "user@example.com"
    And I enter valid password "securepass123"
    And I click the login button
    Then I should be redirected to the dashboard
    And I should see a welcome message

@web @validation @error-handling
Scenario: Login with invalid credentials
    Given I am on the login page
    When I enter invalid username "invalid@example.com"
    And I enter invalid password "wrongpass"
    And I click the login button
    Then I should remain on the login page
    And I should see an error message "Invalid credentials"'''

    def _generate_form_scenarios(self) -> str:
        """Generate form-specific BDD scenarios."""
        return '''@form @validation
Scenario Outline: Form validation with different inputs
    Given I am on the registration form
    When I enter "<field>" with value "<value>"
    Then I should see validation result "<result>"

    Examples:
    | field    | value              | result  |
    | email    | valid@example.com  | valid   |
    | email    | invalid-email      | invalid |
    | phone    | +1-555-123-4567   | valid   |
    | phone    | 123                | invalid |'''

    def _generate_api_scenarios(self) -> str:
        """Generate API-specific BDD scenarios."""
        return '''@api @crud
Scenario: Create user via API
    Given I have valid API credentials
    When I send a POST request to "/api/users"
    And the request body contains:
        """
        {
            "name": "John Doe",
            "email": "john@example.com"
        }
        """
    Then I should receive a 201 status code
    And the response should contain the created user ID'''

    def _generate_crud_scenarios(self) -> str:
        """Generate CRUD-specific scenarios."""
        return '''@api @data-retrieval
Scenario: Retrieve user data
    Given a user exists with ID "12345"
    When I send a GET request to "/api/users/12345"
    Then I should receive a 200 status code
    And the response should contain user details
    And the user email should be "john@example.com"'''

    def _generate_mobile_scenarios(self) -> str:
        """Generate mobile-specific scenarios."""
        return '''@mobile @navigation
Scenario: Navigate through mobile app
    Given I am on the mobile app home screen
    When I tap on the menu button
    And I select "Profile" from the menu
    Then the profile screen should be displayed
    And I should see my user information'''

    def _generate_device_scenarios(self) -> str:
        """Generate device-specific scenarios."""
        return '''@mobile @device-features
Scenario: Use device camera feature
    Given I have camera permissions granted
    When I tap the "Take Photo" button
    And I capture a photo using the device camera
    Then the photo should be saved to the gallery
    And I should see a confirmation message'''


# Convenience functions for easy access

def create_test_generator(prefix: Optional[str] = None) -> TestDataGenerator:
    """Create a new test data generator instance."""
    return TestDataGenerator(prefix)


def generate_sample_manual_tests(count: int = 5, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
    """Generate sample manual test cases."""
    generator = create_test_generator(prefix)
    return [generator.generate_manual_test_case() for _ in range(count)]


def generate_sample_bdd_tests(count: int = 3, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
    """Generate sample BDD test cases."""
    generator = create_test_generator(prefix)
    feature_types = ["web", "api", "mobile"]
    return [generator.generate_bdd_test_case(feature_types[i % len(feature_types)]) for i in range(count)]


def generate_complete_project_dataset(prefix: Optional[str] = None) -> Dict[str, List[Dict[str, Any]]]:
    """Generate a complete project dataset with tests, executions, and plans."""
    generator = create_test_generator(prefix)
    return generator.generate_realistic_project_data()


def generate_multilingual_dataset(prefix: Optional[str] = None) -> List[Dict[str, Any]]:
    """Generate multilingual test data."""
    generator = create_test_generator(prefix)
    return generator.generate_multilingual_test_data()


def generate_edge_case_dataset(prefix: Optional[str] = None) -> List[Dict[str, Any]]:
    """Generate edge case test data."""
    generator = create_test_generator(prefix)
    return generator.generate_edge_case_test_data()


def generate_performance_dataset(count: int = 10, prefix: Optional[str] = None) -> List[Dict[str, Any]]:
    """Generate performance testing dataset."""
    generator = create_test_generator(prefix)
    return generator.generate_performance_test_data()


# Test data validation helpers

def validate_test_data(test_data: Dict[str, Any]) -> List[str]:
    """Validate test data structure and return list of issues."""
    issues = []

    required_fields = ["summary", "test_type"]
    for field in required_fields:
        if field not in test_data or not test_data[field]:
            issues.append(f"Missing required field: {field}")

    if test_data.get("test_type") == "Manual" and "steps" in test_data:
        steps = test_data["steps"]
        if not isinstance(steps, list):
            issues.append("Steps should be a list")
        else:
            for i, step in enumerate(steps):
                if not isinstance(step, dict):
                    issues.append(f"Step {i+1} should be a dictionary")
                else:
                    step_fields = ["action", "data", "result"]
                    for field in step_fields:
                        if field not in step:
                            issues.append(f"Step {i+1} missing field: {field}")

    if test_data.get("test_type") == "Cucumber" and "gherkin" in test_data:
        gherkin = test_data["gherkin"]
        if not isinstance(gherkin, str):
            issues.append("Gherkin should be a string")
        elif "Feature:" not in gherkin:
            issues.append("Gherkin should contain 'Feature:' keyword")

    return issues