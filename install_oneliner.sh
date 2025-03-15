#!/bin/bash
# One-line installer for terminalchat
# Usage: curl -s https://raw.githubusercontent.com/your-username/terminalchat/main/install_oneliner.sh | bash

echo "Installing TerminalChat..."
python3 -m pip install --user rich
cd /tmp && curl -s -L -o terminalchat.py https://raw.githubusercontent.com/your-username/terminalchat/main/terminalchat.py
chmod +x /tmp/terminalchat.py
mkdir -p $HOME/.local/bin
cp /tmp/terminalchat.py $HOME/.local/bin/terminalchat
echo 'export PATH="$HOME/.local/bin:$PATH"' >> $HOME/.bashrc
echo 'export PATH="$HOME/.local/bin:$PATH"' >> $HOME/.zshrc
source $HOME/.bashrc 2>/dev/null || source $HOME/.zshrc 2>/dev/null
echo "TerminalChat installed successfully! You can now use 'terminalchat' command."
echo "If the command is not found, please restart your terminal or run: export PATH=\"\$HOME/.local/bin:\$PATH\""
