#!/bin/bash
set -euo pipefail

# ============================================================================
# Xray MCP Server Setup Script
# 
# A platform-agnostic setup script that works on macOS, Linux, and WSL.
# Handles environment setup, dependency installation, and configuration.
# ============================================================================

# Initialize pyenv if available (do this early)
if [[ -d "$HOME/.pyenv" ]]; then
    export PYENV_ROOT="$HOME/.pyenv"
    export PATH="$PYENV_ROOT/bin:$PATH"
    if command -v pyenv &> /dev/null; then
        eval "$(pyenv init --path)" 2>/dev/null || true
        eval "$(pyenv init -)" 2>/dev/null || true
    fi
fi

# ----------------------------------------------------------------------------
# Constants and Configuration
# ----------------------------------------------------------------------------

# Colors for output (ANSI codes work on all platforms)
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly RED='\033[0;31m'
readonly NC='\033[0m' # No Color

# Configuration
readonly VENV_PATH=".xray-mcp_venv"
readonly DESKTOP_CONFIG_FLAG=".desktop_configured"

# ----------------------------------------------------------------------------
# Utility Functions
# ----------------------------------------------------------------------------

# Print colored output
print_success() {
    echo -e "${GREEN}✓${NC} $1" >&2
}

print_error() {
    echo -e "${RED}✗${NC} $1" >&2
}

print_warning() {
    echo -e "${YELLOW}!${NC} $1" >&2
}

print_info() {
    echo -e "${YELLOW}$1${NC}" >&2
}

# Get the script's directory (works on all platforms)
get_script_dir() {
    cd "$(dirname "$0")" && pwd
}

# Clear Python cache files to prevent import issues
clear_python_cache() {
    print_info "Clearing Python cache files..."
    find . -name "*.pyc" -delete 2>/dev/null || true
    find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true
    print_success "Python cache cleared"
}

# ----------------------------------------------------------------------------
# Platform Detection Functions
# ----------------------------------------------------------------------------

# Get cross-platform Python executable path from venv
get_venv_python_path() {
    local venv_path="$1"
    
    # Check for both Unix and Windows Python executable paths
    if [[ -f "$venv_path/bin/python" ]]; then
        echo "$venv_path/bin/python"
    elif [[ -f "$venv_path/Scripts/python.exe" ]]; then
        echo "$venv_path/Scripts/python.exe"
    else
        return 1  # No Python executable found
    fi
}

# Detect the operating system
detect_os() {
    case "$OSTYPE" in
        darwin*)  echo "macos" ;;
        linux*)   
            if grep -qi microsoft /proc/version 2>/dev/null; then
                echo "wsl"
            else
                echo "linux"
            fi
            ;;
        msys*|cygwin*|win32) echo "windows" ;;
        *)        echo "unknown" ;;
    esac
}

# Get Claude config path based on platform
get_claude_config_path() {
    local os_type=$(detect_os)
    
    case "$os_type" in
        macos)
            echo "$HOME/Library/Application Support/Claude/claude_desktop_config.json"
            ;;
        linux)
            echo "$HOME/.config/Claude/claude_desktop_config.json"
            ;;
        wsl)
            local win_appdata
            if command -v wslvar &> /dev/null; then
                win_appdata=$(wslvar APPDATA 2>/dev/null)
            fi
            
            if [[ -n "$win_appdata" ]]; then
                echo "$(wslpath "$win_appdata")/Claude/claude_desktop_config.json"
            else
                print_warning "Could not determine Windows user path automatically. Please ensure APPDATA is set correctly or provide the full path manually."
                echo "/mnt/c/Users/$USER/AppData/Roaming/Claude/claude_desktop_config.json"
            fi
            ;;
        windows)
            echo "$APPDATA/Claude/claude_desktop_config.json"
            ;;
        *)
            echo ""
            ;;
    esac
}

# ----------------------------------------------------------------------------
# Python Environment Functions
# ----------------------------------------------------------------------------

# Find suitable Python command
find_python() {
    # Pyenv should already be initialized at script start, but check if .python-version exists
    if [[ -f ".python-version" ]] && command -v pyenv &> /dev/null; then
        # Ensure pyenv respects the local .python-version
        pyenv local &>/dev/null || true
    fi
    
    # Prefer Python 3.12 for best compatibility
    local python_cmds=("python3.12" "python3.13" "python3.11" "python3.10" "python3" "python" "py")
    
    for cmd in "${python_cmds[@]}"; do
        if command -v "$cmd" &> /dev/null; then
            local version=$($cmd --version 2>&1)
            if [[ $version =~ Python\ 3\.([0-9]+)\.([0-9]+) ]]; then
                local major_version=${BASH_REMATCH[1]}
                local minor_version=${BASH_REMATCH[2]}
                
                # Check minimum version (3.10) for better library compatibility
                if [[ $major_version -ge 10 ]]; then
                    # Verify the command actually exists (important for pyenv)
                    if command -v "$cmd" &> /dev/null; then
                        echo "$cmd"
                        print_success "Found Python: $version"
                        
                        # Recommend Python 3.12
                        if [[ $major_version -ne 12 ]]; then
                            print_info "Note: Python 3.12 is recommended for best compatibility."
                        fi
                        
                        return 0
                    fi
                fi
            fi
        fi
    done
    
    print_error "Python 3.10+ not found. FastMCP requires Python 3.10+."
    echo "" >&2
    
    local os_type=$(detect_os)
    if [[ "$os_type" == "macos" ]]; then
        echo "To install Python:" >&2
        echo "  brew install python@3.12" >&2
    elif [[ "$os_type" == "linux" || "$os_type" == "wsl" ]]; then
        echo "To install Python:" >&2
        echo "  Ubuntu/Debian: sudo apt update && sudo apt install -y python3.12 python3.12-venv python3.12-pip" >&2
        echo "  RHEL/CentOS:   sudo dnf install -y python3.12 python3.12-venv python3.12-pip" >&2
        echo "  Arch:          sudo pacman -S python python-pip" >&2
    fi
    echo "" >&2
    
    return 1
}

# Setup virtual environment
setup_venv() {
    local python_cmd="$1"
    local venv_python=""
    local venv_pip=""
    
    # Create venv if it doesn't exist
    if [[ ! -d "$VENV_PATH" ]]; then
        print_info "Creating isolated environment..."
        
        # Try creating virtual environment
        if $python_cmd -m venv "$VENV_PATH" >/dev/null 2>&1; then
            print_success "Created isolated environment"
        else
            print_error "Failed to create virtual environment"
            echo "" >&2
            echo "Your system may be missing Python development packages." >&2
            echo "Please install python3-venv or python3-dev packages for your system." >&2
            exit 1
        fi
    fi
    
    # Get venv Python path based on platform
    venv_python=$(get_venv_python_path "$VENV_PATH")
    if [[ $? -ne 0 ]]; then
        print_error "Virtual environment Python not found"
        exit 1
    fi
    
    # Verify pip is working
    if ! $venv_python -m pip --version &>/dev/null 2>&1; then
        print_error "pip is not working correctly in the virtual environment"
        echo "" >&2
        echo "Try deleting the virtual environment and running again:" >&2
        echo "  rm -rf $VENV_PATH" >&2
        echo "  ./run-server.sh" >&2
        exit 1
    fi
    
    print_success "Virtual environment ready with pip"
    
    # Convert to absolute path for MCP registration
    local abs_venv_python=$(cd "$(dirname "$venv_python")" && pwd)/$(basename "$venv_python")
    echo "$abs_venv_python"
    return 0
}

# Check if package is installed
check_package() {
    local python_cmd="$1"
    local package="$2"
    $python_cmd -c "import $package" 2>/dev/null
}

# Install dependencies
install_dependencies() {
    local python_cmd="$1"
    local deps_needed=false
    
    # Check required packages
    local packages=("fastmcp" "aiohttp" "pydantic" "dotenv")
    for package in "${packages[@]}"; do
        local import_name=${package%%.*}  # Get first part before dot
        if ! check_package "$python_cmd" "$import_name"; then
            deps_needed=true
            break
        fi
    done
    
    if [[ "$deps_needed" == false ]]; then
        print_success "Dependencies already installed"
        return 0
    fi
    
    echo ""
    print_info "Setting up Xray MCP Server..."
    echo "Installing required components:"
    echo "  • FastMCP protocol library"
    echo "  • HTTP client (aiohttp)"
    echo "  • Data validation (pydantic)"
    echo "  • Environment configuration"
    echo ""
    
    # Install packages
    local install_cmd="$python_cmd -m pip install -q -r requirements.txt"
    
    echo -n "Downloading packages..."
    local install_output
    
    # Capture both stdout and stderr
    install_output=$($install_cmd 2>&1)
    local exit_code=$?
    
    if [[ $exit_code -ne 0 ]]; then
        echo -e "\r${RED}✗ Setup failed${NC}                      "
        echo ""
        echo "Installation error:"
        echo "$install_output" | head -20
        echo ""
        echo "Try running manually:"
        echo "  $python_cmd -m pip install -r requirements.txt"
        return 1
    else
        echo -e "\r${GREEN}✓ Setup complete!${NC}                    "
        return 0
    fi
}

# ----------------------------------------------------------------------------
# Environment Configuration Functions
# ----------------------------------------------------------------------------

# Setup .env file
setup_env_file() {
    if [[ -f .env ]]; then
        print_success ".env file already exists"
        return 0
    fi
    
    if [[ ! -f .env.example ]]; then
        print_error ".env.example not found!"
        return 1
    fi
    
    cp .env.example .env
    print_success "Created .env from .env.example"
    
    # Update API keys from environment if present
    local api_keys=(
        "XRAY_CLIENT_ID:your_xray_client_id_here"
        "XRAY_CLIENT_SECRET:your_xray_client_secret_here"
        "XRAY_BASE_URL:https://xray.cloud.getxray.app"
    )
    
    # Detect sed version for cross-platform compatibility
    local sed_cmd
    if sed --version >/dev/null 2>&1; then
        sed_cmd="sed -i"  # GNU sed (Linux)
    else
        sed_cmd="sed -i ''"  # BSD sed (macOS)
    fi
    
    for key_pair in "${api_keys[@]}"; do
        local key_name="${key_pair%%:*}"
        local placeholder="${key_pair##*:}"
        local key_value="${!key_name:-}"
        
        if [[ -n "$key_value" ]] && [[ "$key_value" != "$placeholder" ]]; then
            $sed_cmd "s|$placeholder|$key_value|" .env
            print_success "Updated .env with $key_name from environment"
        fi
    done
    
    return 0
}

# Validate API keys
validate_api_keys() {
    local has_key=false
    
    # Source the .env file to check values
    if [[ -f .env ]]; then
        set -a
        source .env 2>/dev/null || true
        set +a
    fi
    
    if [[ -n "${XRAY_CLIENT_ID:-}" ]] && [[ "${XRAY_CLIENT_ID}" != "your_xray_client_id_here" ]]; then
        print_success "XRAY_CLIENT_ID configured"
        has_key=true
    fi
    
    if [[ -n "${XRAY_CLIENT_SECRET:-}" ]] && [[ "${XRAY_CLIENT_SECRET}" != "your_xray_client_secret_here" ]]; then
        print_success "XRAY_CLIENT_SECRET configured"
        has_key=true
    fi
    
    if [[ "$has_key" == false ]]; then
        print_error "Xray API credentials not found in .env!"
        echo "" >&2
        echo "Please edit .env and add your Xray API credentials:" >&2
        echo "  XRAY_CLIENT_ID=your-actual-client-id" >&2
        echo "  XRAY_CLIENT_SECRET=your-actual-client-secret" >&2
        echo "" >&2
        echo "You can obtain these from your Xray instance:" >&2
        echo "  https://docs.getxray.app/display/XRAYCLOUD/Global+Settings%3A+API+Keys" >&2
        echo "" >&2
        print_info "After adding your API keys, run ./run-server.sh again" >&2
        echo "" >&2
        return 1
    fi
    
    return 0
}

# ----------------------------------------------------------------------------
# Claude Integration Functions
# ----------------------------------------------------------------------------

# Check and update Claude Desktop configuration
check_claude_desktop_integration() {
    local python_cmd="$1"
    local server_path="$2"
    
    # Skip if already configured (check flag)
    if [[ -f "$DESKTOP_CONFIG_FLAG" ]]; then
        return 0
    fi
    
    local config_path=$(get_claude_config_path)
    if [[ -z "$config_path" ]]; then
        print_warning "Unable to determine Claude Desktop config path for this platform"
        return 0
    fi
    
    echo ""
    read -p "Configure Xray MCP for Claude Desktop? (Y/n): " -n 1 -r
    echo ""
    if [[ $REPLY =~ ^[Nn]$ ]]; then
        print_info "Skipping Claude Desktop integration"
        touch "$DESKTOP_CONFIG_FLAG"  # Don't ask again
        return 0
    fi
    
    # Create config directory if it doesn't exist
    local config_dir=$(dirname "$config_path")
    mkdir -p "$config_dir" 2>/dev/null || true
    
    # Handle existing config
    if [[ -f "$config_path" ]]; then
        print_info "Updating existing Claude Desktop config..."
        
        # Add new config
        local temp_file=$(mktemp)
        python3 -c "
import json
import sys

try:
    with open('$config_path', 'r') as f:
        config = json.load(f)
except:
    config = {}

# Ensure mcpServers exists
if 'mcpServers' not in config:
    config['mcpServers'] = {}

# Add xray server
config['mcpServers']['xray'] = {
    'command': '$python_cmd',
    'args': ['$server_path']
}

with open('$temp_file', 'w') as f:
    json.dump(config, f, indent=2)
" && mv "$temp_file" "$config_path"
        
    else
        print_info "Creating new Claude Desktop config..."
        cat > "$config_path" << EOF
{
  "mcpServers": {
    "xray": {
      "command": "$python_cmd",
      "args": ["$server_path"]
    }
  }
}
EOF
    fi
    
    if [[ $? -eq 0 ]]; then
        print_success "Successfully configured Claude Desktop"
        echo "  Config: $config_path"
        echo "  Restart Claude Desktop to use the new MCP server"
        touch "$DESKTOP_CONFIG_FLAG"
    else
        print_error "Failed to update Claude Desktop config"
        echo "Manual config location: $config_path"
        echo "Add this configuration:"
        cat << EOF
{
  "mcpServers": {
    "xray": {
      "command": "$python_cmd",
      "args": ["$server_path"]
    }
  }
}
EOF
    fi
}

# Display configuration instructions
display_config_instructions() {
    local python_cmd="$1"
    local server_path="$2"
    
    echo ""
    local config_header="XRAY MCP SERVER CONFIGURATION"
    echo "===== $config_header ====="
    printf '%*s\n' "$((${#config_header} + 12))" | tr ' ' '='
    echo ""
    echo "To use Xray MCP Server with your Claude clients:"
    echo ""
    
    print_info "1. For Claude Desktop:"
    echo "   Add this configuration to your Claude Desktop config file:"
    echo ""
    cat << EOF
   {
     "mcpServers": {
       "xray": {
         "command": "$python_cmd",
         "args": ["$server_path"]
       }
     }
   }
EOF
    
    # Show platform-specific config location
    local config_path=$(get_claude_config_path)
    if [[ -n "$config_path" ]]; then
        echo ""
        print_info "   Config file location:"
        echo -e "   ${YELLOW}$config_path${NC}"
    fi
    
    echo ""
    print_info "2. Restart Claude Desktop after updating the config file"
    echo ""
    
    print_info "3. For FastMCP CLI:"
    echo -e "   ${GREEN}fastmcp run $server_path:mcp${NC}"
    echo ""
}

# Display setup instructions
display_setup_instructions() {
    local python_cmd="$1"
    local server_path="$2"
    
    echo ""
    local setup_header="SETUP COMPLETE"
    echo "===== $setup_header ====="
    printf '%*s\n' "$((${#setup_header} + 12))" | tr ' ' '='
    echo ""
    print_success "Xray MCP Server is ready to use!"
    echo ""
    print_info "Quick Test:"
    echo "  $python_cmd $server_path"
    echo ""
    print_info "FastMCP CLI:"
    echo "  fastmcp run $server_path:mcp"
    echo ""
}

# ----------------------------------------------------------------------------
# Main Function
# ----------------------------------------------------------------------------

# Show help message
show_help() {
    local header="🔧 Xray MCP Server Setup"
    echo "$header"
    printf '%*s\n' "${#header}" | tr ' ' '='
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help      Show this help message"
    echo "  -c, --config    Show configuration instructions for Claude clients"
    echo "  --clear-cache   Clear Python cache and exit (helpful for import issues)"
    echo ""
    echo "Examples:"
    echo "  $0              Setup the MCP server"
    echo "  $0 -c           Show configuration instructions"
    echo "  $0 --clear-cache Clear Python cache (fixes import issues)"
    echo ""
    echo "For more information, visit:"
    echo "  https://github.com/your-username/xray-mcp"
}

main() {
    # Parse command line arguments
    local arg="${1:-}"
    
    case "$arg" in
        -h|--help)
            show_help
            exit 0
            ;;
        -c|--config)
            # Setup minimal environment to get paths for config display
            echo "Setting up environment for configuration display..."
            echo ""
            local python_cmd
            python_cmd=$(find_python) || exit 1
            python_cmd=$(setup_venv "$python_cmd") || exit 1
            local script_dir=$(get_script_dir)
            local server_path="$script_dir/main.py"
            display_config_instructions "$python_cmd" "$server_path"
            exit 0
            ;;
        --clear-cache)
            # Clear cache and exit
            clear_python_cache
            print_success "Cache cleared successfully"
            echo ""
            echo "You can now run './run-server.sh' normally"
            exit 0
            ;;
        "")
            # Normal setup
            ;;
        *)
            print_error "Unknown option: $arg"
            echo "" >&2
            show_help
            exit 1
            ;;
    esac
    
    # Display header
    local main_header="🔧 Xray MCP Server Setup"
    echo "$main_header"
    printf '%*s\n' "${#main_header}" | tr ' ' '='
    echo ""
    
    # Check if venv exists
    if [[ ! -d "$VENV_PATH" ]]; then
        echo "Setting up Python environment for first time..."
    fi
    
    # Step 1: Clear Python cache to prevent import issues
    clear_python_cache
    
    # Step 2: Setup environment file
    setup_env_file || exit 1
    
    # Step 3: Validate API keys
    validate_api_keys || exit 1
    
    # Step 4: Setup Python environment
    local python_cmd
    python_cmd=$(find_python) || exit 1
    python_cmd=$(setup_venv "$python_cmd") || exit 1
    
    # Step 5: Install dependencies
    install_dependencies "$python_cmd" || exit 1
    
    # Step 6: Get absolute server path
    local script_dir=$(get_script_dir)
    local server_path="$script_dir/main.py"
    
    # Step 7: Display setup instructions
    display_setup_instructions "$python_cmd" "$server_path"
    
    # Step 8: Check Claude Desktop integration
    check_claude_desktop_integration "$python_cmd" "$server_path"
    
    echo ""
    echo "To show config: ./run-server.sh -c"
    echo ""
    echo "Happy testing! 🎉"
}

# ----------------------------------------------------------------------------
# Script Entry Point
# ----------------------------------------------------------------------------

# Run main function with all arguments
main "$@"