# Xray MCP Server Installation Guide

## Quick Start

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Credentials**
   ```bash
   cp .env.example .env
   # Edit .env with your Xray API credentials
   ```

3. **Test Installation**
   ```bash
   python test_server.py
   ```

4. **Run the Server**
   ```bash
   # Option 1: Direct execution
   python main.py
   
   # Option 2: FastMCP CLI
   fastmcp run main.py:mcp
   ```

## Detailed Setup

### 1. Prerequisites

- Python 3.11 or higher
- Xray Cloud account with API access
- Valid Xray API credentials (Client ID and Client Secret)

### 2. Get Xray API Credentials

1. Log in to your Xray Cloud instance
2. Navigate to **Global Settings** > **API Keys**
3. Create a new API Key
4. Copy the **Client ID** and **Client Secret**

### 3. Environment Configuration

Create a `.env` file in the project root:

```env
XRAY_CLIENT_ID=your_actual_client_id_here
XRAY_CLIENT_SECRET=your_actual_client_secret_here
XRAY_BASE_URL=https://xray.cloud.getxray.app
```

### 4. Verification

Run the test suite to verify everything is working:

```bash
python test_server.py
```

You should see:
```
🚀 Starting Xray MCP Server tests...
🧪 Testing server creation...
✅ Server creation test passed
🧪 Testing authentication manager...
✅ Authentication manager test passed
🧪 Testing GraphQL client...
✅ GraphQL client test passed
🧪 Testing tool registration...
✅ Tool registration test passed - All tool classes initialized
🧪 Testing error handling...
✅ Error handling test passed
🧪 Testing configuration...
✅ Configuration test passed
🎉 All tests passed! The Xray MCP Server is working correctly.
```

### 5. Running the Server

#### Option A: Direct Python Execution
```bash
python main.py
```

#### Option B: FastMCP CLI
```bash
fastmcp run main.py:mcp
```

Both methods will start the MCP server using the stdio transport, which is the standard way to expose an MCP server to clients.

## Troubleshooting

### Common Issues

1. **Import Errors**
   - Ensure all dependencies are installed: `pip install -r requirements.txt`
   - Make sure you're running from the project directory

2. **Authentication Errors**
   - Verify your Client ID and Client Secret are correct
   - Check that your Xray license is valid
   - Ensure the base URL is correct for your instance

3. **Environment Variable Issues**
   - Make sure the `.env` file is in the project root
   - Verify the environment variable names are correct
   - Check that there are no extra spaces or quotes in the values

### Testing with Mock Credentials

If you want to test the server structure without real Xray credentials:

```python
from main import create_server

# Create server with mock credentials (won't authenticate)
server = create_server("mock_id", "mock_secret")
print("Server created successfully!")
```

## Next Steps

Once the server is running, you can:

1. Connect it to an MCP-compatible client
2. Use the available tools for test management
3. Extend the server with additional Xray functionality
4. Deploy it to a production environment

For detailed usage examples, see the main README.md file.

