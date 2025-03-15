#!/bin/bash

# TerminalChat installer script
echo -e "\033[1;36m"
echo "╔════════════════════════════════════════╗"
echo "║       TerminalChat Installer           ║"
echo "║          © Shortcut Studios            ║"
echo "╚════════════════════════════════════════╝"
echo -e "\033[0m"

# Check if running as root when installing system-wide
if [[ "$1" == "system" ]] && [ "$EUID" -ne 0 ]; then
    echo "System-wide installation requires root privileges. Please run with sudo."
    exit 1
fi

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "Python 3 is required but not installed. Please install Python 3 and try again."
    exit 1
fi

# Determine installation type
INSTALL_TYPE=${1:-"user"}  # Default to user installation
INSTALL_DIR=""
BIN_DIR=""

if [[ "$INSTALL_TYPE" == "system" ]]; then
    # System-wide installation
    INSTALL_DIR="/opt/terminalchat"
    BIN_DIR="/usr/local/bin"
else
    # User installation
    INSTALL_DIR="$HOME/.terminalchat"
    BIN_DIR="$HOME/.local/bin"
    mkdir -p "$BIN_DIR"
fi

echo "Installing TerminalChat to $INSTALL_DIR..."
mkdir -p "$INSTALL_DIR"

# Download the latest version
echo "Downloading TerminalChat..."
if [ -d "$INSTALL_DIR/app" ]; then
    echo "Updating existing installation..."
    cd "$INSTALL_DIR/app" && git pull &>/dev/null
else
    git clone https://github.com/toomanyjoshes/terminalchat.git "$INSTALL_DIR/app" &>/dev/null
fi

# Install dependencies
echo "Installing dependencies..."
cd "$INSTALL_DIR/app" && pip3 install -r requirements.txt &>/dev/null

# Create the tc command script
cat > "$INSTALL_DIR/tc" << 'EOF'
#!/bin/bash

# Display banner
echo -e "\033[1;36m"
echo "╔════════════════════════════════════════╗"
echo "║           TerminalChat Online          ║"
echo "║          © Shortcut Studios            ║"
echo "╚════════════════════════════════════════╝"
echo -e "\033[0m"

# Set the online server URL
export TERMINALCHAT_SERVER_URL="https://terminalchat-server.onrender.com"

# Find the Python script
if [ -f "$HOME/.terminalchat/app/terminalchat.py" ]; then
    SCRIPT_PATH="$HOME/.terminalchat/app/terminalchat.py"
elif [ -f "/opt/terminalchat/app/terminalchat.py" ]; then
    SCRIPT_PATH="/opt/terminalchat/app/terminalchat.py"
else
    echo "Error: Could not find terminalchat.py"
    exit 1
fi

# Run TerminalChat
python3 "$SCRIPT_PATH" "$@"
EOF

chmod +x "$INSTALL_DIR/tc"

# Create symlink
ln -sf "$INSTALL_DIR/tc" "$BIN_DIR/tc"

# Check if the directory is in PATH for user installation
if [[ "$INSTALL_TYPE" != "system" ]] && [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
    echo "Adding $BIN_DIR to your PATH..."
    
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
        echo "Added $BIN_DIR to your PATH in $SHELL_CONFIG"
        echo "Please restart your terminal or run 'source $SHELL_CONFIG' to update your PATH."
    else
        echo "Please add $BIN_DIR to your PATH manually."
    fi
fi

echo -e "\033[1;32mTerminalChat has been installed!\033[0m"
echo -e "\033[1;32mYou can now use the 'tc' command from anywhere.\033[0m"
echo -e "\033[1;32mTry 'tc help' to get started.\033[0m"
