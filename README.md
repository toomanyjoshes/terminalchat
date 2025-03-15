# TerminalChat

A super simple chat application that runs entirely in your terminal. Message anyone by username, transfer files up to 5GB, and manage your chats - all through a simple command-line interface.

## Features

- Simple username/password authentication (no email required)
- Send and receive messages in real-time
- Transfer files up to 5GB
- List all your chats and users
- Clean ASCII interface using Rich for beautiful terminal UI
- Works on macOS and Linux

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

After installation, you can use the `terminalchat` command from anywhere in your terminal:

### Create an account

```bash
terminalchat signup
# or
terminalchat signup username
```

### Login to your account

```bash
terminalchat login
# or
terminalchat login username
```

### List all your chats

```bash
terminalchat list
# or
tc list
```

### Send a message to someone

```bash
terminalchat message username
# or using the alias
terminalchat chat username
```

When in a chat, you can:
- Type a message and press Enter to send
- Type `file:/path/to/file` to send a file
- Type `exit` to leave the chat

### Send a message directly from the command line

```bash
terminalchat message username "Your message here"
# or using the alias
terminalchat chat username "Your message here"
```

### Block a user

```bash
terminalchat block username
# or
tc block username
```

### Unblock a user

```bash
terminalchat unblock username
# or
tc unblock username
```

### List blocked users

```bash
terminalchat blocked
# or
tc blocked
```

### Send a file to someone

```bash
terminalchat send username /path/to/file
# or
tc send username /path/to/file
```

### See your current status

```bash
terminalchat status
# or
tc status
```

### Logout

```bash
terminalchat logout
# or
tc logout
```

### Delete your account

```bash
terminalchat delete
# or
tc delete
```

### Get help

```bash
terminalchat help
```

## Deployment

### Deploying to Render

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

Render will automatically deploy your application and provide you with a URL like `https://terminalchat-server.onrender.com`.

### Using the Online Server

Once you have deployed the server to Render, you can use the `tc-online.sh` script to connect to it:

```bash
# First, update the RENDER_URL in the script with your actual Render URL
nano tc-online.sh

# Then run the script
./tc-online.sh login
```

Alternatively, you can set the environment variable directly:

```bash
export TERMINALCHAT_SERVER_URL="https://terminalchat-server.onrender.com"
python terminalchat.py login
```

Or run the client with the server URL in a single command:

```bash
TERMINALCHAT_SERVER_URL="https://terminalchat-server.onrender.com" python terminalchat.py login
```

### Deploy the server

The TerminalChat server can be deployed to various cloud platforms:

#### Heroku

1. Sign up for a Heroku account
2. Install the Heroku CLI
3. Run the following commands:
   ```bash
   heroku login
   heroku create terminalchat-server
   git push heroku main
   ```

### Connect the client to your deployed server

To connect your TerminalChat client to your deployed server, set the `SERVER_URL` environment variable:

```bash
export TERMINALCHAT_SERVER_URL="https://your-deployed-server-url.com"
```

Or edit the `terminalchat.py` file to update the `SERVER_URL` constant.

## Requirements

- Python 3.6+
- Rich library (automatically installed)
- Flask (for server)
- Requests (for client)

## License

MIT
