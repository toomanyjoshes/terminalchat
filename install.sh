#!/bin/bash

# TerminalChat installer script
echo "Installing TerminalChat..."

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Create installation directory
INSTALL_DIR="$HOME/.terminalchat"
mkdir -p "$INSTALL_DIR"

# Download the latest version
echo "Downloading TerminalChat..."
git clone https://github.com/toomanyjoshes/terminalchat.git "$INSTALL_DIR/app" &>/dev/null || {
    echo "Updating existing installation..."
    cd "$INSTALL_DIR/app" && git pull &>/dev/null
}

# Install dependencies
echo "Installing dependencies..."
cd "$INSTALL_DIR/app" && pip3 install -r requirements.txt &>/dev/null

# Create symlink to make the command available system-wide
SYMLINK_DIR="$HOME/.local/bin"
mkdir -p "$SYMLINK_DIR"

# Create the tc command script
cat > "$INSTALL_DIR/tc" << 'EOF'
#!/bin/bash
python3 "$HOME/.terminalchat/app/terminalchat.py" "$@"
EOF

chmod +x "$INSTALL_DIR/tc"

# Create symlink
ln -sf "$INSTALL_DIR/tc" "$SYMLINK_DIR/tc"

# Check if the directory is in PATH
if [[ ":$PATH:" != *":$SYMLINK_DIR:"* ]]; then
    echo "Adding $SYMLINK_DIR to your PATH..."
    
    # Determine shell configuration file
    SHELL_CONFIG=""
    if [[ "$SHELL" == *"zsh"* ]]; then
        SHELL_CONFIG="$HOME/.zshrc"
    elif [[ "$SHELL" == *"bash"* ]]; then
        SHELL_CONFIG="$HOME/.bashrc"
        if [[ "$OSTYPE" == "darwin"* ]]; then
            SHELL_CONFIG="$HOME/.bash_profile"
        fi
    fi
    
    if [ -n "$SHELL_CONFIG" ]; then
        echo 'export PATH="$HOME/.local/bin:$PATH"' >> "$SHELL_CONFIG"
        echo "Added $SYMLINK_DIR to your PATH in $SHELL_CONFIG"
        echo "Please restart your terminal or run 'source $SHELL_CONFIG' to update your PATH."
    else
        echo "Please add $SYMLINK_DIR to your PATH manually."
    fi
else
    echo "TerminalChat installed successfully!"
    echo "You can now use the 'tc' command from anywhere."
fi

# Create online version script
cat > "$INSTALL_DIR/tc-online" << 'EOF'
#!/bin/bash
TERMINALCHAT_SERVER_URL="https://terminalchat-server.onrender.com" "$HOME/.terminalchat/app/terminalchat.py" "$@"
EOF

chmod +x "$INSTALL_DIR/tc-online"
ln -sf "$INSTALL_DIR/tc-online" "$SYMLINK_DIR/tc-online"

echo "To use the online version, run 'tc-online' instead of 'tc'"
