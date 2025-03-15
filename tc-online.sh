#!/bin/bash
# Script to run TerminalChat with the online server
# © Shortcut Studios

# Your deployed Render URL
RENDER_URL="https://terminalchat-server.onrender.com"

# Display banner
echo -e "\033[1;36m"
echo "╔════════════════════════════════════════╗"
echo "║           TerminalChat Online          ║"
echo "║          © Shortcut Studios            ║"
echo "╚════════════════════════════════════════╝"
echo -e "\033[0m"

# Export the server URL
export TERMINALCHAT_SERVER_URL="$RENDER_URL"
echo -e "\033[1;32mConnecting to: $RENDER_URL\033[0m"

# Create app directory
APP_DIR="$HOME/.terminalchat/app"
mkdir -p "$APP_DIR"

# Always download the latest version of terminalchat.py
echo "Downloading TerminalChat..."
curl -s -o "$APP_DIR/terminalchat.py" "https://raw.githubusercontent.com/toomanyjoshes/terminalchat/main/terminalchat.py"

# Check if download was successful
if [ ! -s "$APP_DIR/terminalchat.py" ]; then
    echo "Error: Failed to download terminalchat.py"
    exit 1
fi

# Download requirements.txt
curl -s -o "$APP_DIR/requirements.txt" "https://raw.githubusercontent.com/toomanyjoshes/terminalchat/main/requirements.txt"

# Install dependencies
echo "Installing dependencies..."
pip3 install -q -r "$APP_DIR/requirements.txt" || {
    echo "Warning: Failed to install dependencies. Continuing anyway..."
}

# Check if command was provided
if [ $# -eq 0 ]; then
    echo -e "\033[1;33mUsage: ./tc-online.sh <command> [arguments]\033[0m"
    echo -e "Example: ./tc-online.sh login"
    echo -e "For a full list of commands, use: ./tc-online.sh help"
    exit 1
fi

# Run TerminalChat with the server URL
python3 "$APP_DIR/terminalchat.py" "$@"
