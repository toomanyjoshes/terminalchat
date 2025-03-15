#!/bin/bash
# Simple installer for terminalchat
# This script can be run with: curl -s https://example.com/install_simple.sh | bash

set -e  # Exit on error

echo "📱 Installing TerminalChat..."

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Create installation directory
INSTALL_DIR="$HOME/.terminalchat"
mkdir -p "$INSTALL_DIR/bin"

# Download the terminalchat script
echo "⬇️ Downloading TerminalChat..."
curl -s -o "$INSTALL_DIR/bin/terminalchat" https://raw.githubusercontent.com/your-username/terminalchat/main/terminalchat.py
chmod +x "$INSTALL_DIR/bin/terminalchat"

# Install dependencies
echo "📦 Installing dependencies..."
python3 -m pip install --user rich

# Create symlink to make it available system-wide
mkdir -p "$HOME/.local/bin"
ln -sf "$INSTALL_DIR/bin/terminalchat" "$HOME/.local/bin/terminalchat"

# Add to PATH if not already there
if [[ ":$PATH:" != *":$HOME/.local/bin:"* ]]; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
    if [ -f "$HOME/.zshrc" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
    fi
    export PATH="$HOME/.local/bin:$PATH"
fi

echo "✅ TerminalChat installed successfully!"
echo ""
echo "🚀 Quick Start Guide:"
echo "  terminalchat signup     - Create a new account"
echo "  terminalchat login      - Log in to your account"
echo "  terminalchat message USERNAME - Message a user"
echo "  terminalchat list       - List your chats"
echo ""
echo "📖 For more information, run: terminalchat --help"
echo ""
echo "If terminalchat command is not found, please restart your terminal or run:"
echo "export PATH=\"\$HOME/.local/bin:\$PATH\""
