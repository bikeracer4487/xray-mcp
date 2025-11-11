"""Helper functions for integration tests."""

import json
from typing import Dict, Any, List


def parse_mcp_response(mcp_result) -> Dict[str, Any]:
    """Parse MCP response format to extract the actual data.

    Args:
        mcp_result: MCP response - can be dict (new format) or list of content blocks (old format)

    Returns:
        Dictionary with parsed response data

    Raises:
        ValueError: If response format is invalid
    """
    # Handle new direct dict format from FastMCP
    if isinstance(mcp_result, dict):
        # FastMCP now returns data directly - wrap in standard format
        return {
            'success': True,
            'data': mcp_result,
            'errors': []
        }

    # Handle old list format
    if not isinstance(mcp_result, list) or len(mcp_result) == 0:
        raise ValueError(f"Invalid MCP result format: {mcp_result}")

    response_text = mcp_result[0].text

    # Check for operation failures first
    if "Operation failed" in response_text:
        return {
            'success': False,
            'errors': [response_text],
            'data': None
        }

    # Check for simple success messages
    if response_text == "Operation completed successfully":
        return {
            'success': True,
            'data': {'message': 'Operation completed successfully'},
            'errors': []
        }

    try:
        # Parse the JSON response directly
        parsed_data = json.loads(response_text)

        # Check if it's the new format (direct dict with success/data/errors)
        if isinstance(parsed_data, dict) and 'success' in parsed_data:
            # Return the parsed data directly - it's already in the expected format
            return parsed_data

        # Check if it's a direct entity response (new FastMCP format)
        elif isinstance(parsed_data, dict) and any(key in parsed_data for key in ['issueId', 'issueKey', 'id', 'message']):
            # This is a successful entity response - wrap in standard format
            # Covers: entities (issueId/issueKey), test runs (id), operations (message)
            return {
                'success': True,
                'data': parsed_data,
                'errors': []
            }

        # Check if it's a list response (multiple entities or search results)
        elif isinstance(parsed_data, list):
            # This is a successful list response - wrap in standard format
            return {
                'success': True,
                'data': parsed_data,
                'errors': []
            }

        # Check if it's the old nested format (list with text fields)
        elif isinstance(parsed_data, list) and len(parsed_data) > 0:
            inner_text = parsed_data[0].get('text', '{}')
            data = json.loads(inner_text)

            # For successful operations, wrap in standard format
            return {
                'success': True,
                'data': data,
                'errors': []
            }
        else:
            return {
                'success': False,
                'errors': [f"Unexpected response format: {response_text}"],
                'data': None
            }

    except json.JSONDecodeError as e:
        return {
            'success': False,
            'errors': [f"Could not parse JSON response: {str(e)}"],
            'data': None
        }