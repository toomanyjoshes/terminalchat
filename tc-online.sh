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

# Check if command was provided
if [ $# -eq 0 ]; then
  echo -e "\033[1;33mUsage: ./tc-online.sh <command> [arguments]\033[0m"
  echo -e "Example: ./tc-online.sh login"
  echo -e "For a full list of commands, use: ./tc-online.sh help"
  exit 1
fi

# Export the server URL
export TERMINALCHAT_SERVER_URL="$RENDER_URL"
echo -e "\033[1;32mConnecting to: $RENDER_URL\033[0m"

# Find the Python script
if [ -f "terminalchat.py" ]; then
  SCRIPT_PATH="terminalchat.py"
else
  # Download the script if it doesn't exist
  if [ ! -d "$HOME/.terminalchat" ]; then
    echo "First-time setup: Downloading TerminalChat..."
    mkdir -p "$HOME/.terminalchat/app"
    curl -s -L https://raw.githubusercontent.com/toomanyjoshes/terminalchat/main/terminalchat.py -o "$HOME/.terminalchat/app/terminalchat.py"
    curl -s -L https://raw.githubusercontent.com/toomanyjoshes/terminalchat/main/requirements.txt -o "$HOME/.terminalchat/app/requirements.txt"
    echo "Installing dependencies..."
    pip3 install -r "$HOME/.terminalchat/app/requirements.txt" &>/dev/null
  fi
  
  SCRIPT_PATH="$HOME/.terminalchat/app/terminalchat.py"
fi

# Run TerminalChat with the server URL
python3 "$SCRIPT_PATH" "$@"
