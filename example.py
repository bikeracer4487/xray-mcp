"""Example usage of Xray MCP Server."""

import asyncio
import os
from dotenv import load_dotenv

from main import create_server


async def main():
    """Example of how to use the Xray MCP server."""

    # Load environment variables
    load_dotenv()

    # Get credentials from environment or set them directly
    client_id = os.getenv("XRAY_CLIENT_ID", "your_client_id_here")
    client_secret = os.getenv("XRAY_CLIENT_SECRET", "your_client_secret_here")

    if client_id == "your_client_id_here" or client_secret == "your_client_secret_here":
        print("Please set XRAY_CLIENT_ID and XRAY_CLIENT_SECRET environment variables")
        print("or modify this script to include your credentials directly.")
        return

    # Create the server
    server = create_server(client_id, client_secret)

    # Initialize (authenticate)
    try:
        await server.initialize()
        print("✅ Successfully authenticated with Xray API")
    except Exception as e:
        print(f"❌ Failed to authenticate: {e}")
        return

    # Test the connection
    try:
        result = await server.utility_tools.validate_connection()
        print(f"Connection validation: {result}")
    except Exception as e:
        print(f"❌ Connection validation failed: {e}")
        return

    # Example: Get tests from a project
    try:
        # Replace 'YOUR_PROJECT' with your actual project key
        tests = await server.test_tools.get_tests(
            jql="project = 'YOUR_PROJECT'", limit=5
        )
        print(f"Found {tests.get('total', 0)} tests in the project")

        if tests.get("results"):
            print("First few tests:")
            for test in tests["results"][:3]:
                print(f"  - {test['jira']['key']}: {test['jira']['summary']}")

    except Exception as e:
        print(f"❌ Failed to get tests: {e}")

    print("\n🎉 Example completed! The server is ready to be used as an MCP server.")
    print("To run as an MCP server, use: python main.py")


if __name__ == "__main__":
    asyncio.run(main())
