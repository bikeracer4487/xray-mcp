"""Helper functions for integration tests."""

import json
from typing import Dict, Any, List


def parse_mcp_response(mcp_result: List) -> Dict[str, Any]:
    """Parse MCP response format to extract the actual data.

    Args:
        mcp_result: List of MCP content blocks from tool.run()

    Returns:
        Dictionary with parsed response data

    Raises:
        ValueError: If response format is invalid
    """
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
        # Parse nested JSON structure
        outer_data = json.loads(response_text)

        # Extract inner data
        if isinstance(outer_data, list) and len(outer_data) > 0:
            inner_text = outer_data[0].get('text', '{}')
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