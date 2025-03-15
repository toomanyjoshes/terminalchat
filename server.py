#!/usr/bin/env python3

import os
import json
import uuid
import hashlib
import time
from datetime import datetime
from flask import Flask, request, jsonify, send_file
from flask_cors import CORS
from werkzeug.utils import secure_filename

app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Constants
DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "server_data")
USERS_FILE = os.path.join(DATA_DIR, "users.json")
MESSAGES_DIR = os.path.join(DATA_DIR, "messages")
FILES_DIR = os.path.join(DATA_DIR, "files")
TOKENS_FILE = os.path.join(DATA_DIR, "tokens.json")
BLOCKED_FILE = os.path.join(DATA_DIR, "blocked.json")

# Ensure directories exist
os.makedirs(DATA_DIR, exist_ok=True)
os.makedirs(MESSAGES_DIR, exist_ok=True)
os.makedirs(FILES_DIR, exist_ok=True)

# Initialize empty data files if they don't exist
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(TOKENS_FILE):
    with open(TOKENS_FILE, 'w') as f:
        json.dump({}, f)

if not os.path.exists(BLOCKED_FILE):
    with open(BLOCKED_FILE, 'w') as f:
        json.dump({}, f)

# Helper functions
def get_users():
    """Get all users from the users file"""
    try:
        with open(USERS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_users(users):
    """Save users to the users file"""
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f, indent=2)

def get_tokens():
    """Get all tokens from the tokens file"""
    try:
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}

def save_tokens(tokens):
    """Save tokens to the tokens file"""
    with open(TOKENS_FILE, 'w') as f:
        json.dump(tokens, f, indent=2)

def get_user_by_token(token):
    """Get a user by their token"""
    # Extract the token from the Bearer format if present
    if token and token.startswith('Bearer '):
        token = token[7:]
        
    tokens = get_tokens()
    if token in tokens:
        return tokens[token]
    return None

def get_messages(sender, recipient):
    """Get messages between two users"""
    message_path = os.path.join(MESSAGES_DIR, f"{sender}_{recipient}.json")
    reverse_path = os.path.join(MESSAGES_DIR, f"{recipient}_{sender}.json")
    
    messages = []
    
    # Check if the message file exists
    if os.path.exists(message_path):
        try:
            with open(message_path, 'r') as f:
                messages.extend(json.load(f))
        except json.JSONDecodeError:
            pass
    
    # Check if the reverse message file exists
    if os.path.exists(reverse_path):
        try:
            with open(reverse_path, 'r') as f:
                messages.extend(json.load(f))
        except json.JSONDecodeError:
            pass
    
    # Sort messages by timestamp
    messages.sort(key=lambda x: x.get('timestamp', ''))
    
    return messages

def save_message(sender, recipient, message_data):
    """Save a message between two users"""
    # Create a unique message file for this pair of users
    message_path = os.path.join(MESSAGES_DIR, f"{sender}_{recipient}.json")
    
    # Load existing messages or create a new list
    if os.path.exists(message_path):
        with open(message_path, 'r') as f:
            messages = json.load(f)
    else:
        messages = []
    
    # Add the new message
    messages.append(message_data)
    
    # Save the messages
    with open(message_path, 'w') as f:
        json.dump(messages, f, indent=2)

def get_user_chats(username):
    """Get all chats for a user"""
    chats = []
    for filename in os.listdir(MESSAGES_DIR):
        if filename.endswith('.json'):
            parts = filename.split('_')
            if len(parts) >= 2:
                user1 = parts[0]
                user2 = parts[1].split('.')[0]
                
                if user1 == username or user2 == username:
                    other_user = user2 if user1 == username else user1
                    
                    # Get the messages
                    messages = get_messages(user1, user2)
                    
                    if messages:
                        last_message = messages[-1]
                        chats.append({
                            'username': other_user,
                            'last_message': last_message.get('content', ''),
                            'timestamp': last_message.get('timestamp', ''),
                            'is_file': last_message.get('is_file', False),
                            'unread': sum(1 for msg in messages if msg.get('recipient') == username and not msg.get('read', False))
                        })
    
    # Sort chats by timestamp (newest first)
    chats.sort(key=lambda x: x['timestamp'], reverse=True)
    
    return chats

# API Routes
@app.route('/signup', methods=['POST'])
def signup():
    """Create a new user account"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    users = get_users()
    
    if username in users:
        return jsonify({'error': 'Username already exists'}), 400
    
    # Hash the password
    salt = uuid.uuid4().hex
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    
    # Create the user
    users[username] = {
        'password_hash': hashed_password,
        'salt': salt,
        'created_at': datetime.now().isoformat()
    }
    
    save_users(users)
    
    return jsonify({'success': True, 'message': 'User created successfully'}), 201

@app.route('/login', methods=['POST'])
def login():
    """Log in a user"""
    data = request.json
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'error': 'Username and password are required'}), 400
    
    users = get_users()
    
    if username not in users:
        return jsonify({'error': 'Invalid username or password'}), 401
    
    user = users[username]
    salt = user['salt']
    hashed_password = hashlib.sha256((password + salt).encode()).hexdigest()
    
    if hashed_password != user['password_hash']:
        return jsonify({'error': 'Invalid username or password'}), 401
    
    # Generate a token
    token = uuid.uuid4().hex
    
    # Save the token
    tokens = get_tokens()
    tokens[token] = username
    save_tokens(tokens)
    
    return jsonify({'success': True, 'token': token}), 200

@app.route('/users', methods=['GET'])
def users():
    """Get all users"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'error': 'Authorization token is required'}), 401
    
    username = get_user_by_token(token)
    
    if not username:
        return jsonify({'error': 'Invalid token'}), 401
    
    users = get_users()
    
    # Remove password hashes and salts
    user_list = [{'username': u} for u in users.keys() if u != username]
    
    return jsonify(user_list), 200

@app.route('/messages/<recipient>', methods=['GET'])
def get_user_messages(recipient):
    """Get messages between the current user and another user"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'error': 'Authorization token is required'}), 401
    
    sender = get_user_by_token(token)
    
    if not sender:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get the messages
    messages = get_messages(sender, recipient)
    
    # Mark messages as read
    for message in messages:
        if message.get('recipient') == sender and not message.get('read', False):
            message['read'] = True
    
    # Save the updated messages
    message_path = os.path.join(MESSAGES_DIR, f"{sender}_{recipient}.json")
    reverse_path = os.path.join(MESSAGES_DIR, f"{recipient}_{sender}.json")
    
    if os.path.exists(message_path):
        with open(message_path, 'w') as f:
            json.dump([m for m in messages if m.get('sender') == sender], f, indent=2)
    
    if os.path.exists(reverse_path):
        with open(reverse_path, 'w') as f:
            json.dump([m for m in messages if m.get('sender') == recipient], f, indent=2)
    
    return jsonify(messages), 200

@app.route('/messages/<recipient>', methods=['POST'])
def send_message(recipient):
    """Send a message to another user"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'error': 'Authorization token is required'}), 401
    
    sender = get_user_by_token(token)
    
    if not sender:
        return jsonify({'error': 'Invalid token'}), 401
    
    data = request.json
    content = data.get('content')
    
    if not content:
        return jsonify({'error': 'Message content is required'}), 400
    
    # Create the message
    message_data = {
        'sender': sender,
        'recipient': recipient,
        'content': content,
        'timestamp': datetime.now().isoformat(),
        'read': False,
        'is_file': False
    }
    
    # Save the message
    save_message(sender, recipient, message_data)
    
    return jsonify({'success': True, 'message': 'Message sent successfully'}), 201

@app.route('/files/<recipient>', methods=['POST'])
def send_file(recipient):
    """Send a file to another user"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'error': 'Authorization token is required'}), 401
    
    sender = get_user_by_token(token)
    
    if not sender:
        return jsonify({'error': 'Invalid token'}), 401
    
    if 'file' not in request.files:
        return jsonify({'error': 'No file part'}), 400
    
    file = request.files['file']
    
    if file.filename == '':
        return jsonify({'error': 'No selected file'}), 400
    
    # Secure the filename
    filename = secure_filename(file.filename)
    
    # Create a unique filename
    unique_filename = f"{uuid.uuid4().hex}_{filename}"
    
    # Save the file
    file_path = os.path.join(FILES_DIR, unique_filename)
    file.save(file_path)
    
    # Create the message
    message_data = {
        'sender': sender,
        'recipient': recipient,
        'content': filename,
        'file_id': unique_filename,
        'timestamp': datetime.now().isoformat(),
        'read': False,
        'is_file': True
    }
    
    # Save the message
    save_message(sender, recipient, message_data)
    
    return jsonify({'success': True, 'message': 'File sent successfully'}), 201

@app.route('/files/<file_id>', methods=['GET'])
def download_file(file_id):
    """Download a file"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'error': 'Authorization token is required'}), 401
    
    username = get_user_by_token(token)
    
    if not username:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Check if the file exists
    file_path = os.path.join(FILES_DIR, file_id)
    
    if not os.path.exists(file_path):
        return jsonify({'error': 'File not found'}), 404
    
    # Get the original filename
    original_filename = file_id.split('_', 1)[1]
    
    # Return the file
    return send_file(file_path, as_attachment=True, download_name=original_filename)

@app.route('/chats', methods=['GET'])
def get_chats():
    """Get all chats for the current user"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'error': 'Authorization token is required'}), 401
    
    username = get_user_by_token(token)
    
    if not username:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get the chats
    chats = get_user_chats(username)
    
    return jsonify(chats), 200

@app.route('/chats/<username>', methods=['DELETE'])
def delete_chat(username):
    """Delete chat history with another user"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'error': 'Authorization token is required'}), 401
    
    current_user = get_user_by_token(token)
    
    if not current_user:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Delete the message files
    message_path = os.path.join(MESSAGES_DIR, f"{current_user}_{username}.json")
    reverse_path = os.path.join(MESSAGES_DIR, f"{username}_{current_user}.json")
    
    if os.path.exists(message_path):
        os.remove(message_path)
    
    if os.path.exists(reverse_path):
        os.remove(reverse_path)
    
    return jsonify({'success': True, 'message': 'Chat deleted successfully'}), 200

@app.route('/account', methods=['DELETE'])
def delete_account():
    """Delete a user account"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'error': 'Authorization token is required'}), 401
    
    # Extract the token from the Bearer format
    if token.startswith('Bearer '):
        token = token[7:]
    
    username = get_user_by_token(token)
    
    if not username:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get all users
    users = get_users()
    
    # Check if the user exists
    if username not in users:
        return jsonify({'error': 'User not found'}), 404
    
    # Delete the user
    del users[username]
    save_users(users)
    
    # Delete all messages involving this user
    for filename in os.listdir(MESSAGES_DIR):
        if filename.endswith('.json'):
            parts = filename.split('_')
            if len(parts) >= 2:
                user1 = parts[0]
                user2 = parts[1].split('.')[0]
                
                if user1 == username or user2 == username:
                    os.remove(os.path.join(MESSAGES_DIR, filename))
    
    # Delete all files sent by this user
    for filename in os.listdir(FILES_DIR):
        file_path = os.path.join(FILES_DIR, filename)
        if os.path.isfile(file_path):
            try:
                with open(file_path, 'r') as f:
                    file_data = json.load(f)
                    if file_data.get('sender') == username:
                        os.remove(file_path)
            except:
                pass
    
    # Delete the token
    tokens = get_tokens()
    for t, user in list(tokens.items()):
        if user == username:
            del tokens[t]
    save_tokens(tokens)
    
    return jsonify({'success': True, 'message': 'Account deleted successfully'}), 200

@app.route('/logout', methods=['POST'])
def logout():
    """Log out a user"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'success': True, 'message': 'Already logged out'}), 200
    
    # Remove the token
    tokens = get_tokens()
    
    if token in tokens:
        del tokens[token]
        save_tokens(tokens)
    
    return jsonify({'success': True, 'message': 'Logged out successfully'}), 200

@app.route('/status', methods=['GET'])
def status():
    """Check the server status"""
    return jsonify({
        'status': 'online',
        'version': '1.0.0',
        'time': datetime.now().isoformat()
    }), 200

@app.route('/user/<username>', methods=['GET'])
def check_user(username):
    """Check if a user exists"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'error': 'Authorization token is required'}), 401
    
    # Extract the token from the Bearer format if present
    if token.startswith('Bearer '):
        token = token[7:]
    
    # Verify the token
    requester = get_user_by_token(token)
    
    if not requester:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get all users
    users = get_users()
    
    # Check if the user exists
    exists = username in users
    
    return jsonify({'exists': exists}), 200

@app.route('/blocked/<username>', methods=['GET'])
def check_blocked(username):
    """Check if a user is blocked"""
    token = request.headers.get('Authorization')
    
    if not token:
        return jsonify({'error': 'Authorization token is required'}), 401
    
    # Extract the token from the Bearer format if present
    if token.startswith('Bearer '):
        token = token[7:]
    
    # Verify the token
    requester = get_user_by_token(token)
    
    if not requester:
        return jsonify({'error': 'Invalid token'}), 401
    
    # Get blocked users
    blocked_file = os.path.join(DATA_DIR, 'blocked.json')
    blocked_data = {}
    
    if os.path.exists(blocked_file):
        try:
            with open(blocked_file, 'r') as f:
                blocked_data = json.load(f)
        except json.JSONDecodeError:
            blocked_data = {}
    
    # Check if the user is blocked
    is_blocked = (username in blocked_data.get(requester, []) or 
                  requester in blocked_data.get(username, []))
    
    return jsonify({'blocked': is_blocked}), 200

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5001))
    app.run(host='0.0.0.0', port=port, debug=False)
