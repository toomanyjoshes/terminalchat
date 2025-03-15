#!/bin/bash
# Simple installer for terminalchat - installs and makes available immediately

# Install Rich library if needed
python3 -m pip install --user rich

# Create bin directory if it doesn't exist
mkdir -p "$HOME/bin"

# Copy the script
cp "$(pwd)/terminalchat.py" "$HOME/bin/terminalchat"
chmod +x "$HOME/bin/terminalchat"

# Add to PATH immediately for this session
export PATH="$HOME/bin:$PATH"

# Add to PATH permanently if not already there
if ! grep -q 'export PATH="$HOME/bin:$PATH"' "$HOME/.bashrc" 2>/dev/null; then
    echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.bashrc"
fi

if [ -f "$HOME/.zshrc" ] && ! grep -q 'export PATH="$HOME/bin:$PATH"' "$HOME/.zshrc" 2>/dev/null; then
    echo 'export PATH="$HOME/bin:$PATH"' >> "$HOME/.zshrc"
fi

echo "TerminalChat installed."
echo "You can now use: terminalchat help"
