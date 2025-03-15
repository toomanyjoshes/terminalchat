# TerminalChat

A super simple chat application that runs entirely in your terminal. Message anyone by username, transfer files up to 5GB, and manage your chats - all through a simple command-line interface.

## Features

- Simple username/password authentication (no email required)
- Send and receive messages in real-time
- Transfer files up to 5GB
- List all your chats and users
- Clean ASCII interface using Rich for beautiful terminal UI
- Works on macOS and Linux

## Quick Install

```bash
sudo curl -s https://raw.githubusercontent.com/toomanyjoshes/terminalchat/main/tc | bash
```

This command will download and install TerminalChat on your system, allowing you to use it from anywhere with the simple `tc` command.

## Installation

### Using pip (recommended)

```bash
pip install git+https://github.com/your-username/terminalchat.git
```

### From source

```bash
git clone https://github.com/your-username/terminalchat.git
cd terminalchat
pip install -e .
```

## Usage

After installation, you can use the `tc` command from anywhere in your terminal:

### Create an account

```bash
tc signup
# or
tc signup username
```

### Login to your account

```bash
tc login
# or
tc login username
```

### List all your chats

```bash
tc list
```

### Send a message to someone

```bash
tc message username
# or using the alias
tc chat username
```

When in a chat, you can:
- Type a message and press Enter to send
- Type `file:/path/to/file` to send a file
- Type `exit` to leave the chat

### Send a message directly from the command line

```bash
tc message username "Your message here"
# or using the alias
tc chat username "Your message here"
```

### Block a user

```bash
tc block username
```

### Unblock a user

```bash
tc unblock username
```

### List blocked users

```bash
tc blocked
```

### Send a file to someone

```bash
tc send username /path/to/file
```

### See your current status

```bash
tc status
```

### Logout

```bash
tc logout
```

### Delete your account

```bash
tc delete
```

### Get help

```bash
tc help
```

## About

TerminalChat is developed by © Shortcut Studios. It's designed to be simple, fast, and secure.

All communication is done through our secure online server at https://terminalchat-server.onrender.com.

## Deployment

### Deploying Your Own Server

If you want to deploy your own TerminalChat server:

1. Create a free account on [Render](https://render.com)
2. Click on "New" and select "Web Service"
3. Connect your GitHub account and select the `terminalchat` repository
4. Configure your web service with these settings:
   - Name: `terminalchat-server`
   - Environment: `Python`
   - Build Command: `pip install -r requirements.txt`
   - Start Command: `gunicorn server:app`
   - Instance Type: `Free`
5. Click "Create Web Service"

Render will automatically deploy your application and provide you with a URL.

### Using Your Custom Server

If you've deployed your own server, you can connect to it by setting the environment variable:

```bash
export TERMINALCHAT_SERVER_URL="https://your-server-url.com"
tc login
```

## License

TerminalChat is © Shortcut Studios. All rights reserved.
