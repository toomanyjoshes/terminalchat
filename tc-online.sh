#!/bin/bash
# Script to run TerminalChat with the online server

# Your deployed Render URL
RENDER_URL="https://terminalchat-server.onrender.com"

# Run TerminalChat with the server URL
TERMINALCHAT_SERVER_URL="$RENDER_URL" python3 terminalchat.py "$@"
