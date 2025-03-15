#!/bin/bash
# Direct installer for terminalchat
# This script installs terminalchat directly without using pip's editable mode

set -e  # Exit on error

echo "📱 Installing TerminalChat..."

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Install Rich library
echo "📦 Installing dependencies..."
python3 -m pip install --user rich

# Create installation directory
INSTALL_DIR="$HOME/.terminalchat"
mkdir -p "$INSTALL_DIR"
mkdir -p "$HOME/.local/bin"

# Copy the terminalchat script
echo "📋 Copying TerminalChat script..."
cp "$(pwd)/terminalchat.py" "$HOME/.local/bin/terminalchat"
chmod +x "$HOME/.local/bin/terminalchat"

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
