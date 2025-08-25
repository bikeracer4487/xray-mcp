#!/usr/bin/env python3
"""Quick test script to verify GraphQL injection protection is working."""

import sys
import asyncio
from validators.graphql_validator import GraphQLValidator, validate_graphql_query

def test_graphql_validation():
    """Test GraphQL validator with various attack scenarios."""
    validator = GraphQLValidator()
    
    print("Testing GraphQL validation security...")
    
    # Test 1: Valid query should pass
    valid_query = """
        query GetTest($issueId: String!) {
            getTest(issueId: $issueId) {
                issueId
                jira { key summary }
            }
        }
    """
    
    try:
        result = validator.validate_query(valid_query, {"issueId": "TEST-123"})
        print("✓ Valid query passed validation")
    except Exception as e:
        print(f"✗ Valid query failed: {e}")
        return False
    
    # Test 2: Schema introspection attack should be blocked
    introspection_query = """
        query IntrospectionQuery {
            __schema {
                queryType { name }
                mutationType { name }
                types {
                    name
                    fields { name type { name } }
                }
            }
        }
    """
    
    try:
        validator.validate_query(introspection_query)
        print("✗ Schema introspection was not blocked!")
        return False
    except Exception as e:
        print(f"✓ Schema introspection blocked: {e}")
    
    # Test 3: Unknown field should be blocked
    unknown_field_query = """
        query EvilQuery {
            getTest(issueId: "TEST-123") {
                issueId
                evilField
            }
        }
    """
    
    try:
        validator.validate_query(unknown_field_query)
        print("✗ Unknown field was not blocked!")
        return False
    except Exception as e:
        print(f"✓ Unknown field blocked: {e}")
    
    # Test 4: Script injection in variables should be blocked
    script_variables = {
        "issueId": "<script>alert('xss')</script>"
    }
    
    try:
        validator.validate_query(valid_query, script_variables)
        print("✗ Script injection in variables was not blocked!")
        return False
    except Exception as e:
        print(f"✓ Script injection in variables blocked: {e}")
    
    # Test 5: Excessive query depth should be blocked
    deep_query = """
        query DeepQuery {
            getTest(issueId: "TEST-123") {
                issueId
                jira {
                    key
                    project {
                        key
                        lead {
                            key
                            groups {
                                name
                                users {
                                    key
                                    groups {
                                        name
                                        users {
                                            key
                                        }
                                    }
                                }
                            }
                        }
                    }
                }
            }
        }
    """
    
    try:
        validator.validate_query(deep_query)
        print("✗ Deep query was not blocked!")
        return False
    except Exception as e:
        print(f"✓ Deep query blocked: {e}")
    
    # Test 6: Valid mutation should pass
    valid_mutation = """
        mutation CreateTest($projectId: String!, $summary: String!) {
            createTest(testIssueFields: {
                projectId: $projectId
                summary: $summary
            }) {
                test { issueId jira { key } }
                warnings
            }
        }
    """
    
    try:
        result = validator.validate_query(
            valid_mutation, 
            {"projectId": "10000", "summary": "Test Summary"}
        )
        print("✓ Valid mutation passed validation")
    except Exception as e:
        print(f"✗ Valid mutation failed: {e}")
        return False
    
    print("\n✓ All GraphQL security tests passed!")
    return True

if __name__ == "__main__":
    if test_graphql_validation():
        print("GraphQL injection protection is working correctly!")
        sys.exit(0)
    else:
        print("GraphQL injection protection has vulnerabilities!")
        sys.exit(1)