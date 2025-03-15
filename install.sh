#!/bin/bash

# TerminalChat installer script
echo "Installing TerminalChat..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
cd "$TEMP_DIR"

# Clone the repository (replace with actual repo URL when available)
if [ "$1" == "--local" ]; then
    # Use local installation (for development)
    cd "$2"
else
    # Download the latest version
    echo "Downloading TerminalChat..."
    curl -L -o terminalchat.zip https://github.com/your-username/terminalchat/archive/main.zip
    unzip terminalchat.zip
    cd terminalchat-main
fi

# Install the package
echo "Installing dependencies and application..."
pip3 install -e . --user

# Clean up
if [ "$1" != "--local" ]; then
    cd ..
    rm -rf "$TEMP_DIR"
fi

echo "TerminalChat has been installed successfully!"
echo "You can now use the 'terminalchat' command from your terminal."
echo ""
echo "Quick start:"
echo "  terminalchat signup - Create a new account"
echo "  terminalchat login - Log in to your account"
echo "  terminalchat message USERNAME - Message a user"
echo "  terminalchat list - List your chats"
echo ""
echo "For more information, run: terminalchat --help"
