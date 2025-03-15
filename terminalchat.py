#!/usr/bin/env python3

import os
import sys
import json
import time
import argparse
import getpass
import platform
import subprocess
import shutil
import tempfile
import warnings

# Suppress all warnings
warnings.filterwarnings("ignore")

import requests
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.progress import Progress
from rich.markdown import Markdown
from rich import box
from datetime import datetime
from getpass import getpass  # Use getpass instead of getpass.getpass
import urllib3
import re

# Suppress urllib3 warnings
urllib3.disable_warnings()

# Try to import required packages, install if missing
try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress
    import rich.box
    import requests
except ImportError:
    print("Installing required packages...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich", "requests"])
    
    # Now import the packages
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.text import Text
    from rich.progress import Progress
    import rich.box
    import requests

# Create console for rich output
console = Console()

# Constants
APP_DIR = os.path.expanduser("~/.terminalchat")
USERS_FILE = os.path.join(APP_DIR, "users.json")
MESSAGES_DIR = os.path.join(APP_DIR, "messages")
FILES_DIR = os.path.join(APP_DIR, "files")
CONFIG_FILE = os.path.join(APP_DIR, "config.json")
BLOCKED_FILE = os.path.join(APP_DIR, "blocked.json")
MAX_FILE_SIZE = 5 * 1024 * 1024 * 1024  # 5GB in bytes
DOWNLOADS_DIR = os.path.expanduser("~/Downloads")  # Default downloads directory
DATA_DIR = os.path.join(APP_DIR, "data")

# Server configuration
SERVER_URL = os.environ.get('TERMINALCHAT_SERVER_URL', 'http://localhost:5001')  # Local server URL for testing
USE_SERVER = True  # Always use server mode for internet messaging

# Update configuration
REPO_URL = "https://github.com/terminalchat/terminalchat"
VERSION = "1.0.0"
COPYRIGHT = " Shortcut Studios"
MESSAGES_PER_PAGE = 20  # Number of messages to show per page

# Setup application directories
def setup_app_directories():
    """Setup application directories"""
    # Create app directory if it doesn't exist
    os.makedirs(APP_DIR, exist_ok=True)
    
    # Create downloads directory if it doesn't exist
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    
    # Create data directory if it doesn't exist
    os.makedirs(DATA_DIR, exist_ok=True)
    
    # Create users file if it doesn't exist
    if not os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'w') as f:
            json.dump({}, f)
    
    # Create config file if it doesn't exist
    if not os.path.exists(CONFIG_FILE):
        with open(CONFIG_FILE, 'w') as f:
            json.dump({
                'logged_in': False,
                'username': None,
                'token': None,
                'server_url': SERVER_URL,
                'use_server': USE_SERVER
            }, f, indent=2)
    
    # Create blocked users file if it doesn't exist
    if not os.path.exists(BLOCKED_FILE):
        with open(BLOCKED_FILE, 'w') as f:
            json.dump([], f)

# Server communication functions
def server_request(endpoint, method="GET", data=None, files=None, token=None, progress_callback=None):
    """Make a request to the server"""
    url = f"{SERVER_URL}/{endpoint}"
    headers = {}
    
    if token:
        headers["Authorization"] = f"Bearer {token}"
    
    try:
        if method == "GET":
            response = requests.get(url, headers=headers, timeout=10)
        elif method == "POST":
            if files:
                response = requests.post(url, headers=headers, data=data, files=files, timeout=30)
            else:
                response = requests.post(url, headers=headers, json=data, timeout=10)
        elif method == "PUT":
            response = requests.put(url, headers=headers, json=data, timeout=10)
        elif method == "DELETE":
            response = requests.delete(url, headers=headers, timeout=10)
        else:
            console.print(f"[bold red]Invalid method: {method}[/bold red]")
            return None
        
        # Check if the response is JSON
        try:
            return response.json()
        except:
            return response.content
    except requests.exceptions.ConnectionError:
        console.print("[bold red]Could not connect to the server. Please check your internet connection.[/bold red]")
        return None
    except requests.exceptions.Timeout:
        console.print("[bold red]The server took too long to respond. Please try again later.[/bold red]")
        return None
    except Exception as e:
        console.print(f"[bold red]An error occurred: {str(e)}[/bold red]")
        return None

def get_server_token():
    """Get the authentication token from config"""
    config = get_config()
    return config.get("token", None)

def save_server_token(token):
    """Save the authentication token to config"""
    config = get_config()
    config["token"] = token
    save_config(config)

# User management functions
def get_users():
    if USE_SERVER:
        token = get_server_token()
        if not token:
            return {}
        
        users = server_request("users", token=token)
        if users:
            return users
        else:
            # Fallback to local if server fails
            with open(USERS_FILE, 'r') as f:
                return json.load(f)
    else:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)

def save_users(users):
    if not USE_SERVER:
        with open(USERS_FILE, 'w') as f:
            json.dump(users, f)

def get_current_user():
    """Get the current logged in user"""
    config = get_config()
    return config.get('username', None)

def save_current_user(username):
    config = get_config()
    config["username"] = username
    save_config(config)

def signup(username, password):
    if USE_SERVER:
        result = server_request("signup", method="POST", data={"username": username, "password": password})
        if result and result.get("success"):
            save_server_token(result.get("token"))
            save_current_user(username)
            console.print(f"[bold green]User {username} created successfully![/bold green]")
            return True
        else:
            console.print("[bold red]Failed to create user on server![/bold red]")
            return False
    else:
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
    if USE_SERVER:
        result = server_request("login", method="POST", data={"username": username, "password": password})
        if result and result.get("success"):
            save_server_token(result.get("token"))
            save_current_user(username)
            console.print(f"[bold green]Logged in as {username}![/bold green]")
            return True
        else:
            console.print("[bold red]Failed to login on server![/bold red]")
            return False
    else:
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
    if USE_SERVER:
        token = get_server_token()
        if token:
            server_request("logout", method="POST", token=token)
        
        # Clear token
        save_server_token(None)
    
    save_current_user(None)
    console.print("[bold yellow]Logged out successfully![/bold yellow]")

def delete_account():
    current_user = get_current_user()
    
    if not current_user:
        console.print("[bold red]You are not logged in![/bold red]")
        return False
    
    if USE_SERVER:
        token = get_server_token()
        if token:
            result = server_request("delete_account", method="DELETE", token=token)
            if result and result.get("success"):
                save_server_token(None)
                save_current_user(None)
                console.print("[bold green]Account deleted successfully![/bold green]")
                return True
            else:
                console.print("[bold red]Failed to delete account on server![/bold red]")
                return False
    else:
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

# Blocked users functions
def get_blocked_users():
    current_user = get_current_user()
    if not current_user:
        return []
        
    if USE_SERVER:
        token = get_server_token()
        if token:
            blocked = server_request("blocked", token=token)
            if blocked:
                return blocked
    
    # Fallback to local if server fails or not using server
    with open(BLOCKED_FILE, 'r') as f:
        blocked_data = json.load(f)
    return blocked_data.get(current_user, [])

def block_user(username):
    current_user = get_current_user()
    if not current_user:
        console.print("[bold red]You are not logged in![/bold red]")
        return False
        
    if current_user == username:
        console.print("[bold red]You cannot block yourself![/bold red]")
        return False
        
    if USE_SERVER:
        token = get_server_token()
        if token:
            result = server_request("blocked", method="POST", 
                                  data={"username": username}, token=token)
            if result and result.get("success"):
                console.print(f"[bold green]User {username} has been blocked.[/bold green]")
                return True
            else:
                console.print(f"[bold red]Failed to block user {username}![/bold red]")
                return False
    
    # Fallback to local if server fails or not using server
    with open(BLOCKED_FILE, 'r') as f:
        blocked_data = json.load(f)
    
    if current_user not in blocked_data:
        blocked_data[current_user] = []
        
    if username in blocked_data[current_user]:
        console.print(f"[bold yellow]User {username} is already blocked.[/bold yellow]")
        return True
        
    blocked_data[current_user].append(username)
    
    with open(BLOCKED_FILE, 'w') as f:
        json.dump(blocked_data, f)
        
    console.print(f"[bold green]User {username} has been blocked.[/bold green]")
    return True

def unblock_user(username):
    current_user = get_current_user()
    if not current_user:
        console.print("[bold red]You are not logged in![/bold red]")
        return False
        
    if USE_SERVER:
        token = get_server_token()
        if token:
            result = server_request(f"blocked/{username}", method="DELETE", token=token)
            if result and result.get("success"):
                console.print(f"[bold green]User {username} has been unblocked.[/bold green]")
                return True
            else:
                console.print(f"[bold red]Failed to unblock user {username}![/bold red]")
                return False
    
    # Fallback to local if server fails or not using server
    with open(BLOCKED_FILE, 'r') as f:
        blocked_data = json.load(f)
    
    if current_user not in blocked_data or username not in blocked_data[current_user]:
        console.print(f"[bold yellow]User {username} is not blocked.[/bold yellow]")
        return False
        
    blocked_data[current_user].remove(username)
    
    with open(BLOCKED_FILE, 'w') as f:
        json.dump(blocked_data, f)
        
    console.print(f"[bold green]User {username} has been unblocked.[/bold green]")
    return True

def is_blocked(sender, recipient):
    """Check if a user is blocked"""
    if USE_SERVER:
        token = get_server_token()
        if token:
            try:
                result = server_request(f"blocked/{recipient}", token=token)
                if isinstance(result, dict):
                    return result.get("blocked", False)
            except:
                # Fall back to local if there's an error
                pass
    
    # Fallback to local if server fails or not using server
    with open(BLOCKED_FILE, 'r') as f:
        blocked_data = json.load(f)
    return (recipient in blocked_data.get(sender, []) or 
            sender in blocked_data.get(recipient, []))

# Message management functions
def get_message_file(sender, recipient):
    # Ensure the directory exists
    os.makedirs(os.path.join(MESSAGES_DIR, sender), exist_ok=True)
    return os.path.join(MESSAGES_DIR, sender, f"{recipient}.json")

def get_messages(sender, recipient):
    if USE_SERVER:
        token = get_server_token()
        if token:
            messages = server_request(f"messages/{recipient}", token=token)
            if messages:
                return messages
    
    # Fallback to local if server fails or not using server
    messages_file = get_message_file(sender, recipient)
    
    if not os.path.exists(messages_file):
        return []
    
    with open(messages_file, 'r') as f:
        return json.load(f)

def save_messages(sender, recipient, messages):
    if not USE_SERVER:
        message_file = get_message_file(sender, recipient)
        with open(message_file, 'w') as f:
            json.dump(messages, f)

def get_all_chats(username):
    """Get a list of all users the current user has chatted with"""
    if USE_SERVER:
        token = get_server_token()
        if token:
            chats = server_request("chats", token=token)
            if chats:
                return chats
    
    # Fallback to local if server fails or not using server
    user_messages_dir = os.path.join(MESSAGES_DIR, username)
    if not os.path.exists(user_messages_dir):
        return []
    
    chats = []
    for filename in os.listdir(user_messages_dir):
        if filename.endswith('.json'):
            chat_user = filename[:-5]  # Remove .json extension
            chats.append(chat_user)
    
    return chats

def delete_chat(username, other_user):
    """Delete chat history with a specific user"""
    if USE_SERVER:
        token = get_server_token()
        if token:
            result = server_request(f"chats/{other_user}", method="DELETE", token=token)
            if result and result.get("success"):
                console.print(f"[bold green]Chat with {other_user} deleted successfully![/bold green]")
                return True
            else:
                console.print(f"[bold red]Failed to delete chat with {other_user}![/bold red]")
                return False
    
    # Fallback to local if server fails or not using server
    message_file = get_message_file(username, other_user)
    if os.path.exists(message_file):
        os.remove(message_file)
        console.print(f"[bold green]Chat with {other_user} deleted successfully![/bold green]")
        return True
    else:
        console.print(f"[bold yellow]No chat history found with {other_user}.[/bold yellow]")
        return False

def send_message(recipient, message_text):
    """Send a message to a user"""
    if not is_logged_in():
        console.print("[bold red]You must be logged in to send messages.[/bold red]")
        return False
    
    current_user = get_current_user()
    
    # Check if the recipient exists
    if not user_exists(recipient):
        console.print(f"[bold red]User {recipient} does not exist.[/bold red]")
        return False
    
    # Check if the user is blocked
    if is_blocked(current_user, recipient):
        console.print(f"[bold red]You have blocked {recipient} or they have blocked you.[/bold red]")
        return False
    
    # Create the message
    timestamp = datetime.now().isoformat()
    message = {
        "sender": current_user,
        "recipient": recipient,
        "content": message_text,
        "timestamp": timestamp,
        "read": False,
        "is_file": False
    }
    
    # Send the message to the server
    if USE_SERVER:
        token = get_server_token()
        if token:
            result = server_request(f"messages/{recipient}", method="POST", data=message, token=token)
            if result and result.get('success'):
                return True
            else:
                error = result.get('error', 'Unknown error') if result else 'Could not connect to server'
                console.print(f"[bold red]Failed to send message: {error}[/bold red]")
                return False
    
    # Fallback to local if server fails or not using server
    messages_dir = os.path.join(MESSAGES_DIR, current_user)
    os.makedirs(messages_dir, exist_ok=True)
    
    message_file = os.path.join(messages_dir, f"{recipient}.json")
    
    messages = []
    if os.path.exists(message_file):
        try:
            with open(message_file, 'r') as f:
                messages = json.load(f)
        except json.JSONDecodeError:
            messages = []
    
    messages.append(message)
    
    with open(message_file, 'w') as f:
        json.dump(messages, f, indent=2)
    
    return True

def save_message(sender, recipient, message_text):
    if is_blocked(sender, recipient):
        console.print("[bold red]You cannot send messages to this user. You may be blocked or have blocked them.[/bold red]")
        return False
    
    if USE_SERVER:
        token = get_server_token()
        if token:
            result = server_request("messages", method="POST", data={
                "recipient": recipient,
                "message": message_text
            }, token=token)
            
            if result and result.get("success"):
                console.print(f"[bold green]Message sent to {recipient}![/bold green]")
                return True
            else:
                console.print(f"[bold red]Failed to send message to {recipient}![/bold red]")
                return False
    
    # Fallback to local if server fails or not using server
    # Save message in sender's file
    sender_messages = get_messages(sender, recipient)
    sender_messages.append({
        "sender": sender,
        "recipient": recipient,
        "message": message_text,
        "timestamp": datetime.now().isoformat(),
        "read": True
    })
    save_messages(sender, recipient, sender_messages)
    
    # Save message in recipient's file
    recipient_messages = get_messages(recipient, sender)
    recipient_messages.append({
        "sender": sender,
        "recipient": recipient,
        "message": message_text,
        "timestamp": datetime.now().isoformat(),
        "read": False
    })
    save_messages(recipient, sender, recipient_messages)
    
    console.print(f"[bold green]Message sent to {recipient}![/bold green]")
    return True

def send_file(sender, recipient, file_path):
    """Send a file to another user"""
    # Expand ~ to home directory if present
    file_path = os.path.expanduser(file_path)
    
    if not os.path.exists(file_path):
        console.print(f"[bold red]File {file_path} does not exist![/bold red]")
        return False
    
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        console.print(f"[bold red]File is too large! Maximum size is {MAX_FILE_SIZE / (1024 * 1024 * 1024)}GB.[/bold red]")
        return False
    
    file_name = os.path.basename(file_path)
    
    if USE_SERVER:
        token = get_server_token()
        if token:
            with open(file_path, 'rb') as f:
                files = {'file': (file_name, f)}
                
                # Show ASCII progress bar
                console.print(f"[bold cyan]Uploading {file_name} to {recipient}...[/bold cyan]")
                
                # Create a custom progress bar
                total_size = os.path.getsize(file_path)
                uploaded = 0
                bar_length = 40
                
                def progress_callback(monitor):
                    nonlocal uploaded
                    uploaded = monitor.bytes_read
                    progress = min(1.0, uploaded / total_size)
                    bar = "█" * int(bar_length * progress) + "░" * (bar_length - int(bar_length * progress))
                    percent = int(progress * 100)
                    console.print(f"\r[{bar}] {percent}% ({format_size(uploaded)}/{format_size(total_size)})", end="")
                
                # Use a custom adapter with progress tracking
                result = server_request(f"files/{recipient}", method="POST", 
                                      files=files, token=token, 
                                      progress_callback=progress_callback)
                
                console.print()  # New line after progress bar
                
                if result and result.get("success"):
                    console.print(f"[bold green]File {file_name} sent to {recipient}![/bold green]")
                    return True
                else:
                    console.print(f"[bold red]Failed to send file to {recipient}![/bold red]")
                    return False
    
    # Fallback to local if server fails or not using server
    # Copy file to recipient's directory
    os.makedirs(os.path.join(FILES_DIR, recipient), exist_ok=True)
    recipient_file_path = os.path.join(FILES_DIR, recipient, file_name)
    
    try:
        # Show ASCII progress bar for local copy
        console.print(f"[bold cyan]Copying {file_name} to {recipient}...[/bold cyan]")
        
        total_size = os.path.getsize(file_path)
        copied = 0
        bar_length = 40
        
        with open(file_path, 'rb') as src, open(recipient_file_path, 'wb') as dst:
            while True:
                buf = src.read(1024 * 1024)  # 1MB chunks
                if not buf:
                    break
                dst.write(buf)
                copied += len(buf)
                
                # Update progress bar
                progress = min(1.0, copied / total_size)
                bar = "█" * int(bar_length * progress) + "░" * (bar_length - int(bar_length * progress))
                percent = int(progress * 100)
                console.print(f"\r[{bar}] {percent}% ({format_size(copied)}/{format_size(total_size)})", end="")
        
        console.print()  # New line after progress bar
    except Exception as e:
        console.print(f"[bold red]Failed to copy file: {str(e)}[/bold red]")
        return False
    
    # Save message about the file transfer
    save_message(sender, recipient, f"[FILE] {file_name}")
    
    console.print(f"[bold green]File sent successfully to {recipient}![/bold green]")
    return True

def format_size(size):
    """Format file size in human-readable format"""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024.0:
            return f"{size:.2f} {unit}"
        size /= 1024.0
    return f"{size:.2f} PB"

def display_messages(username, messages, page, total_pages):
    """Display messages with pagination"""
    console.clear()
    console.print(f"[bold cyan]Chat with {username} (Page {page}/{total_pages})[/bold cyan]")
    console.print("[bold cyan]Type '~' to exit, 'p' for previous page, 'n' for next page[/bold cyan]")
    console.print()
    
    # If messages is empty, return early
    if not messages:
        return
    
    # Calculate the slice of messages to display
    start_idx = (page - 1) * MESSAGES_PER_PAGE
    end_idx = min(start_idx + MESSAGES_PER_PAGE, len(messages))
    
    # Get the messages for this page
    page_messages = messages[start_idx:end_idx]
    
    # Display the messages
    for message in page_messages:
        if not isinstance(message, dict):
            continue
            
        sender = message.get('sender', '')
        content = message.get('content', '')
        timestamp = message.get('timestamp', '')
        is_file = message.get('is_file', False)
        
        # Format the timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp
        
        # Determine the style based on the sender
        if sender == get_current_user():
            sender_style = "green"
            align = "right"
        else:
            sender_style = "blue"
            align = "left"
        
        # Create the message text
        if is_file:
            message_text = Text(f"📎 {content} (File)")
        else:
            message_text = Text(content)
        
        # Create the panel
        panel = Panel(
            message_text,
            title=f"[{sender_style}]{sender}[/{sender_style}] - {formatted_time}",
            border_style=sender_style
        )
        
        # Print the panel
        console.print(panel, justify=align)
    
    console.print()

# Command handlers
def handle_signup(args):
    """Handle the signup command"""
    if is_logged_in():
        console.print("[bold yellow]You are already logged in. Please log out first.[/bold yellow]")
        return
    
    # Get the username
    username = args.username
    if not username:
        username = input("Enter username: ")
    
    # Get the password
    password = getpass("Enter password: ")
    password_confirm = getpass("Confirm password: ")
    
    # Check if passwords match
    if password != password_confirm:
        console.print("[bold red]Passwords do not match![/bold red]")
        return
    
    # Sign up the user
    result = server_request("signup", method="POST", data={"username": username, "password": password})
    
    if result and result.get('success'):
        console.print(f"[bold green]User {username} created successfully![/bold green]")
        
        # Automatically log in
        login_result = server_request("login", method="POST", data={"username": username, "password": password})
        
        if login_result and login_result.get('success'):
            # Save the token
            config = get_config()
            config['logged_in'] = True
            config['username'] = username
            config['token'] = login_result.get('token')
            save_config(config)
            
            console.print(f"[bold green]Logged in as {username}![/bold green]")
        else:
            console.print("[bold yellow]Account created but could not log in automatically. Please log in manually.[/bold yellow]")
    else:
        error_message = result.get('error', 'Unknown error') if result else 'Could not connect to server'
        console.print(f"[bold red]Failed to create user: {error_message}[/bold red]")

def handle_login(args):
    """Handle the login command"""
    if is_logged_in():
        clear_terminal()
        console.print(f"[bold yellow]You are already logged in as {get_current_user()}[/bold yellow]")
        return
    
    # Get the username
    username = args.username
    if not username:
        username = input("Enter username: ")
    
    # Get the password
    password = getpass("Enter password: ")
    
    # Log in the user
    result = server_request("login", method="POST", data={"username": username, "password": password})
    
    if result and result.get('success'):
        # Save the token
        config = get_config()
        config['logged_in'] = True
        config['username'] = username
        config['token'] = result.get('token')
        save_config(config)
        
        clear_terminal()
        console.print(f"[bold green]Logged in as {username}![/bold green]")
    else:
        error_message = result.get('error', 'Invalid username or password') if result else 'Could not connect to server'
        clear_terminal()
        console.print(f"[bold red]Failed to log in: {error_message}[/bold red]")

def handle_logout(args):
    """Handle the logout command"""
    if not is_logged_in():
        clear_terminal()
        console.print("[bold yellow]You are not logged in.[/bold yellow]")
        return
    
    # Log out the user
    token = get_server_token()
    if token:
        server_request("logout", method="POST", token=token)
    
    # Clear the config
    config = get_config()
    config['logged_in'] = False
    config['username'] = None
    config['token'] = None
    save_config(config)
    
    clear_terminal()
    console.print("[bold green]Logged out successfully![/bold green]")

def handle_message(args):
    """Handle the message command"""
    if not is_logged_in():
        console.print("[bold red]You must be logged in to send messages.[/bold red]")
        return
    
    # Get the username
    username = args.username
    if not username:
        username = input("Enter username to message: ")
    
    # Check if direct message was provided
    if hasattr(args, 'text') and args.text:
        # Send the message directly
        send_message(username, args.text)
        console.print(f"[bold green]Message sent to {username}[/bold green]")
        return
    
    # Get the page number
    page = 1
    if hasattr(args, 'page') and args.page and args.page.isdigit():
        page = int(args.page)
    
    # Get the messages
    token = get_server_token()
    result = server_request(f"messages/{username}", token=token)
    
    messages = []
    if result and isinstance(result, list):
        messages = result
    
    # Calculate pagination
    total_pages = max(1, (len(messages) + MESSAGES_PER_PAGE - 1) // MESSAGES_PER_PAGE)
    
    if page > total_pages:
        page = total_pages
    
    # Display the messages
    display_messages(username, messages, page, total_pages)
    
    # Enter chat mode
    chat_mode(username)

def handle_send(args):
    """Handle the send command"""
    if not is_logged_in():
        console.print("[bold red]You must be logged in to send files.[/bold red]")
        return
    
    # Get the username and file path
    username = args.username
    file_path = args.file
    
    # Check if the file exists
    if not os.path.exists(file_path):
        console.print(f"[bold red]File not found: {file_path}[/bold red]")
        return
    
    # Check the file size
    file_size = os.path.getsize(file_path)
    if file_size > MAX_FILE_SIZE:
        console.print(f"[bold red]File is too large: {format_file_size(file_size)}. Maximum size is {format_file_size(MAX_FILE_SIZE)}.[/bold red]")
        return
    
    # Send the file
    with open(file_path, 'rb') as f:
        file_data = f.read()
    
    token = get_server_token()
    with Progress() as progress:
        task = progress.add_task("[cyan]Uploading file...", total=100)
        
        # Create a files dictionary for the request
        files = {
            'file': (os.path.basename(file_path), file_data, 'application/octet-stream')
        }
        
        # Send the file
        result = server_request(f"files/{username}", method="POST", token=token, files=files)
        
        # Update progress
        progress.update(task, completed=100)
    
    if result and result.get('success'):
        console.print(f"[bold green]File sent to {username} successfully![/bold green]")
    else:
        error_message = result.get('error', 'Unknown error') if result else 'Could not connect to server'
        console.print(f"[bold red]Failed to send file: {error_message}[/bold red]")

# Display messages
def display_messages(username, messages, page, total_pages):
    """Display messages with pagination"""
    console.clear()
    console.print(f"[bold cyan]Chat with {username} (Page {page}/{total_pages})[/bold cyan]")
    console.print("[bold cyan]Type '~' to exit, 'p' for previous page, 'n' for next page[/bold cyan]")
    console.print()
    
    # If messages is empty, return early
    if not messages:
        return
    
    # Calculate the slice of messages to display
    start_idx = (page - 1) * MESSAGES_PER_PAGE
    end_idx = min(start_idx + MESSAGES_PER_PAGE, len(messages))
    
    # Get the messages for this page
    page_messages = messages[start_idx:end_idx]
    
    # Display the messages
    for message in page_messages:
        if not isinstance(message, dict):
            continue
            
        sender = message.get('sender', '')
        content = message.get('content', '')
        timestamp = message.get('timestamp', '')
        is_file = message.get('is_file', False)
        
        # Format the timestamp
        try:
            dt = datetime.fromisoformat(timestamp)
            formatted_time = dt.strftime("%Y-%m-%d %H:%M:%S")
        except:
            formatted_time = timestamp
        
        # Determine the style based on the sender
        if sender == get_current_user():
            sender_style = "green"
            align = "right"
        else:
            sender_style = "blue"
            align = "left"
        
        # Create the message text
        if is_file:
            message_text = Text(f"📎 {content} (File)")
        else:
            message_text = Text(content)
        
        # Create the panel
        panel = Panel(
            message_text,
            title=f"[{sender_style}]{sender}[/{sender_style}] - {formatted_time}",
            border_style=sender_style
        )
        
        # Print the panel
        console.print(panel, justify=align)
    
    console.print()

# Chat mode
def chat_mode(username):
    """Enter chat mode with a user"""
    while True:
        # Get the message
        message = input("> ")
        
        # Check for navigation commands
        if message == "~":
            # Exit chat mode
            break
        elif message == "p":
            # Previous page
            # This would need to be implemented with state tracking
            console.print("[bold yellow]Previous page navigation not implemented in this version.[/bold yellow]")
            continue
        elif message == "n":
            # Next page
            # This would need to be implemented with state tracking
            console.print("[bold yellow]Next page navigation not implemented in this version.[/bold yellow]")
            continue
        
        # Send the message
        if message:
            token = get_server_token()
            result = server_request(f"messages/{username}", method="POST", token=token, data={"content": message})
            
            if result and result.get('success'):
                # Refresh the messages
                messages = server_request(f"messages/{username}", token=token)
                
                if messages:
                    # Display the last page of messages
                    total_pages = (len(messages) + MESSAGES_PER_PAGE - 1) // MESSAGES_PER_PAGE
                    if total_pages == 0:
                        total_pages = 1
                    
                    display_messages(username, messages, total_pages, total_pages)
            else:
                error_message = result.get('error', 'Unknown error') if result else 'Could not connect to server'
                console.print(f"[bold red]Failed to send message: {error_message}[/bold red]")

# Format file size
def format_file_size(size_bytes):
    """Format file size in a human-readable format"""
    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"

def handle_about(args):
    """Display information about TerminalChat"""
    logo = """
    ████████╗███████╗██████╗ ███╗   ███╗██╗███╗   ██╗ █████╗ ██╗      ██████╗██╗  ██╗ █████╗ ████████╗
    ╚══██╔══╝██╔════╝██╔══██╗████╗ ████║██║████╗  ██║██╔══██╗██║     ██╔════╝██║  ██║██╔══██╗╚══██╔══╝
       ██║   █████╗  ██████╔╝██╔████╔██║██║██╔██╗ ██║███████║██║     ██║     ███████║███████║   ██║   
       ██║   ██╔══╝  ██╔══██╗██║╚██╔╝██║██║██║╚██╗██║██╔══██║██║     ██║     ██╔══██║██╔══██║   ██║   
       ██║   ███████╗██║  ██║██║ ╚═╝ ██║██║██║ ╚████║██║  ██║███████╗╚██████╗██║  ██║██║  ██║   ██║   
       ╚═╝   ╚══════╝╚═╝  ╚═╝╚═╝     ╚═╝╚═╝╚═╝  ╚═══╝╚═╝  ╚═╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝  ╚═╝   ╚═╝   
    """
    
    about_text = f"""
    [bold cyan]TerminalChat[/bold cyan] - A simple terminal-based chat application
    
    [bold]Version:[/bold] {VERSION}
    [bold]Server Mode:[/bold] {'Enabled' if USE_SERVER else 'Disabled'}
    [bold]Server URL:[/bold] {SERVER_URL}
    
    [bold]Features:[/bold]
    • Send messages to other users
    • Transfer files securely
    • Block unwanted users
    • Work both locally and over the internet
    • System notifications for new messages
    
    [bold]{COPYRIGHT}[/bold]
    """
    
    console.print(logo, style="cyan")
    console.print(Panel(about_text, title="About TerminalChat", border_style="cyan"))

def handle_status(args):
    """Display the current status of TerminalChat"""
    clear_terminal()
    
    current_user = get_current_user()
    
    status_text = f"""
    [bold]Current User:[/bold] {current_user if current_user else 'Not logged in'}
    [bold]Server Mode:[/bold] {'Enabled' if USE_SERVER else 'Disabled'}
    [bold]Version:[/bold] {VERSION}
    """
    
    # Check for new messages
    if current_user:
        new_messages = check_for_new_messages()
        if new_messages:
            status_text += f"\n[bold]New Messages:[/bold] {len(new_messages)}"
    
    console.print(Panel(status_text, title="TerminalChat Status", border_style="cyan"))

def handle_chat_list(args):
    current_user = get_current_user()
    
    if not current_user:
        clear_terminal()
        console.print("[bold red]You are not logged in! Please login first.[/bold red]")
        return
    
    # Get all message files
    user_messages_dir = os.path.join(MESSAGES_DIR, current_user)
    
    if not os.path.exists(user_messages_dir):
        os.makedirs(user_messages_dir, exist_ok=True)
    
    chats = []
    
    if USE_SERVER:
        token = get_server_token()
        if token:
            server_chats = server_request("chats", token=token)
            if server_chats and isinstance(server_chats, list):
                chats = server_chats
    
    # Fallback to local if server fails or not using server
    if not chats:
        message_files = []
        for filename in os.listdir(MESSAGES_DIR):
            if filename.endswith('.json'):
                parts = filename.split('_')
                if len(parts) >= 2:
                    user1 = parts[0]
                    user2 = parts[1].split('.')[0]
                    
                    if user1 == current_user or user2 == current_user:
                        other_user = user2 if user1 == current_user else user1
                        message_files.append((other_user, filename))
        
        for other_user, _ in message_files:
            messages = get_messages(current_user, other_user)
            
            if messages:
                last_message = messages[-1]
                last_message_text = last_message.get("content", "")
                timestamp = last_message.get("timestamp", "")
                
                try:
                    formatted_time = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M")
                except:
                    formatted_time = timestamp
                
                # Check if there are unread messages
                has_unread = has_unread_messages(other_user)
                
                # Check if the last message is a file
                is_file = last_message.get("is_file", False)
                
                chats.append({
                    "username": other_user,
                    "last_message": last_message_text,
                    "timestamp": formatted_time,
                    "unread": has_unread,
                    "is_file": is_file
                })
    
    if not chats:
        clear_terminal()
        console.print("[bold yellow]You have no active chats.[/bold yellow]")
        return
    
    table = Table(title="Your Chats", box=rich.box.ROUNDED)
    table.add_column("Username", style="cyan")
    table.add_column("Last Message", style="white")
    table.add_column("Time", style="green")
    table.add_column("Status", style="yellow")
    
    for chat in sorted(chats, key=lambda x: x.get("timestamp", ""), reverse=True):
        username = chat.get("username", "")
        last_message = chat.get("last_message", "")
        timestamp = chat.get("timestamp", "")
        has_unread = chat.get("unread", 0)
        
        # Format the last message
        if chat.get("is_file", False):
            last_message = f"📎 {last_message}"
        
        # Truncate long messages
        if len(last_message) > 30:
            last_message = last_message[:27] + "..."
        
        # Use red style for users with unread messages
        username_style = "bold red" if has_unread else "cyan"
        status = f"[bold red]{has_unread} unread[/bold red]" if has_unread else ""
        
        table.add_row(
            f"[{username_style}]{username}[/{username_style}]",
            last_message,
            timestamp,
            status
        )
    
    console.print(table)

def handle_chat_delete(args):
    current_user = get_current_user()
    
    if not current_user:
        console.print("[bold red]You are not logged in! Please login first.[/bold red]")
        return
    
    username = args.username
    
    if not username:
        console.print("[bold yellow]Please specify a username to delete chat history with.[/bold yellow]")
        console.print("Usage: terminalchat chat delete USERNAME")
        return
    
    delete_chat(current_user, username)

def handle_block(args):
    clear_terminal()
    current_user = get_current_user()
    
    if not current_user:
        console.print("[bold red]You are not logged in! Please login first.[/bold red]")
        return
    
    username = args.username
    
    if not username:
        console.print("[bold red]Please specify a username to block.[/bold red]")
        console.print("Usage: terminalchat block USERNAME")
        return
    
    block_user(username)

def handle_unblock(args):
    clear_terminal()
    current_user = get_current_user()
    
    if not current_user:
        console.print("[bold red]You are not logged in! Please login first.[/bold red]")
        return
    
    username = args.username
    
    if not username:
        console.print("[bold red]Please specify a username to unblock.[/bold red]")
        console.print("Usage: terminalchat unblock USERNAME")
        return
    
    unblock_user(username)

def handle_list_blocked(args):
    clear_terminal()
    current_user = get_current_user()
    
    if not current_user:
        console.print("[bold red]You are not logged in! Please login first.[/bold red]")
        return
    
    blocked_users = get_blocked_users()
    
    if not blocked_users:
        console.print("[bold yellow]You have not blocked any users.[/bold yellow]")
        return
    
    table = Table(title="Blocked Users", box=rich.box.ROUNDED)
    table.add_column("Username", style="red")
    
    for user in blocked_users:
        table.add_row(user)
    
    console.print(table)

def handle_server(args):
    """This function is kept for backward compatibility but does nothing"""
    console.print("[bold cyan]TerminalChat is always online![/bold cyan]")
    console.print("[bold yellow]Note: The server command is deprecated and will be removed in a future version.[/bold yellow]")

def handle_uninstall(args):
    confirm = console.input("[bold red]Are you sure you want to uninstall TerminalChat? This will delete all your local data. (y/n): [/bold red]")
    
    if confirm.lower() != 'y':
        console.print("[bold yellow]Uninstall cancelled.[/bold yellow]")
        return
    
    # Remove application directory
    if os.path.exists(APP_DIR):
        shutil.rmtree(APP_DIR)
    
    console.print("[bold green]TerminalChat has been uninstalled from your system.[/bold green]")
    console.print("[bold yellow]Note: You may need to manually remove the terminalchat command from your PATH.[/bold yellow]")

def handle_update(args):
    """Update TerminalChat to the latest version"""
    console.print("[bold cyan]Checking for updates...[/bold cyan]")
    
    if USE_SERVER:
        # Check with the server for the latest version
        token = get_server_token()
        if token:
            latest_version = server_request("version", token=token)
            if latest_version and latest_version.get("version") != VERSION:
                console.print(f"[bold green]New version available: {latest_version.get('version')}[/bold green]")
                console.print(f"[bold yellow]Current version: {VERSION}[/bold yellow]")
                
                if not args.force:
                    confirm = console.input("[bold cyan]Do you want to update? (y/n): [/bold cyan]")
                    if confirm.lower() != 'y':
                        console.print("[bold yellow]Update cancelled.[/bold yellow]")
                        return
                
                # Download and install the latest version
                console.print("[bold cyan]Downloading latest version...[/bold cyan]")
                
                try:
                    # Create a temporary directory for the update
                    temp_dir = os.path.join(APP_DIR, "update")
                    os.makedirs(temp_dir, exist_ok=True)
                    
                    # Clone or pull the repository
                    if shutil.which("git"):
                        # Use git if available
                        if os.path.exists(os.path.join(temp_dir, ".git")):
                            # Git repository already exists, pull latest changes
                            subprocess.run(["git", "pull"], cwd=temp_dir, check=True)
                        else:
                            # Clone the repository
                            subprocess.run(["git", "clone", REPO_URL, temp_dir], check=True)
                    else:
                        # Download the zip file
                        zip_url = f"{REPO_URL}/archive/main.zip"
                        zip_path = os.path.join(temp_dir, "terminalchat.zip")
                        
                        with requests.get(zip_url, stream=True) as r:
                            r.raise_for_status()
                            with open(zip_path, 'wb') as f:
                                for chunk in r.iter_content(chunk_size=8192):
                                    f.write(chunk)
                        
                        # Extract the zip file
                        import zipfile
                        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
                            zip_ref.extractall(temp_dir)
                    
                    # Find the terminalchat.py file
                    terminalchat_path = None
                    for root, dirs, files in os.walk(temp_dir):
                        if "terminalchat.py" in files:
                            terminalchat_path = os.path.join(root, "terminalchat.py")
                            break
                    
                    if not terminalchat_path:
                        console.print("[bold red]Could not find terminalchat.py in the downloaded files![/bold red]")
                        return
                    
                    # Get the path to the current script
                    current_script = os.path.abspath(sys.argv[0])
                    
                    # Backup the current script
                    backup_path = current_script + ".backup"
                    shutil.copy2(current_script, backup_path)
                    
                    # Replace the current script with the new one
                    shutil.copy2(terminalchat_path, current_script)
                    
                    # Clean up
                    shutil.rmtree(temp_dir)
                    
                    console.print("[bold green]TerminalChat has been updated to the latest version![/bold green]")
                    console.print("[bold yellow]Please restart TerminalChat to use the new version.[/bold yellow]")
                    
                except Exception as e:
                    console.print(f"[bold red]Failed to update: {str(e)}[/bold red]")
                    console.print(f"[bold yellow]You can manually update by downloading the latest version from {REPO_URL}[/bold yellow]")
                
                return
    
    # If we reach here, either server mode is disabled or no update is available
    console.print(f"[bold green]You are running the latest version of TerminalChat (v{VERSION})![/bold green]")

def handle_delete_account(args):
    """Handle the delete account command"""
    if not is_logged_in():
        console.print("[bold red]You must be logged in to delete your account.[/bold red]")
        return
    
    # Confirm deletion
    clear_terminal()
    console.print("[bold yellow]WARNING: This will permanently delete your account and all your messages.[/bold yellow]")
    console.print("[bold yellow]This action cannot be undone.[/bold yellow]")
    confirm = input("Type your username to confirm deletion: ")
    
    if confirm != get_current_user():
        console.print("[bold red]Account deletion cancelled. Username did not match.[/bold red]")
        return
    
    # Delete the account
    token = get_server_token()
    result = server_request("account", method="DELETE", token=token)
    
    if result and result.get('success'):
        # Clear the config
        config = get_config()
        config['logged_in'] = False
        config['username'] = None
        config['token'] = None
        save_config(config)
        
        clear_terminal()
        console.print("[bold green]Your account has been deleted successfully.[/bold green]")
    else:
        error_message = result.get('error', 'Unknown error') if result else 'Could not connect to server'
        clear_terminal()
        console.print(f"[bold red]Failed to delete account: {error_message}[/bold red]")

def show_notification(message):
    """Show a system notification"""
    try:
        # Check the operating system
        if sys.platform == "darwin":  # macOS
            # Use osascript to show notification
            os.system(f"""
            osascript -e 'display notification "{message}" with title "TerminalChat"'
            """)
        elif sys.platform == "linux":
            # Use notify-send on Linux
            os.system(f'notify-send "TerminalChat" "{message}"')
        elif sys.platform == "win32":
            # Use Windows toast notifications
            try:
                from win10toast import ToastNotifier
                toaster = ToastNotifier()
                toaster.show_toast("TerminalChat", message, duration=5)
            except ImportError:
                # Fall back to console notification
                console.print(f"[bold cyan]NOTIFICATION:[/bold cyan] {message}")
        else:
            # Fall back to console notification
            console.print(f"[bold cyan]NOTIFICATION:[/bold cyan] {message}")
    except Exception as e:
        # Silently fail for notifications
        pass

def handle_file_received(sender, file_name, file_data=None, file_path=None):
    """Handle a received file by saving it to the Downloads directory"""
    # Create Downloads directory if it doesn't exist
    os.makedirs(DOWNLOADS_DIR, exist_ok=True)
    
    # Generate a unique filename to avoid overwriting existing files
    base_name, ext = os.path.splitext(file_name)
    target_path = os.path.join(DOWNLOADS_DIR, file_name)
    
    counter = 1
    
    # If file already exists, add a number to the filename
    while os.path.exists(target_path):
        target_path = os.path.join(DOWNLOADS_DIR, f"{base_name}_{counter}{ext}")
        counter += 1
    
    try:
        if file_data:
            # Save file data directly
            with open(target_path, 'wb') as f:
                f.write(file_data)
        elif file_path:
            # Copy file from source path
            shutil.copy2(file_path, target_path)
        else:
            console.print("[bold red]No file data or path provided![/bold red]")
            return False
        
        # Send a notification
        show_notification(f"File received from {sender}: {os.path.basename(target_path)}")
        console.print(f"[bold green]File from {sender} saved to {target_path}[/bold green]")
        return True
    except Exception as e:
        console.print(f"[bold red]Failed to save file: {str(e)}[/bold red]")
        return False

def has_unread_messages(username):
    """Check if a user has unread messages from a specific sender"""
    current_user = get_current_user()
    if not current_user:
        return False
    
    messages = get_messages(current_user, username)
    
    for message in messages:
        if message["sender"] == username and not message.get("read", False):
            return True
    
    return False

def check_for_new_messages():
    """Check for new messages from other users"""
    # Skip if not logged in
    if not is_logged_in():
        return
    
    try:
        # Get the current user
        current_user = get_current_user()
        
        # Get all chats
        if USE_SERVER:
            token = get_server_token()
            if not token:
                return
            
            # Get chats from server
            chats = server_request("chats", token=token)
            
            # Count unread messages
            unread_count = sum(chat.get('unread', 0) for chat in chats)
            
            # Show notification if there are unread messages
            if unread_count > 0:
                # Show system notification
                show_notification(f"You have {unread_count} unread message(s)")
        else:
            # Local mode not supported for new message checks
            pass
    except Exception as e:
        # Silently fail for background checks
        pass

def is_logged_in():
    """Check if a user is logged in"""
    config = get_config()
    return config.get('logged_in', False)

def get_config():
    """Get the configuration from the config file"""
    if not os.path.exists(CONFIG_FILE):
        return {
            'logged_in': False,
            'username': None,
            'token': None,
            'server_url': SERVER_URL,
            'use_server': USE_SERVER
        }
    
    with open(CONFIG_FILE, 'r') as f:
        return json.load(f)

def save_config(config):
    """Save the configuration to the config file"""
    with open(CONFIG_FILE, 'w') as f:
        json.dump(config, f, indent=2)

def user_exists(username):
    """Check if a user exists"""
    if USE_SERVER:
        token = get_server_token()
        if token:
            result = server_request(f"user/{username}", token=token)
            if result and result.get('exists'):
                return True
    
    # Fallback to local if server fails or not using server
    users_file = os.path.join(DATA_DIR, 'users.json')
    if os.path.exists(users_file):
        try:
            with open(users_file, 'r') as f:
                users = json.load(f)
                return username in users
        except json.JSONDecodeError:
            pass
    
    return False

def clear_terminal():
    """Clear the terminal screen"""
    os_name = platform.system().lower()
    if os_name == 'windows':
        os.system('cls')
    else:
        os.system('clear')

def show_help():
    help_text = """
    [bold cyan]TerminalChat - A simple terminal-based chat application[/bold cyan]
    
    [bold cyan]Commands:[/bold cyan]
    
    [bold cyan]terminalchat signup[/bold cyan] or [bold cyan]tc signup[/bold cyan]
        Create a new account
        Options:
            --username USERNAME
            --password PASSWORD
    
    [bold cyan]terminalchat login[/bold cyan] or [bold cyan]tc login[/bold cyan]
        Login to your account
        Options:
            --username USERNAME
            --password PASSWORD
    
    [bold cyan]terminalchat logout[/bold cyan] or [bold cyan]tc logout[/bold cyan]
        Logout from your account
    
    [bold cyan]terminalchat message USERNAME[/bold cyan] or [bold cyan]tc message USERNAME[/bold cyan]
        Send a message to a user
    
    [bold cyan]terminalchat chat USERNAME[/bold cyan] or [bold cyan]tc chat USERNAME[/bold cyan]
        Chat with a user (alias for message)
    
    [bold cyan]terminalchat list[/bold cyan] or [bold cyan]tc list[/bold cyan]
        List all your chats
    
    [bold cyan]terminalchat block USERNAME[/bold cyan] or [bold cyan]tc block USERNAME[/bold cyan]
        Block a user
    
    [bold cyan]terminalchat unblock USERNAME[/bold cyan] or [bold cyan]tc unblock USERNAME[/bold cyan]
        Unblock a user
    
    [bold cyan]terminalchat blocked[/bold cyan] or [bold cyan]tc blocked[/bold cyan]
        List all blocked users
    
    [bold cyan]terminalchat send USERNAME FILE_PATH[/bold cyan] or [bold cyan]tc send USERNAME FILE_PATH[/bold cyan]
        Send a file to a user
    
    [bold cyan]terminalchat status[/bold cyan] or [bold cyan]tc status[/bold cyan]
        Show your current status
    
    [bold cyan]terminalchat update[/bold cyan] or [bold cyan]tc update[/bold cyan]
        Check for updates
    
    [bold cyan]terminalchat uninstall[/bold cyan] or [bold cyan]tc uninstall[/bold cyan]
        Uninstall TerminalChat from your system
    
    [bold cyan]terminalchat delete[/bold cyan] or [bold cyan]tc delete[/bold cyan]
        Delete your account
    
    [bold cyan]terminalchat help[/bold cyan] or [bold cyan]tc help[/bold cyan]
        Show this help message
    
    """
    # Clear the terminal before showing help
    clear_terminal()
    console.print(help_text)

def main():
    # Setup application directories
    setup_app_directories()
    
    # Check for new messages
    check_for_new_messages()
    
    # Create the argument parser with custom error handling
    class CustomArgumentParser(argparse.ArgumentParser):
        def error(self, message):
            # Show custom error message
            show_invalid_command()
            # Exit without showing the default error message
            sys.exit(0)
    
    # Use our custom parser
    parser = CustomArgumentParser(prog='tc', description='TerminalChat - A simple terminal-based chat application')
    parser.add_argument('--version', action='version', version=f'TerminalChat {VERSION}')
    
    subparsers = parser.add_subparsers(dest='command', help='Command to run')
    
    # Signup command
    signup_parser = subparsers.add_parser('signup', help='Create a new account')
    signup_parser.add_argument('username', nargs='?', help='Username for the new account')
    signup_parser.add_argument('--password', help='Password for the new account')
    
    # Login command
    login_parser = subparsers.add_parser('login', help='Log in to your account')
    login_parser.add_argument('username', nargs='?', help='Username to log in with')
    login_parser.add_argument('--password', help='Password to log in with')
    
    # Logout command
    logout_parser = subparsers.add_parser('logout', help='Log out from your account')
    
    # Message command
    message_parser = subparsers.add_parser('message', help='Send a message to a user')
    message_parser.add_argument('username', nargs='?', help='Username to message')
    message_parser.add_argument('text', nargs='?', help='Message text (optional)')
    message_parser.add_argument('--page', help='Page number for pagination')
    
    # Chat command (alias for message)
    chat_parser = subparsers.add_parser('chat', help='Chat with a user (alias for message)')
    chat_parser.add_argument('username', nargs='?', help='Username to chat with')
    chat_parser.add_argument('text', nargs='?', help='Message text (optional)')
    chat_parser.add_argument('--page', help='Page number for pagination')
    
    # Chat list command
    chat_list_parser = subparsers.add_parser('chat_list', help='List all your chats')
    
    # Simpler alias for chat_list
    list_parser = subparsers.add_parser('list', help='List all your chats (alias for chat_list)')
    
    # Block command
    block_parser = subparsers.add_parser('block', help='Block a user')
    block_parser.add_argument('username', nargs='?', help='Username to block')
    
    # Unblock command
    unblock_parser = subparsers.add_parser('unblock', help='Unblock a user')
    unblock_parser.add_argument('username', nargs='?', help='Username to unblock')
    
    # Blocked list command
    blocked_parser = subparsers.add_parser('blocked', help='List all blocked users')
    
    # Send file command
    send_file_parser = subparsers.add_parser('send_file', help='Send a file to a user')
    send_file_parser.add_argument('username', help='Username to send file to')
    send_file_parser.add_argument('file_path', help='Path to file')
    
    # Simpler alias for send_file
    send_parser = subparsers.add_parser('send', help='Send a file to a user (alias for send_file)')
    send_parser.add_argument('username', help='Username to send file to')
    send_parser.add_argument('file_path', help='Path to file')
    
    # Status command
    status_parser = subparsers.add_parser('status', help='Show your current status')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Check for updates')
    
    # Uninstall command
    uninstall_parser = subparsers.add_parser('uninstall', help='Uninstall TerminalChat')
    
    # Delete account command
    delete_account_parser = subparsers.add_parser('delete_account', help='Delete your account')
    
    # Simpler alias for delete_account
    delete_parser = subparsers.add_parser('delete', help='Delete your account (alias for delete_account)')
    
    # Help command
    help_parser = subparsers.add_parser('help', help='Show help information')
    
    try:
        # Parse the arguments
        args = parser.parse_args()
        
        # Handle the commands
        if args.command == 'signup':
            handle_signup(args)
        elif args.command == 'login':
            handle_login(args)
        elif args.command == 'logout':
            handle_logout(args)
        elif args.command == 'message' or args.command == 'chat':
            handle_message(args)
        elif args.command == 'chat_list' or args.command == 'list':
            handle_chat_list(args)
        elif args.command == 'block':
            handle_block(args)
        elif args.command == 'unblock':
            handle_unblock(args)
        elif args.command == 'blocked':
            handle_list_blocked(args)
        elif args.command == 'send_file' or args.command == 'send':
            handle_send_file(args)
        elif args.command == 'status':
            handle_status(args)
        elif args.command == 'update':
            handle_update(args)
        elif args.command == 'uninstall':
            handle_uninstall(args)
        elif args.command == 'delete_account' or args.command == 'delete':
            handle_delete_account(args)
        elif args.command == 'help' or not args.command:
            show_help()
        else:
            show_invalid_command()
    except SystemExit:
        # This catches the case when argparse exits due to --help
        pass
    except Exception as e:
        console.print(Panel(f"[bold red]An error occurred:[/bold red] {str(e)}", title="Error", border_style="red"))

def show_invalid_command():
    """Show a nice error message for invalid commands"""
    clear_terminal()
    console.print(Panel(
        "[bold red]Invalid command[/bold red]\n\n"
        "Run [bold cyan]terminalchat help[/bold cyan] or [bold cyan]tc help[/bold cyan] to see available commands.",
        title="Error",
        border_style="red"
    ))

# Create a symbolic link for 'tc' command
def create_tc_symlink():
    """Create a symbolic link for 'tc' as an abbreviation for 'terminalchat'"""
    try:
        # Get the path to the terminalchat script
        terminalchat_path = os.path.abspath(sys.argv[0])
        
        # Determine common bin directories
        bin_dirs = ['/usr/local/bin', '/usr/bin', os.path.expanduser('~/.local/bin')]
        
        # Find where terminalchat is installed
        terminalchat_bin = None
        for bin_dir in bin_dirs:
            possible_path = os.path.join(bin_dir, 'terminalchat')
            if os.path.exists(possible_path):
                terminalchat_bin = possible_path
                break
        
        if not terminalchat_bin:
            # If we couldn't find it, use the current script path
            terminalchat_bin = terminalchat_path
        
        # Create the tc symlink in the same directory
        tc_bin = os.path.join(os.path.dirname(terminalchat_bin), 'tc')
        
        # Check if the symlink already exists
        if os.path.exists(tc_bin):
            # If it exists but doesn't point to terminalchat, replace it
            if os.path.islink(tc_bin) and os.readlink(tc_bin) != terminalchat_bin:
                os.remove(tc_bin)
                os.symlink(terminalchat_bin, tc_bin)
        else:
            # Create the symlink
            os.symlink(terminalchat_bin, tc_bin)
            
        return True
    except Exception as e:
        console.print(f"[bold yellow]Note: Could not create 'tc' command shortcut: {str(e)}[/bold yellow]")
        console.print("[bold yellow]You may need to manually create a symlink or alias for 'tc'.[/bold yellow]")
        return False

if __name__ == "__main__":
    # Check if the script is being run directly
    if len(sys.argv) > 1 and sys.argv[0].endswith('terminalchat.py'):
        # If this is the first run or an update, try to create the tc symlink
        create_tc_symlink()
    
    main()
