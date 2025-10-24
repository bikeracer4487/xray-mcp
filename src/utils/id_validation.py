"""
ID Format Validation Utilities

This module provides utilities to validate and handle the critical ID format issue
discovered in QA reports: Xray GraphQL API requires numeric IDs (e.g., "1192649")
but users naturally expect JIRA keys (e.g., "FTEST-1590") to work.

Key Discovery from QA Reports:
- ✅ Numeric IDs work: "1192649"
- ❌ JIRA keys fail: "FTEST-1590"

This utility helps:
1. Detect ID format
2. Provide helpful error messages
3. Guide users to use correct format
"""

import re
from typing import Union, Tuple, Optional, List
from dataclasses import dataclass


@dataclass
class IDValidationResult:
    """Result of ID format validation."""
    is_valid: bool
    id_type: str  # "numeric", "jira_key", "unknown"
    error_message: Optional[str] = None
    helpful_message: Optional[str] = None


@dataclass
class ArrayValidationResult:
    """Result of array ID format validation."""
    is_valid: bool
    valid_ids: List[str]
    invalid_ids: List[str]
    invalid_details: List[IDValidationResult]
    error_message: Optional[str] = None
    helpful_message: Optional[str] = None


class IDFormatValidator:
    """Validator for Xray issue ID formats."""

    # Pattern for JIRA keys: PROJECT-123, FTEST-1590, etc.
    JIRA_KEY_PATTERN = re.compile(r'^[A-Z][A-Z0-9]*-\d+$')

    # Pattern for numeric IDs: 1192649, 123456, etc.
    NUMERIC_ID_PATTERN = re.compile(r'^\d+$')

    @classmethod
    def detect_id_format(cls, issue_id: str) -> str:
        """
        Detect the format of an issue ID.

        Args:
            issue_id: The issue ID to analyze

        Returns:
            "numeric", "jira_key", or "unknown"
        """
        if not issue_id or not isinstance(issue_id, str):
            return "unknown"

        issue_id = issue_id.strip()

        if cls.NUMERIC_ID_PATTERN.match(issue_id):
            return "numeric"
        elif cls.JIRA_KEY_PATTERN.match(issue_id):
            return "jira_key"
        else:
            return "unknown"

    @classmethod
    def is_numeric_id(cls, issue_id: str) -> bool:
        """Check if the ID is in numeric format (required by Xray GraphQL)."""
        return cls.detect_id_format(issue_id) == "numeric"

    @classmethod
    def is_jira_key(cls, issue_id: str) -> bool:
        """Check if the ID is in JIRA key format (not supported by Xray GraphQL)."""
        return cls.detect_id_format(issue_id) == "jira_key"

    @classmethod
    def validate_for_xray_graphql(cls, issue_id: str, entity_type: str = "entity") -> IDValidationResult:
        """
        Validate an issue ID for use with Xray GraphQL API.

        Args:
            issue_id: The issue ID to validate
            entity_type: Type of entity (test, test_execution, test_plan) for better error messages

        Returns:
            IDValidationResult with validation status and helpful messages
        """
        if not issue_id:
            return IDValidationResult(
                is_valid=False,
                id_type="unknown",
                error_message="Issue ID is required",
                helpful_message=(
                    f"SOLUTION: Provide a numeric issue ID for your {entity_type}. "
                    f"EXAMPLE: Use issue_id='1192649' (numeric format only). "
                    f"NOTE: JIRA keys like 'FTEST-1590' are not supported by Xray's GraphQL API"
                )
            )

        if not isinstance(issue_id, str):
            return IDValidationResult(
                is_valid=False,
                id_type="unknown",
                error_message=f"Issue ID must be a string, got {type(issue_id).__name__}",
                helpful_message=(
                    f"SOLUTION: Convert {entity_type} ID to string format. "
                    f"EXAMPLE: Use issue_id='1192649' (quoted string) instead of issue_id={issue_id}. "
                    f"COMMON MISTAKE: Ensure numeric IDs are quoted as strings in JSON/parameters"
                )
            )

        issue_id = issue_id.strip()
        id_format = cls.detect_id_format(issue_id)

        if id_format == "numeric":
            return IDValidationResult(
                is_valid=True,
                id_type="numeric"
            )
        elif id_format == "jira_key":
            entity_examples = {
                "test": "entity='test', project_key='{}'",
                "test_execution": "entity='test_execution', project_key='{}'",
                "test_plan": "entity='test_plan', project_key='{}'",
                "test_run": "entity='test_run'"
            }
            project_key = issue_id.split('-')[0] if '-' in issue_id else 'PROJECT'
            list_example = entity_examples.get(entity_type, "entity='test', project_key='{}'").format(project_key)

            return IDValidationResult(
                is_valid=False,
                id_type="jira_key",
                error_message=(
                    f"Invalid ID format. JIRA keys ('{issue_id}') are not supported by Xray's GraphQL API"
                ),
                helpful_message=(
                    f"SOLUTION: Use numeric issue IDs instead of JIRA keys. "
                    f"STEP 1: List {entity_type}s with: {list_example}. "
                    f"STEP 2: Find '{issue_id}' in results and use its 'issueId' field (e.g., '1192649'). "
                    f"EXAMPLE: Replace '{issue_id}' with '1192649' in your request"
                )
            )
        else:
            return IDValidationResult(
                is_valid=False,
                id_type="unknown",
                error_message=f"Invalid issue ID format: '{issue_id}'",
                helpful_message=(
                    f"SOLUTION: Use only numeric {entity_type} IDs with Xray GraphQL API. "
                    f"REQUIRED FORMAT: Numeric digits only (e.g., '1192649'). "
                    f"NOT SUPPORTED: JIRA keys ('FTEST-1590'), special characters, or mixed formats. "
                    f"EXAMPLE: Replace '{issue_id}' with a valid numeric ID like '1192649'"
                )
            )

    @classmethod
    def validate_id_array_for_xray_graphql(cls, issue_ids: List[str], entity_type: str = "entity") -> ArrayValidationResult:
        """
        Validate an array of issue IDs for use with Xray GraphQL API.

        Args:
            issue_ids: List of issue IDs to validate
            entity_type: Type of entity for better error messages

        Returns:
            ArrayValidationResult with detailed validation status
        """
        if not issue_ids:
            return ArrayValidationResult(
                is_valid=False,
                valid_ids=[],
                invalid_ids=[],
                invalid_details=[],
                error_message="Issue ID array is empty",
                helpful_message=(
                    f"SOLUTION: Provide at least one {entity_type} ID in the array. "
                    f"EXAMPLE: Use test_issue_ids=['1192649', '1192650'] for multiple {entity_type}s. "
                    f"SINGLE ITEM: Use test_issue_ids=['1192649'] for one {entity_type}. "
                    f"NOTE: All IDs must be numeric strings, not JIRA keys"
                )
            )

        if not isinstance(issue_ids, list):
            return ArrayValidationResult(
                is_valid=False,
                valid_ids=[],
                invalid_ids=[],
                invalid_details=[],
                error_message=f"Issue IDs must be provided as a list, got {type(issue_ids).__name__}",
                helpful_message=(
                    f"SOLUTION: Convert {entity_type} IDs to a list format. "
                    f"CORRECT FORMAT: test_issue_ids=['1192649', '1192650'] (array of strings). "
                    f"INCORRECT: test_issue_ids='1192649' (single string) or test_issue_ids=1192649 (number). "
                    f"EXAMPLE: Use test_issue_ids=['1192649'] even for a single {entity_type}"
                )
            )

        valid_ids = []
        invalid_ids = []
        invalid_details = []

        for issue_id in issue_ids:
            if not isinstance(issue_id, str):
                invalid_ids.append(str(issue_id))
                invalid_details.append(IDValidationResult(
                    is_valid=False,
                    id_type="unknown",
                    error_message=f"Issue ID must be a string, got {type(issue_id).__name__}: {issue_id}",
                    helpful_message="All issue IDs must be strings in numeric format (e.g., '1192649')"
                ))
                continue

            validation_result = cls.validate_for_xray_graphql(issue_id, entity_type)
            if validation_result.is_valid:
                valid_ids.append(issue_id)
            else:
                invalid_ids.append(issue_id)
                invalid_details.append(validation_result)

        # Create summary error message if there are invalid IDs
        if invalid_ids:
            error_parts = []
            helpful_parts = []

            # Count different types of errors
            jira_keys = [detail for detail in invalid_details if detail.id_type == "jira_key"]
            unknown_formats = [detail for detail in invalid_details if detail.id_type == "unknown"]

            if jira_keys:
                jira_id_list = [invalid_ids[i] for i, detail in enumerate(invalid_details) if detail.id_type == "jira_key"]
                error_parts.append(f"JIRA keys found: {jira_id_list}")
                project_keys = list(set([jid.split('-')[0] for jid in jira_id_list if '-' in jid]))
                helpful_parts.append(
                    f"STEP 1: List {entity_type}s to find numeric IDs for {jira_id_list}. "
                    f"STEP 2: Use entity='{entity_type}', project_key='{project_keys[0] if project_keys else 'PROJECT'}'. "
                    f"STEP 3: Replace JIRA keys with 'issueId' values from results"
                )

            if unknown_formats:
                unknown_id_list = [invalid_ids[i] for i, detail in enumerate(invalid_details) if detail.id_type == "unknown"]
                error_parts.append(f"Invalid formats: {unknown_id_list}")
                helpful_parts.append(
                    f"FIX: Replace invalid formats {unknown_id_list} with numeric IDs (e.g., '1192649'). "
                    f"ENSURE: All IDs are strings containing only digits"
                )

            error_message = f"Invalid IDs in array ({len(invalid_ids)}/{len(issue_ids)} invalid). " + ". ".join(error_parts)
            helpful_message = (
                f"SOLUTION: Xray GraphQL API requires numeric IDs only. " +
                ". ".join(helpful_parts) +
                f". WORKING IDs: {valid_ids if valid_ids else ['None - all IDs need fixing']}"
            )

            return ArrayValidationResult(
                is_valid=False,
                valid_ids=valid_ids,
                invalid_ids=invalid_ids,
                invalid_details=invalid_details,
                error_message=error_message,
                helpful_message=helpful_message
            )

        # All IDs are valid
        return ArrayValidationResult(
            is_valid=True,
            valid_ids=valid_ids,
            invalid_ids=[],
            invalid_details=[]
        )

    @classmethod
    def validate_id_array_for_xray_graphql_allow_empty(cls, issue_ids: List[str], entity_type: str = "entity") -> ArrayValidationResult:
        """
        Validate an array of issue IDs for use with Xray GraphQL API - allows empty arrays for creation operations.

        Args:
            issue_ids: List of issue IDs to validate
            entity_type: Type of entity for better error messages

        Returns:
            ArrayValidationResult with detailed validation status
        """
        if not isinstance(issue_ids, list):
            return ArrayValidationResult(
                is_valid=False,
                valid_ids=[],
                invalid_ids=[],
                invalid_details=[],
                error_message=f"Issue IDs must be provided as a list, got {type(issue_ids).__name__}",
                helpful_message=(
                    f"SOLUTION: Convert {entity_type} IDs to a list format. "
                    f"CORRECT FORMAT: test_issue_ids=['1192649', '1192650'] (array of strings). "
                    f"ALSO VALID: test_issue_ids=[] (empty array for creation operations). "
                    f"INCORRECT: test_issue_ids='1192649' (single string) or test_issue_ids=1192649 (number)"
                )
            )

        # Empty arrays are allowed for creation operations
        if len(issue_ids) == 0:
            return ArrayValidationResult(
                is_valid=True,
                valid_ids=[],
                invalid_ids=[],
                invalid_details=[]
            )

        valid_ids = []
        invalid_ids = []
        invalid_details = []

        for issue_id in issue_ids:
            if not isinstance(issue_id, str):
                invalid_ids.append(str(issue_id))
                invalid_details.append(IDValidationResult(
                    is_valid=False,
                    id_type="unknown",
                    error_message=f"Issue ID must be a string, got {type(issue_id).__name__}: {issue_id}",
                    helpful_message="All issue IDs must be strings in numeric format (e.g., '1192649')"
                ))
                continue

            validation_result = cls.validate_for_xray_graphql(issue_id, entity_type)
            if validation_result.is_valid:
                valid_ids.append(issue_id)
            else:
                invalid_ids.append(issue_id)
                invalid_details.append(validation_result)

        # Create summary error message if there are invalid IDs
        if invalid_ids:
            error_parts = []
            helpful_parts = []

            # Count different types of errors
            jira_keys = [detail for detail in invalid_details if detail.id_type == "jira_key"]
            unknown_formats = [detail for detail in invalid_details if detail.id_type == "unknown"]

            if jira_keys:
                jira_id_list = [invalid_ids[i] for i, detail in enumerate(invalid_details) if detail.id_type == "jira_key"]
                error_parts.append(f"JIRA keys found: {jira_id_list}")
                project_keys = list(set([jid.split('-')[0] for jid in jira_id_list if '-' in jid]))
                helpful_parts.append(
                    f"STEP 1: List {entity_type}s to find numeric IDs for {jira_id_list}. "
                    f"STEP 2: Use entity='{entity_type}', project_key='{project_keys[0] if project_keys else 'PROJECT'}'. "
                    f"STEP 3: Replace JIRA keys with 'issueId' values from results"
                )

            if unknown_formats:
                unknown_id_list = [invalid_ids[i] for i, detail in enumerate(invalid_details) if detail.id_type == "unknown"]
                error_parts.append(f"Invalid formats: {unknown_id_list}")
                helpful_parts.append(
                    f"FIX: Replace invalid formats {unknown_id_list} with numeric IDs (e.g., '1192649'). "
                    f"ENSURE: All IDs are strings containing only digits"
                )

            error_message = f"Invalid IDs in array ({len(invalid_ids)}/{len(issue_ids)} invalid). " + ". ".join(error_parts)
            helpful_message = (
                f"SOLUTION: Xray GraphQL API requires numeric IDs only. " +
                ". ".join(helpful_parts) +
                f". WORKING IDs: {valid_ids if valid_ids else ['None - all IDs need fixing']}"
            )

            return ArrayValidationResult(
                is_valid=False,
                valid_ids=valid_ids,
                invalid_ids=invalid_ids,
                invalid_details=invalid_details,
                error_message=error_message,
                helpful_message=helpful_message
            )

        # All IDs are valid
        return ArrayValidationResult(
            is_valid=True,
            valid_ids=valid_ids,
            invalid_ids=[],
            invalid_details=[]
        )

    @classmethod
    def create_helpful_error_message(cls, issue_id: str, entity_type: str = "entity") -> str:
        """
        Create a helpful error message for ID format issues.

        This provides users with clear guidance on how to fix the problem.
        """
        validation = cls.validate_for_xray_graphql(issue_id, entity_type)

        if validation.is_valid:
            return ""  # No error message needed

        base_error = validation.error_message
        helpful_guidance = validation.helpful_message

        # Combine error with helpful guidance
        return f"{base_error}. {helpful_guidance}"

    @classmethod
    def suggest_solution_for_jira_key(cls, jira_key: str, entity_type: str = "entity") -> str:
        """
        Suggest a solution when user provides a JIRA key instead of numeric ID.

        Args:
            jira_key: The JIRA key that was provided (e.g., "FTEST-1590")
            entity_type: Type of entity for better guidance

        Returns:
            A helpful message explaining how to find the numeric ID
        """
        return (
            f"To find the numeric ID for '{jira_key}', use a list operation first:\n\n"
            f"1. List {entity_type}s: list(entity='{entity_type}', project_key='{jira_key.split('-')[0]}')\n"
            f"2. Find '{jira_key}' in the results\n"
            f"3. Use the 'issueId' field (numeric) instead of 'issueKey' field\n"
            f"4. Example: Use '1192649' instead of '{jira_key}'\n\n"
            f"The Xray GraphQL API requires numeric IDs, not JIRA keys."
        )


def validate_issue_id(issue_id: str, entity_type: str = "entity") -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate an issue ID for Xray operations.

    Args:
        issue_id: The issue ID to validate
        entity_type: Type of entity for better error messages

    Returns:
        Tuple of (is_valid, error_message_if_invalid)
    """
    result = IDFormatValidator.validate_for_xray_graphql(issue_id, entity_type)

    if result.is_valid:
        return True, None
    else:
        error_msg = f"{result.error_message}. {result.helpful_message}"
        return False, error_msg


def is_jira_key_format(issue_id: str) -> bool:
    """
    Quick check if an ID is in JIRA key format.

    Args:
        issue_id: The ID to check

    Returns:
        True if it looks like a JIRA key (e.g., "FTEST-1590")
    """
    return IDFormatValidator.is_jira_key(issue_id)


def is_numeric_id_format(issue_id: str) -> bool:
    """
    Quick check if an ID is in numeric format.

    Args:
        issue_id: The ID to check

    Returns:
        True if it looks like a numeric ID (e.g., "1192649")
    """
    return IDFormatValidator.is_numeric_id(issue_id)


def get_helpful_id_format_error(issue_id: str, entity_type: str = "entity") -> str:
    """
    Get a helpful error message for ID format issues.

    Args:
        issue_id: The problematic issue ID
        entity_type: Type of entity for context

    Returns:
        A helpful error message explaining the issue and solution
    """
    return IDFormatValidator.create_helpful_error_message(issue_id, entity_type)


def validate_issue_id_array(issue_ids: List[str], entity_type: str = "entity") -> Tuple[bool, Optional[str]]:
    """
    Convenience function to validate an array of issue IDs for Xray operations.

    Args:
        issue_ids: List of issue IDs to validate
        entity_type: Type of entity for better error messages

    Returns:
        Tuple of (is_valid, error_message_if_invalid)
    """
    result = IDFormatValidator.validate_id_array_for_xray_graphql(issue_ids, entity_type)

    if result.is_valid:
        return True, None
    else:
        error_msg = f"{result.error_message}. {result.helpful_message}"
        return False, error_msg


def get_helpful_array_format_error(issue_ids: List[str], entity_type: str = "entity") -> str:
    """
    Get a helpful error message for array ID format issues.

    Args:
        issue_ids: The problematic array of issue IDs
        entity_type: Type of entity for context

    Returns:
        A helpful error message explaining the issues and solutions
    """
    result = IDFormatValidator.validate_id_array_for_xray_graphql(issue_ids, entity_type)

    if result.is_valid:
        return ""  # No error message needed

    return f"{result.error_message}. {result.helpful_message}"


# Examples of how to use this utility:
if __name__ == "__main__":
    # Example usage for single IDs
    test_ids = ["1192649", "FTEST-1590", "invalid-id", "", 123]

    print("🔍 Testing Single ID Validation:")
    for test_id in test_ids:
        print(f"\nTesting ID: {test_id}")
        try:
            result = IDFormatValidator.validate_for_xray_graphql(str(test_id), "test")
            print(f"  Valid: {result.is_valid}")
            print(f"  Type: {result.id_type}")
            if result.error_message:
                print(f"  Error: {result.error_message}")
            if result.helpful_message:
                print(f"  Help: {result.helpful_message}")
        except Exception as e:
            print(f"  Exception: {e}")

    # Example usage for arrays
    test_arrays = [
        ["1192649", "1192650", "1192651"],  # All valid
        ["1192649", "FTEST-1590", "1192651"],  # Mixed valid/JIRA key
        ["FTEST-1590", "FTEST-1591"],  # All JIRA keys
        ["1192649", "invalid-id", 123],  # Mixed valid/invalid
        [],  # Empty array
        "not-an-array"  # Wrong type
    ]

    print("\n\n🔍 Testing Array ID Validation:")
    for i, test_array in enumerate(test_arrays):
        print(f"\nTesting Array {i+1}: {test_array}")
        try:
            result = IDFormatValidator.validate_id_array_for_xray_graphql(test_array, "test")
            print(f"  Valid: {result.is_valid}")
            print(f"  Valid IDs: {result.valid_ids}")
            print(f"  Invalid IDs: {result.invalid_ids}")
            if result.error_message:
                print(f"  Error: {result.error_message}")
            if result.helpful_message:
                print(f"  Help: {result.helpful_message}")
        except Exception as e:
            print(f"  Exception: {e}")