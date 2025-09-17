"""
Integration tests for BDD conversion workflow.

Tests complex workflows for converting requirements to BDD format
and managing Cucumber/Gherkin tests. Covers use cases UC-011 through UC-020.
"""

import pytest
import pytest_asyncio
from datetime import datetime
from typing import Dict, Any, List

from src.server import create_server
from src.tools.xray_tool import XrayTool


@pytest.fixture
def unique_prefix():
    """Generate unique prefix for test names."""
    return f"BDDConversion_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


@pytest.fixture
def project_key():
    """Get project key from environment."""
    import os
    return os.getenv('XRAY_PROJECT_KEY', 'FTEST')


@pytest.mark.asyncio
class TestBDDConversionWorkflow:
    """Test complete BDD conversion and management workflows."""

    async def test_user_story_to_gherkin_conversion(self, tool, unique_prefix, project_key):
        """
        UC-011: Convert user story to Gherkin format.

        Tests the complete workflow of:
        1. Taking a user story description
        2. Converting it to proper Gherkin format
        3. Creating Cucumber test with the Gherkin
        4. Validating the Gherkin syntax
        5. Linking to requirements
        """
        created_resources = []

        try:
            # Step 1: Define user stories to convert
            user_stories = [
                {
                    'id': 'US-001',
                    'title': 'User Login Authentication',
                    'description': '''
                    As a registered user
                    I want to log into the system with my credentials
                    So that I can access my personal dashboard and data

                    Acceptance Criteria:
                    - User can enter username and password
                    - System validates credentials against database
                    - Upon successful login, user is redirected to dashboard
                    - Upon failed login, appropriate error message is shown
                    - User session is created and maintained
                    ''',
                    'gherkin': '''Feature: User Login Authentication

@authentication @login
Scenario: Successful user login with valid credentials
    Given I am on the login page
    And I have a registered account with username "testuser@example.com" and password "SecurePass123"
    When I enter my username "testuser@example.com"
    And I enter my password "SecurePass123"
    And I click the "Login" button
    Then I should be redirected to the dashboard page
    And I should see a welcome message "Welcome back, Test User"
    And my user session should be active

@authentication @login @error-handling
Scenario: Failed login with invalid credentials
    Given I am on the login page
    When I enter an invalid username "invalid@example.com"
    And I enter an invalid password "wrongpassword"
    And I click the "Login" button
    Then I should remain on the login page
    And I should see an error message "Invalid username or password"
    And no user session should be created

@authentication @login @validation
Scenario Outline: Login validation with different invalid inputs
    Given I am on the login page
    When I enter username "<username>"
    And I enter password "<password>"
    And I click the "Login" button
    Then I should see the error message "<error_message>"

    Examples:
    | username              | password      | error_message                    |
    | ""                    | "password123" | "Username is required"           |
    | "user@example.com"    | ""            | "Password is required"           |
    | "invalid-email"       | "password123" | "Please enter a valid email"     |
    | "user@example.com"    | "123"         | "Password must be at least 8 characters" |'''
                },
                {
                    'id': 'US-002',
                    'title': 'Shopping Cart Management',
                    'description': '''
                    As a customer
                    I want to add products to my shopping cart
                    So that I can purchase multiple items in a single transaction

                    Acceptance Criteria:
                    - User can add products to cart from product listings
                    - Cart displays all added products with quantities
                    - User can update quantities or remove products
                    - Cart total is calculated correctly including tax
                    ''',
                    'gherkin': '''Feature: Shopping Cart Management

@shopping-cart @product-management
Scenario: Add single product to empty cart
    Given I am logged in as a customer
    And my shopping cart is empty
    And I am viewing a product "Wireless Headphones" priced at $99.99
    When I click the "Add to Cart" button
    Then the product should be added to my cart
    And my cart should contain 1 item
    And the cart total should be $99.99

@shopping-cart @product-management
Scenario: Add multiple products to cart
    Given I am logged in as a customer
    And my shopping cart is empty
    When I add "Wireless Headphones" priced at $99.99 to my cart
    And I add "Phone Case" priced at $19.99 to my cart
    And I add "Screen Protector" priced at $9.99 to my cart
    Then my cart should contain 3 items
    And the cart subtotal should be $129.97

@shopping-cart @quantity-management
Scenario: Update product quantity in cart
    Given I have "Wireless Headphones" in my cart with quantity 1
    When I change the quantity to 2
    Then the cart should show 2 "Wireless Headphones"
    And the line total should be $199.98
    And the cart total should be updated accordingly

@shopping-cart @product-removal
Scenario: Remove product from cart
    Given I have multiple products in my cart
    And one product is "Phone Case" priced at $19.99
    When I click "Remove" next to "Phone Case"
    Then "Phone Case" should be removed from my cart
    And the cart total should be reduced by $19.99'''
                }
            ]

            # Step 2: Create Cucumber tests from converted Gherkin
            created_test_ids = []
            for story in user_stories:
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': f'{unique_prefix}_{story["id"]}_{story["title"].replace(" ", "_")}',
                    'test_type': 'Cucumber',
                    'priority': 'High',
                    'gherkin': story['gherkin'],
                    'description': f'''BDD Test converted from User Story {story["id"]}

Original Story:
{story["description"]}

This test covers the acceptance criteria through Gherkin scenarios with proper tagging and examples.'''
                })

                assert result['success'], f"Failed to create BDD test for {story['id']}: {result.get('errors', [])}"
                test_id = result['data']['issueId']
                created_test_ids.append(test_id)
                created_resources.append(('test', test_id))

            assert len(created_test_ids) == 2, "Should have created 2 BDD tests from user stories"

            # Step 3: Verify Gherkin content is properly stored
            for i, test_id in enumerate(created_test_ids):
                test_details = await tool.execute({
                    'entity': 'test',
                    'action': 'get',
                    'issue_id': test_id
                })

                assert test_details['success'], f"Should retrieve test details for {test_id}"
                test_data = test_details['data']['test']

                # Verify test type is Cucumber
                assert test_data['testType']['name'] == 'Cucumber', "Test should be Cucumber type"

                # Verify Gherkin content exists
                gherkin_content = test_data.get('unstructuredDefinition', '')
                assert 'Feature:' in gherkin_content, "Gherkin should contain Feature definition"
                assert 'Scenario:' in gherkin_content, "Gherkin should contain Scenario definitions"
                assert 'Given' in gherkin_content, "Gherkin should contain Given steps"
                assert 'When' in gherkin_content, "Gherkin should contain When steps"
                assert 'Then' in gherkin_content, "Gherkin should contain Then steps"

                # Verify tags are present
                if i == 0:  # Login test
                    assert '@authentication' in gherkin_content, "Should contain authentication tags"
                    assert '@login' in gherkin_content, "Should contain login tags"
                elif i == 1:  # Shopping cart test
                    assert '@shopping-cart' in gherkin_content, "Should contain shopping-cart tags"

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    async def test_feature_file_with_multiple_scenarios(self, tool, unique_prefix, project_key):
        """
        UC-012: Create feature file with multiple scenarios.

        Tests creating comprehensive feature files with multiple related scenarios.
        """
        created_resources = []

        try:
            # Create a comprehensive feature with multiple scenarios
            comprehensive_feature = '''Feature: E-commerce Product Search

  As a customer
  I want to search for products
  So that I can find items I want to purchase

  Background:
    Given I am on the e-commerce website
    And the product catalog is loaded
    And I have access to the search functionality

  @search @basic @smoke
  Scenario: Basic product search with valid term
    Given I am on the homepage
    When I enter "laptop" in the search box
    And I click the search button
    Then I should see a list of laptop products
    And the results should be sorted by relevance
    And each result should contain product name, price, and image

  @search @filters @advanced
  Scenario: Advanced search with filters
    Given I am on the search results page for "laptop"
    When I apply the following filters:
      | Filter Type | Value       |
      | Brand       | Dell        |
      | Price Range | $500-$1000  |
      | Rating      | 4+ stars    |
    Then the results should be filtered accordingly
    And I should see only Dell laptops in the specified price range
    And all displayed products should have 4+ star ratings

  @search @no-results @edge-case
  Scenario: Search with no results
    Given I am on the homepage
    When I search for "nonexistentproduct12345"
    Then I should see a "No results found" message
    And I should see suggested alternative searches
    And I should see popular product categories

  @search @pagination @performance
  Scenario: Search results pagination
    Given I am on the search results page for "electronics"
    And there are more than 20 results
    When I click on page 2
    Then I should see the next set of results
    And the page should load within 3 seconds
    And the URL should reflect the current page number

  @search @autocomplete @usability
  Scenario Outline: Search autocomplete functionality
    Given I am on the homepage
    When I type "<partial_term>" in the search box
    Then I should see autocomplete suggestions
    And the suggestions should contain "<expected_suggestion>"

    Examples:
      | partial_term | expected_suggestion |
      | lap          | laptop              |
      | iph          | iphone              |
      | sam          | samsung             |
      | book         | books               |

  @search @special-characters @validation
  Scenario: Search with special characters
    Given I am on the homepage
    When I search for "C++ programming"
    Then the search should handle the special characters correctly
    And I should see programming-related results
    And the search term should be preserved in the search box'''

            # Create the comprehensive feature test
            result = await tool.execute({
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Comprehensive_Product_Search_Feature',
                'test_type': 'Cucumber',
                'priority': 'High',
                'gherkin': comprehensive_feature,
                'description': '''Comprehensive product search feature covering:
- Basic search functionality
- Advanced filtering
- Edge cases and error handling
- Performance requirements
- Usability features (autocomplete)
- Special character handling

This feature demonstrates proper Gherkin structure with:
- Background steps
- Multiple scenario types
- Scenario outlines with examples
- Proper tagging strategy
- Data tables
- Clear Given-When-Then structure'''
            })

            assert result['success'], f"Failed to create comprehensive feature: {result.get('errors', [])}"
            test_id = result['data']['issueId']
            created_resources.append(('test', test_id))

            # Verify the feature contains all expected elements
            test_details = await tool.execute({
                'entity': 'test',
                'action': 'get',
                'issue_id': test_id
            })

            assert test_details['success'], "Should retrieve comprehensive feature details"
            gherkin_content = test_details['data']['test']['unstructuredDefinition']

            # Verify structure elements
            assert 'Background:' in gherkin_content, "Should contain Background section"
            assert gherkin_content.count('Scenario:') == 4, "Should contain 4 regular scenarios"
            assert gherkin_content.count('Scenario Outline:') == 2, "Should contain 2 scenario outlines"
            assert 'Examples:' in gherkin_content, "Should contain Examples tables"
            assert '| Filter Type | Value       |' in gherkin_content, "Should contain data tables"

            # Verify tags are properly distributed
            expected_tags = ['@search', '@basic', '@smoke', '@filters', '@advanced',
                           '@no-results', '@edge-case', '@pagination', '@performance',
                           '@autocomplete', '@usability', '@special-characters', '@validation']

            for tag in expected_tags:
                assert tag in gherkin_content, f"Should contain {tag} tag"

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    async def test_scenario_outline_with_examples(self, tool, unique_prefix, project_key):
        """
        UC-013: Create scenario outline with examples table.

        Tests creating data-driven tests using Scenario Outline and Examples.
        """
        created_resources = []

        try:
            # Create data-driven test scenarios
            data_driven_features = [
                {
                    'name': f'{unique_prefix}_Login_Validation_DataDriven',
                    'gherkin': '''Feature: Login Data Validation

@data-driven @validation @login
Scenario Outline: Login validation with various input combinations
    Given I am on the login page
    When I enter username "<username>"
    And I enter password "<password>"
    And I click the login button
    Then I should see the result "<expected_result>"
    And the status should be "<status>"

    Examples: Valid credentials
    | username            | password      | expected_result      | status  |
    | admin@test.com      | AdminPass123  | Welcome Dashboard    | success |
    | user@test.com       | UserPass456   | Welcome Dashboard    | success |
    | manager@test.com    | ManagerPass789| Welcome Dashboard    | success |

    Examples: Invalid credentials
    | username            | password      | expected_result           | status |
    | invalid@test.com    | wrongpass     | Invalid credentials       | error  |
    | ""                  | password123   | Username required         | error  |
    | user@test.com       | ""            | Password required         | error  |
    | notanemail          | password123   | Invalid email format      | error  |

    Examples: Security test cases
    | username            | password           | expected_result           | status |
    | admin@test.com      | password123        | Password too weak         | error  |
    | user@test.com       | 123                | Password too short        | error  |
    | test@test.com       | ' OR '1'='1        | Invalid characters        | error  |'''
                },
                {
                    'name': f'{unique_prefix}_Payment_Processing_DataDriven',
                    'gherkin': '''Feature: Payment Processing Validation

@data-driven @payment @financial
Scenario Outline: Process payments with different card types and amounts
    Given I am logged in as a customer
    And I have items totaling $<cart_total> in my cart
    When I enter card number "<card_number>"
    And I enter expiry date "<expiry_date>"
    And I enter CVV "<cvv>"
    And I enter cardholder name "<cardholder_name>"
    And I click "Process Payment"
    Then the payment should be "<result>"
    And I should see the message "<message>"

    Examples: Valid payments
    | cart_total | card_number      | expiry_date | cvv | cardholder_name | result    | message                    |
    | 25.99      | 4111111111111111 | 12/25       | 123 | John Smith      | processed | Payment successful         |
    | 99.99      | 5555555555554444 | 06/26       | 456 | Jane Doe        | processed | Payment successful         |
    | 199.99     | 378282246310005  | 03/25       | 789 | Bob Johnson     | processed | Payment successful         |

    Examples: Invalid payments
    | cart_total | card_number      | expiry_date | cvv | cardholder_name | result   | message                     |
    | 25.99      | 1234567890123456 | 12/25       | 123 | John Smith      | declined | Invalid card number         |
    | 99.99      | 4111111111111111 | 12/20       | 456 | Jane Doe        | declined | Card expired                |
    | 199.99     | 4111111111111111 | 12/25       | 12  | Bob Johnson     | declined | Invalid CVV                 |
    | 0.00       | 4111111111111111 | 12/25       | 123 | John Smith      | declined | Invalid amount              |

    Examples: Edge cases
    | cart_total | card_number      | expiry_date | cvv | cardholder_name | result   | message                     |
    | 9999.99    | 4111111111111111 | 12/25       | 123 | John Smith      | declined | Amount exceeds limit        |
    | 25.99      | 4111111111111111 | 12/25       | 123 | ""              | declined | Cardholder name required    |'''
                }
            ]

            created_test_ids = []
            for feature_data in data_driven_features:
                result = await tool.execute({
                    'entity': 'test',
                    'action': 'create',
                    'project_key': project_key,
                    'summary': feature_data['name'],
                    'test_type': 'Cucumber',
                    'priority': 'High',
                    'gherkin': feature_data['gherkin'],
                    'description': 'Data-driven test using Scenario Outline with multiple Examples tables for comprehensive coverage'
                })

                assert result['success'], f"Failed to create data-driven test: {result.get('errors', [])}"
                test_id = result['data']['issueId']
                created_test_ids.append(test_id)
                created_resources.append(('test', test_id))

            # Verify data-driven tests structure
            for test_id in created_test_ids:
                test_details = await tool.execute({
                    'entity': 'test',
                    'action': 'get',
                    'issue_id': test_id
                })

                assert test_details['success'], "Should retrieve data-driven test details"
                gherkin_content = test_details['data']['test']['unstructuredDefinition']

                # Verify Scenario Outline structure
                assert 'Scenario Outline:' in gherkin_content, "Should contain Scenario Outline"
                assert gherkin_content.count('Examples:') >= 2, "Should contain multiple Examples tables"
                assert '<' in gherkin_content and '>' in gherkin_content, "Should contain parameter placeholders"
                assert '|' in gherkin_content, "Should contain table structure"

                # Verify data tables have headers and data rows
                lines = gherkin_content.split('\n')
                examples_sections = [i for i, line in enumerate(lines) if 'Examples:' in line]

                for examples_index in examples_sections:
                    # Should have header row and at least one data row after Examples:
                    header_line = None
                    data_rows = 0

                    for i in range(examples_index + 1, len(lines)):
                        line = lines[i].strip()
                        if not line:
                            continue
                        if line.startswith('|') and line.endswith('|'):
                            if header_line is None:
                                header_line = line
                            else:
                                data_rows += 1
                        elif line.startswith('Examples:') or line.startswith('Scenario'):
                            break

                    assert header_line is not None, "Examples should have header row"
                    assert data_rows > 0, "Examples should have data rows"

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    async def test_gherkin_syntax_validation(self, tool, unique_prefix, project_key):
        """
        UC-018: Validate Gherkin syntax during creation.

        Tests validation of Gherkin syntax and proper error handling.
        """
        created_resources = []

        try:
            # Test cases with valid and invalid Gherkin
            gherkin_test_cases = [
                {
                    'name': f'{unique_prefix}_Valid_Gherkin_Structure',
                    'gherkin': '''Feature: Valid Gherkin Example

This is a properly structured Gherkin feature file.

@smoke @valid
Scenario: Proper Gherkin syntax
    Given I have a valid Gherkin structure
    When I create a test with this structure
    Then it should be accepted by the system
    And no syntax errors should occur''',
                    'should_succeed': True,
                    'description': 'Valid Gherkin with proper structure'
                },
                {
                    'name': f'{unique_prefix}_Valid_Complex_Gherkin',
                    'gherkin': '''Feature: Complex Valid Gherkin

Background:
    Given the system is initialized
    And the database is connected

@complex @valid @background
Scenario: Complex scenario with background
    Given I have completed the background steps
    When I perform the main action
    Then the result should be correct

@valid @outline
Scenario Outline: Valid scenario outline
    Given I have "<input>"
    When I process it
    Then I get "<output>"

    Examples:
    | input | output |
    | hello | HELLO  |
    | world | WORLD  |''',
                    'should_succeed': True,
                    'description': 'Complex valid Gherkin with Background and Scenario Outline'
                },
                # Note: Testing invalid Gherkin requires the system to actually validate it
                # For now, we'll focus on valid Gherkin structures and test the creation
                {
                    'name': f'{unique_prefix}_Edge_Case_Gherkin',
                    'gherkin': '''Feature: Edge Case Gherkin

@edge-case
Scenario: Scenario with special characters and unicode
    Given I have text with special characters: !@#$%^&*()
    And I have unicode characters: 你好, ñoño, café
    When I process this text "with quotes" and 'single quotes'
    Then the system should handle it correctly
    And preserve all characters: <tag>content</tag>''',
                    'should_succeed': True,
                    'description': 'Gherkin with special characters and unicode'
                }
            ]

            created_test_ids = []
            for test_case in gherkin_test_cases:
                if test_case['should_succeed']:
                    result = await tool.execute({
                        'entity': 'test',
                        'action': 'create',
                        'project_key': project_key,
                        'summary': test_case['name'],
                        'test_type': 'Cucumber',
                        'priority': 'Medium',
                        'gherkin': test_case['gherkin'],
                        'description': test_case['description']
                    })

                    assert result['success'], f"Valid Gherkin should be accepted: {result.get('errors', [])}"
                    test_id = result['data']['issueId']
                    created_test_ids.append(test_id)
                    created_resources.append(('test', test_id))

                    # Verify the Gherkin was stored correctly
                    test_details = await tool.execute({
                        'entity': 'test',
                        'action': 'get',
                        'issue_id': test_id
                    })

                    assert test_details['success'], "Should retrieve test with Gherkin"
                    stored_gherkin = test_details['data']['test']['unstructuredDefinition']

                    # Basic validation that content was preserved
                    assert 'Feature:' in stored_gherkin, "Feature keyword should be preserved"
                    assert 'Scenario:' in stored_gherkin, "Scenario keyword should be preserved"

                    # Verify structure keywords are present
                    if 'Background:' in test_case['gherkin']:
                        assert 'Background:' in stored_gherkin, "Background should be preserved"
                    if 'Scenario Outline:' in test_case['gherkin']:
                        assert 'Scenario Outline:' in stored_gherkin, "Scenario Outline should be preserved"
                    if 'Examples:' in test_case['gherkin']:
                        assert 'Examples:' in stored_gherkin, "Examples should be preserved"

            assert len(created_test_ids) == 3, "Should have created 3 valid Gherkin tests"

            # Test Gherkin content update
            update_gherkin = '''Feature: Updated Gherkin Content

@updated @version-2
Scenario: Updated scenario content
    Given the test has been updated
    When I retrieve the test content
    Then it should reflect the changes
    And maintain proper Gherkin structure'''

            update_result = await tool.execute({
                'entity': 'test',
                'action': 'update_content',
                'issue_id': created_test_ids[0],
                'gherkin': update_gherkin
            })

            assert update_result['success'], "Should update Gherkin content"

            # Verify update was applied
            updated_test = await tool.execute({
                'entity': 'test',
                'action': 'get',
                'issue_id': created_test_ids[0]
            })

            assert updated_test['success'], "Should retrieve updated test"
            updated_content = updated_test['data']['test']['unstructuredDefinition']
            assert '@updated' in updated_content, "Updated content should contain new tags"
            assert 'Updated scenario content' in updated_content, "Should contain updated scenario"

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass

    async def test_bdd_test_execution_workflow(self, tool, unique_prefix, project_key):
        """
        UC-019 & UC-020: Link scenarios to requirements and execute BDD tests.

        Tests linking BDD tests to requirements and executing them.
        """
        created_resources = []

        try:
            # Create BDD test linked to requirements
            requirement_linked_test = f'''Feature: User Registration System

This feature implements user registration functionality as per requirements REQ-001 and REQ-002.

@registration @requirements @req-001 @req-002
Scenario: Complete user registration process
    Given I am on the registration page
    And the registration form is displayed
    When I fill in the registration form with valid data:
        | Field            | Value                    |
        | First Name       | John                     |
        | Last Name        | Smith                    |
        | Email            | john.smith@example.com   |
        | Password         | SecurePassword123        |
        | Confirm Password | SecurePassword123        |
        | Terms Agreement  | true                     |
    And I submit the registration form
    Then my account should be created successfully
    And I should receive a confirmation email
    And I should be redirected to the welcome page
    And my profile should be accessible

@registration @validation @req-001
Scenario: Registration validation requirements
    Given I am on the registration page
    When I attempt to register with invalid data
    Then appropriate validation messages should be displayed
    And the account should not be created
    And no confirmation email should be sent

@registration @security @req-002
Scenario: Registration security requirements
    Given I am on the registration page
    When I enter a password that doesn't meet security requirements
    Then I should see a password strength indicator
    And I should see specific security requirement messages
    And the form should not be submittable until requirements are met'''

            # Create the BDD test
            bdd_test_result = await tool.execute({
                'entity': 'test',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_User_Registration_BDD_Requirements',
                'test_type': 'Cucumber',
                'priority': 'High',
                'gherkin': requirement_linked_test,
                'description': '''BDD test for user registration functionality

Requirements Coverage:
- REQ-001: User registration with validation
- REQ-002: Password security requirements

This test ensures all acceptance criteria are met through executable scenarios.'''
            })

            assert bdd_test_result['success'], "Should create requirements-linked BDD test"
            bdd_test_id = bdd_test_result['data']['issueId']
            created_resources.append(('test', bdd_test_id))

            # Create test execution for BDD tests
            bdd_execution_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_BDD_Requirements_Execution',
                'description': 'Execution of BDD tests for requirements validation',
                'test_environments': ['UAT', 'Staging']
            })

            assert bdd_execution_result['success'], "Should create BDD execution"
            execution_id = bdd_execution_result['data']['issueId']
            created_resources.append(('test_execution', execution_id))

            # Add BDD test to execution
            add_test_result = await tool.execute({
                'entity': 'test_execution',
                'action': 'add_tests',
                'issue_id': execution_id,
                'test_issue_ids': [bdd_test_id]
            })

            assert add_test_result['success'], "Should add BDD test to execution"

            # Execute BDD test scenarios with detailed results
            scenario_results = [
                {
                    'scenario': 'Complete user registration process',
                    'status': 'PASS',
                    'comment': 'All registration steps completed successfully. REQ-001 and REQ-002 satisfied.'
                }
            ]

            # Update test run with BDD execution results
            run_result = await tool.execute({
                'entity': 'test_run',
                'action': 'update_status',
                'test_execution_id': execution_id,
                'test_issue_id': bdd_test_id,
                'status': 'PASS',
                'comment': '''BDD Test Execution Results:

✓ Complete user registration process - PASSED
  - Registration form validation working
  - Account creation successful
  - Email confirmation sent
  - Welcome page redirection working
  - Profile accessibility confirmed

✓ Registration validation requirements - PASSED
  - Form validation working correctly
  - Invalid data properly rejected
  - Error messages displayed appropriately

✓ Registration security requirements - PASSED
  - Password strength validation implemented
  - Security requirements clearly communicated
  - Form submission properly controlled

Requirements Coverage:
✓ REQ-001: User registration with validation - SATISFIED
✓ REQ-002: Password security requirements - SATISFIED

All BDD scenarios passed. Requirements fully implemented and validated.'''
            })

            assert run_result['success'], "Should update BDD test run with results"

            # Verify BDD execution results
            execution_details = await tool.execute({
                'entity': 'test_execution',
                'action': 'get',
                'issue_id': execution_id
            })

            assert execution_details['success'], "Should retrieve BDD execution details"
            test_runs = execution_details['data']['testExecution']['testRuns']
            assert len(test_runs) == 1, "Should have 1 BDD test run"

            bdd_test_run = test_runs[0]
            assert bdd_test_run['status']['name'] == 'PASS', "BDD test should have passed"
            assert 'Requirements Coverage' in bdd_test_run['comment'], "Should contain requirements traceability"

            # Create test plan for requirements coverage
            coverage_plan_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'create',
                'project_key': project_key,
                'summary': f'{unique_prefix}_Requirements_Coverage_Plan',
                'description': 'Test plan for validating requirements coverage through BDD tests'
            })

            assert coverage_plan_result['success'], "Should create requirements coverage plan"
            plan_id = coverage_plan_result['data']['issueId']
            created_resources.append(('test_plan', plan_id))

            # Link BDD test and execution to coverage plan
            link_tests_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_tests',
                'issue_id': plan_id,
                'test_issue_ids': [bdd_test_id]
            })

            link_executions_result = await tool.execute({
                'entity': 'test_plan',
                'action': 'add_executions',
                'issue_id': plan_id,
                'test_exec_issue_ids': [execution_id]
            })

            assert link_tests_result['success'] and link_executions_result['success'], "Should link BDD artifacts to plan"

            # Verify complete requirements coverage workflow
            final_plan = await tool.execute({
                'entity': 'test_plan',
                'action': 'get',
                'issue_id': plan_id
            })

            assert final_plan['success'], "Should retrieve final coverage plan"
            plan_data = final_plan['data']['testPlan']
            assert len(plan_data['tests']) == 1, "Plan should contain 1 BDD test"
            assert len(plan_data['testExecutions']) == 1, "Plan should contain 1 execution"

        finally:
            # Cleanup
            for resource_type, resource_id in reversed(created_resources):
                try:
                    await tool.execute({
                        'entity': resource_type,
                        'action': 'delete',
                        'issue_id': resource_id
                    })
                except Exception:
                    pass