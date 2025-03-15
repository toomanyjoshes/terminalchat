#!/bin/bash
# Package installer for terminalchat
# This script creates a simple package that can be installed with a single command

set -e  # Exit on error

echo "📱 Creating TerminalChat package..."

# Check for Python 3
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Create a simple wrapper script
cat > terminalchat << 'EOF'
#!/bin/bash
python3 $(dirname "$0")/terminalchat.py "$@"
EOF

chmod +x terminalchat

# Create installation directories
sudo mkdir -p /usr/local/bin
sudo mkdir -p /usr/local/share/terminalchat

# Copy files
sudo cp terminalchat.py /usr/local/share/terminalchat/
sudo cp terminalchat /usr/local/bin/

echo "✅ TerminalChat installed successfully!"
echo ""
echo "🚀 Quick Start Guide:"
echo "  terminalchat signup     - Create a new account"
echo "  terminalchat login      - Log in to your account"
echo "  terminalchat message USERNAME - Message a user"
echo "  terminalchat list       - List your chats"
echo ""
echo "📖 For more information, run: terminalchat --help"
