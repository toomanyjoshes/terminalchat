#!/bin/bash
# Easy installer for terminalchat - installs and runs immediately

set -e  # Exit on error

echo "📱 Installing TerminalChat..."

# Install Rich library if needed
python3 -m pip install --user rich

# Create installation directory
mkdir -p "$HOME/.local/bin"

# Copy the terminalchat script
cp "$(pwd)/terminalchat.py" "$HOME/.local/bin/terminalchat"
chmod +x "$HOME/.local/bin/terminalchat"

# Add to PATH immediately for this session
export PATH="$HOME/.local/bin:$PATH"

# Add to PATH permanently if not already there
if ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.bashrc"
fi

if [ -f "$HOME/.zshrc" ] && ! grep -q 'export PATH="$HOME/.local/bin:$PATH"' "$HOME/.zshrc" 2>/dev/null; then
    echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$HOME/.zshrc"
fi

echo "✅ TerminalChat installed successfully!"
echo "🚀 Starting TerminalChat..."
echo ""

# Run terminalchat immediately
terminalchat
