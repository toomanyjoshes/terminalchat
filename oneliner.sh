#!/bin/bash
# One-line installer for terminalchat
# Usage: curl -s https://raw.githubusercontent.com/your-username/terminalchat/main/oneliner.sh | bash

# Create temporary directory
TMP_DIR=$(mktemp -d)
cd "$TMP_DIR"

# Download terminalchat.py
curl -s -o terminalchat.py https://raw.githubusercontent.com/your-username/terminalchat/main/terminalchat.py

# Make it executable
chmod +x terminalchat.py

# Create installation directories
mkdir -p "$HOME/.local/bin"

# Copy to local bin
cp terminalchat.py "$HOME/.local/bin/terminalchat"

# Add to PATH if needed
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    if [ -f "$HOME/.zshrc" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    fi
    export PATH="$HOME/.local/bin:$PATH"
fi

# Clean up
cd - > /dev/null
rm -rf "$TMP_DIR"

echo "✅ TerminalChat installed successfully!"
echo "You can now use the 'terminalchat' command from your terminal."
echo ""
echo "🚀 Quick Start Guide:"
echo "  terminalchat signup     - Create a new account"
echo "  terminalchat login      - Log in to your account"
echo "  terminalchat message USERNAME - Message a user"
echo "  terminalchat list       - List your chats"
echo ""
echo "If terminalchat command is not found, please restart your terminal or run:"
echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
