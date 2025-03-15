#!/bin/bash
# TerminalChat One-Command Installer
# Usage: curl -s https://raw.githubusercontent.com/your-username/terminalchat/main/terminalchat_installer.sh | bash

echo "📱 Installing TerminalChat..."

# Create installation directories
mkdir -p "$HOME/.local/bin"
mkdir -p "$HOME/.terminalchat"

# Download the script
cat > "$HOME/.local/bin/terminalchat" << 'EOF'
#!/usr/bin/env python3
import argparse
import os
import json
import getpass
import socket
import threading
import time
import sys
import shutil
from datetime import datetime
try:
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
except ImportError:
    print("Rich library is required. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "--user", "rich"])
    from rich.console import Console
    from rich.table import Table
    from rich.progress import Progress
    from rich.panel import Panel
    from rich.text import Text
    from rich import box
import uuid

console = Console()

# Constants
APP_DIR = os.path.expanduser("~/.terminalchat")
USERS_FILE = os.path.join(APP_DIR, "users.json")
MESSAGES_DIR = os.path.join(APP_DIR, "messages")
FILES_DIR = os.path.join(APP_DIR, "files")
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB in bytes
SERVER_HOST = '0.0.0.0'
SERVER_PORT = 8989

# Ensure application directories exist
def setup_app_directories():
    os.makedirs(APP_DIR, exist_ok=True)
    os.makedirs(MESSAGES_DIR, exist_ok=True)
    os.makedirs(FILES_DIR, exist_ok=True)
    
    # Initialize users file if it doesn't exist
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    
    # Initialize config file if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({"current_user": None}, f)

# User management functions
def get_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

def get_current_user():
    if os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'r') as f:
            config = json.load(f)
            return config.get("current_user")
    return None

def save_current_user(username):
    with open(CONFIG_FILE, 'r') as f:
        config = json.load(f)
    
    config["current_user"] = username
    
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f)

def signup(username, password):
    users = get_users()
    
    if username in users:
        console.print("[bold red]Username already exists![/bold red]")
        return False
    
    users[username] = {
        "password": password,
        "created_at": datetime.now().isoformat()
    }
    
    save_users(users)
    save_current_user(username)
    console.print(f"[bold green]User {username} created successfully![/bold green]")
    return True

def login(username, password):
    users = get_users()
    
    if username not in users:
        console.print("[bold red]Username does not exist![/bold red]")
        return False
    
    if users[username]["password"] != password:
        console.print("[bold red]Incorrect password![/bold red]")
        return False
    
    save_current_user(username)
    console.print(f"[bold green]Logged in as {username}![/bold green]")
    return True

def logout():
    save_current_user(None)
    console.print("[bold yellow]Logged out successfully![/bold yellow]")

def delete_account():
    current_user = get_current_user()
    
    if not current_user:
        console.print("[bold red]You are not logged in![/bold red]")
        return False
    
    users = get_users()
    
    if current_user in users:
        del users[current_user]
        save_users(users)
        
        # Delete user's messages
        user_messages_dir = os.path.join(MESSAGES_DIR, current_user)
        if os.path.exists(user_messages_dir):
            shutil.rmtree(user_messages_dir)
        
        # Delete user's files
        user_files_dir = os.path.join(FILES_DIR, current_user)
        if os.path.exists(user_files_dir):
            shutil.rmtree(user_files_dir)
        
        save_current_user(None)
        console.print("[bold green]Account deleted successfully![/bold green]")
        return True
    
    console.print("[bold red]Failed to delete account![/bold red]")
    return False

# Message management functions
def get_message_file(sender, recipient):
    # Ensure the directory exists
    os.makedirs(os.path.join(MESSAGES_DIR, sender), exist_ok=True)
    
    # Sort usernames to ensure the same file is used regardless of who is sending
    users = sorted([sender, recipient])
    filename = f"{users[0]}_{users[1]}.json"
    
    message_file = os.path.join(MESSAGES_DIR, sender, filename)
    
    if not os.path.exists(message_file):
        with open(message_file, 'w') as f:
            json.dump([], f)
    
    return message_file

def get_messages(sender, recipient):
    message_file = get_message_file(sender, recipient)
    
    with open(message_file, 'r') as f:
        return json.load(f)

def save_message(sender, recipient, message_text):
    message_file = get_message_file(sender, recipient)
    
    with open(message_file, 'r') as f:
        messages = json.load(f)
    
    messages.append({
        "id": str(uuid.uuid4()),
        "sender": sender,
        "recipient": recipient,
        "text": message_text,
        "timestamp": datetime.now().isoformat(),
        "read": False
    })
    
    with open(message_file, 'w') as f:
        json.dump(messages, f)

def get_all_chats():
    current_user = get_current_user()
    
    if not current_user:
        console.print("[bold red]You are not logged in![/bold red]")
        return []
    
    user_dir = os.path.join(MESSAGES_DIR, current_user)
    
    if not os.path.exists(user_dir):
        return []
    
    chats = []
    
    for filename in os.listdir(user_dir):
        if filename.endswith('.json'):
            users = filename.replace('.json', '').split('_')
            other_user = users[0] if users[0] != current_user else users[1]
            
            # Get the last message
            message_file = os.path.join(user_dir, filename)
            with open(message_file, 'r') as f:
                messages = json.load(f)
            
            if messages:
                last_message = messages[-1]
                chats.append({
                    "user": other_user,
                    "last_message": last_message["text"],
                    "timestamp": last_message["timestamp"],
                    "unread": sum(1 for msg in messages if msg["recipient"] == current_user and not msg["read"])
                })
    
    # Sort by timestamp (newest first)
    chats.sort(key=lambda x: x["timestamp"], reverse=True)
    
    return chats

def mark_messages_as_read(sender, recipient):
    message_file = get_message_file(sender, recipient)
    
    with open(message_file, 'r') as f:
        messages = json.load(f)
    
    updated = False
    for message in messages:
        if message["recipient"] == sender and not message["read"]:
            message["read"] = True
            updated = True
    
    if updated:
        with open(message_file, 'w') as f:
            json.dump(messages, f)

# File transfer functions
def send_file(sender, recipient, file_path):
    if not os.path.exists(file_path):
        console.print(f"[bold red]File {file_path} does not exist![/bold red]")
        return False
    
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        console.print(f"[bold red]File size exceeds the maximum limit of 5GB![/bold red]")
        return False
    
    # Create directories if they don't exist
    sender_files_dir = os.path.join(FILES_DIR, sender)
    recipient_files_dir = os.path.join(FILES_DIR, recipient)
    os.makedirs(sender_files_dir, exist_ok=True)
    os.makedirs(recipient_files_dir, exist_ok=True)
    
    # Generate a unique filename
    file_id = str(uuid.uuid4())
    file_name = os.path.basename(file_path)
    dest_file = os.path.join(recipient_files_dir, f"{file_id}_{file_name}")
    
    # Copy the file with progress bar
    with Progress() as progress:
        task = progress.add_task(f"[green]Sending {file_name} to {recipient}...", total=file_size)
        
        with open(file_path, 'rb') as src, open(dest_file, 'wb') as dst:
            copied = 0
            while True:
                buf = src.read(1024 * 1024)  # 1MB chunks
                if not buf:
                    break
                dst.write(buf)
                copied += len(buf)
                progress.update(task, completed=copied)
    
    # Save a message about the file transfer
    save_message(sender, recipient, f"[FILE] {file_name} ({format_size(file_size)})")
    
    console.print(f"[bold green]File sent successfully to {recipient}![/bold green]")
    return True

def list_files(username):
    files_dir = os.path.join(FILES_DIR, username)
    
    if not os.path.exists(files_dir):
        console.print("[bold yellow]No files found![/bold yellow]")
        return []
    
    files = []
    for filename in os.listdir(files_dir):
        file_path = os.path.join(files_dir, filename)
        file_size = os.path.getsize(file_path)
        file_id, *file_parts = filename.split('_', 1)
        original_name = '_'.join(file_parts) if file_parts else filename
        
        files.append({
            "id": file_id,
            "name": original_name,
            "size": file_size,
            "path": file_path
        })
    
    return files

def format_size(size_bytes):
    """Format file size in a human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB']:
        if size_bytes < 1024.0 or unit == 'GB':
            break
        size_bytes /= 1024.0
    return f"{size_bytes:.2f} {unit}"

# Command handlers
def handle_signup(args):
    username = args.username
    if not username:
        username = input("Enter username: ")
    
    password = getpass.getpass("Enter password: ")
    confirm_password = getpass.getpass("Confirm password: ")
    
    if password != confirm_password:
        console.print("[bold red]Passwords do not match![/bold red]")
        return
    
    signup(username, password)

def handle_login(args):
    username = args.username
    if not username:
        username = input("Enter username: ")
    
    password = getpass.getpass("Enter password: ")
    login(username, password)

def handle_logout(args):
    logout()

def handle_delete(args):
    current_user = get_current_user()
    
    if not current_user:
        console.print("[bold red]You are not logged in![/bold red]")
        return
    
    confirm = input(f"Are you sure you want to delete your account '{current_user}'? (y/n): ")
    
    if confirm.lower() == 'y':
        delete_account()

def handle_list(args):
    current_user = get_current_user()
    
    if not current_user:
        console.print("[bold red]You are not logged in![/bold red]")
        return
    
    chats = get_all_chats()
    
    if not chats:
        console.print("[bold yellow]No chats found![/bold yellow]")
        return
    
    table = Table(title=f"Chats for {current_user}", box=box.ROUNDED)
    table.add_column("Username", style="cyan")
    table.add_column("Last Message", style="green")
    table.add_column("Time", style="yellow")
    table.add_column("Unread", style="red")
    
    for chat in chats:
        timestamp = datetime.fromisoformat(chat["timestamp"]).strftime("%Y-%m-%d %H:%M")
        unread = str(chat["unread"]) if chat["unread"] > 0 else ""
        table.add_row(chat["user"], chat["last_message"][:30], timestamp, unread)
    
    console.print(table)

def handle_message(args):
    current_user = get_current_user()
    
    if not current_user:
        console.print("[bold red]You are not logged in![/bold red]")
        return
    
    recipient = args.username
    
    # Check if recipient exists
    users = get_users()
    if recipient not in users:
        console.print(f"[bold red]User {recipient} does not exist![/bold red]")
        return
    
    # Mark messages as read
    mark_messages_as_read(current_user, recipient)
    
    # Display previous messages
    messages = get_messages(current_user, recipient)
    
    console.clear()
    console.print(Panel(f"Chat with [bold]{recipient}[/bold]", style="cyan"))
    console.print("Type 'exit' to return to the main menu")
    console.print("Type 'file:path/to/file' to send a file")
    console.print("")
    
    for msg in messages:
        sender = msg["sender"]
        text = msg["text"]
        timestamp = datetime.fromisoformat(msg["timestamp"]).strftime("%H:%M")
        
        style = "green" if sender == current_user else "blue"
        align = "right" if sender == current_user else "left"
        sender_display = "You" if sender == current_user else sender
        
        message_text = Text(f"{text}")
        message_panel = Panel(
            message_text,
            title=f"{sender_display} ({timestamp})",
            style=style,
            width=60
        )
        
        console.print(message_panel, justify=align)
    
    # Chat loop
    while True:
        message_text = input("> ")
        
        if message_text.lower() == 'exit':
            break
        
        if message_text.startswith('file:'):
            file_path = message_text[5:].strip()
            send_file(current_user, recipient, file_path)
            continue
        
        if message_text:
            save_message(current_user, recipient, message_text)
            
            # Display the sent message
            timestamp = datetime.now().strftime("%H:%M")
            message_panel = Panel(
                Text(f"{message_text}"),
                title=f"You ({timestamp})",
                style="green",
                width=60
            )
            console.print(message_panel, justify="right")

def handle_files(args):
    current_user = get_current_user()
    
    if not current_user:
        console.print("[bold red]You are not logged in![/bold red]")
        return
    
    files = list_files(current_user)
    
    if not files:
        console.print("[bold yellow]No files found![/bold yellow]")
        return
    
    table = Table(title=f"Files for {current_user}", box=box.ROUNDED)
    table.add_column("ID", style="cyan")
    table.add_column("Name", style="green")
    table.add_column("Size", style="yellow")
    
    for file in files:
        table.add_row(file["id"][:8], file["name"], format_size(file["size"]))
    
    console.print(table)

def handle_users(args):
    users = get_users()
    
    if not users:
        console.print("[bold yellow]No users found![/bold yellow]")
        return
    
    table = Table(title="Registered Users", box=box.ROUNDED)
    table.add_column("Username", style="cyan")
    table.add_column("Created At", style="green")
    
    for username, user_data in users.items():
        created_at = datetime.fromisoformat(user_data["created_at"]).strftime("%Y-%m-%d %H:%M")
        table.add_row(username, created_at)
    
    console.print(table)

def handle_whoami(args):
    current_user = get_current_user()
    
    if current_user:
        console.print(f"[bold green]You are logged in as: {current_user}[/bold green]")
    else:
        console.print("[bold yellow]You are not logged in![/bold yellow]")

def main():
    setup_app_directories()
    
    parser = argparse.ArgumentParser(description='Terminal Chat Application')
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Signup command
    signup_parser = subparsers.add_parser('signup', help='Create a new account')
    signup_parser.add_argument('username', nargs='?', help='Username')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Login to your account')
    login_parser.add_argument('username', nargs='?', help='Username')
    
    # Logout command
    logout_parser = subparsers.add_parser('logout', help='Logout from your account')
    
    # Delete account command
    delete_parser = subparsers.add_parser('delete', help='Delete your account')
    
    # List chats command
    list_parser = subparsers.add_parser('list', help='List all your chats')
    
    # Message command
    message_parser = subparsers.add_parser('message', help='Send a message to a user')
    message_parser.add_argument('username', help='Username to message')
    
    # Files command
    files_parser = subparsers.add_parser('files', help='List your received files')
    
    # Users command
    users_parser = subparsers.add_parser('users', help='List all registered users')
    
    # Whoami command
    whoami_parser = subparsers.add_parser('whoami', help='Show current logged in user')
    
    args = parser.parse_args()
    
    if args.command == 'signup':
        handle_signup(args)
    elif args.command == 'login':
        handle_login(args)
    elif args.command == 'logout':
        handle_logout(args)
    elif args.command == 'delete':
        handle_delete(args)
    elif args.command == 'list':
        handle_list(args)
    elif args.command == 'message':
        handle_message(args)
    elif args.command == 'files':
        handle_files(args)
    elif args.command == 'users':
        handle_users(args)
    elif args.command == 'whoami':
        handle_whoami(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Exiting Terminal Chat...[/bold yellow]")
        sys.exit(0)
EOF

# Make it executable
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
