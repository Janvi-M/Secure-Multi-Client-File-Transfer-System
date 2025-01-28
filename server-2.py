import os
import socket
import select
import signal
import sys
import logging
from concurrent.futures import ThreadPoolExecutor

# Server settings
HOST = '127.0.0.1'
PORT = 12345
UPLOAD_DIR = 'uploads'  # Base directory for file storage

# Logging configuration
logging.basicConfig(
    filename="server.log",
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(message)s"
)

# Initialize server socket
server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
server_socket.bind((HOST, PORT))
server_socket.listen(5)

# Global variables
sockets_list = [server_socket]
clients = {}
authenticated_clients = set()

# Ensure upload directory exists
if not os.path.exists(UPLOAD_DIR):
    os.makedirs(UPLOAD_DIR)

# Load credentials
def load_credentials(filename='id_passwd.txt'):
    credentials = {}
    try:
        with open(filename, 'r') as file:
            for line in file:
                username, password = line.strip().split(':')
                credentials[username] = password
    except FileNotFoundError:
        logging.error("Credential file not found.")
    return credentials

credentials = load_credentials()

# Signal handler to gracefully shut down the server
def signal_handler(sig, frame):
    logging.info("Server shutting down gracefully...")
    for client_socket in list(clients.keys()):
        try:
            client_socket.send(b'SERVER SHUTDOWN')
        except Exception as e:
            logging.error(f"Error notifying client about shutdown: {e}")
    server_socket.close()
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)

# Authentication function
def authenticate_client(client_socket):
    try:
        client_socket.send(b"AUTH REQUIRED. SEND 'USERNAME:PASSWORD'")
        auth_data = client_socket.recv(1024).decode('utf-8').strip()
        if ':' in auth_data:
            username, password = auth_data.split(':', 1)
            if username in credentials and credentials[username] == password:
                client_socket.send(b"AUTH SUCCESSFUL. SESSION STARTED.")
                return True, username
        client_socket.send(b"AUTH FAILED. CLOSING CONNECTION.")
    except Exception as e:
        logging.error(f"Authentication error: {e}")
    return False, None

# Error handling for file uploads
def receive_file_chunks(client_socket, username):
    user_dir = os.path.join(UPLOAD_DIR, username)
    os.makedirs(user_dir, exist_ok=True)
    client_socket.send(b"READY TO RECEIVE FILE. SEND 'FILENAME:<filename>'")
    
    try:
        file_info = client_socket.recv(1024).decode('utf-8').strip()
        if file_info.startswith("FILENAME:"):
            filename = os.path.basename(file_info.split(':', 1)[1])  # Prevent directory traversal
            file_path = os.path.join(user_dir, filename)
            client_socket.send(b"RECEIVING CHUNKS")
            with open(file_path, 'wb') as f:
                while True:
                    chunk = client_socket.recv(4096)
                    if chunk == b'EOF':
                        break
                    f.write(chunk)
                    client_socket.send(b"CHUNK RECEIVED")
            logging.info(f"File '{filename}' uploaded successfully by {username}")
            client_socket.send(f"UPLOAD SUCCESSFUL: {filename}".encode('utf-8'))
        else:
            raise ValueError("Invalid file information format.")
    except Exception as e:
        logging.error(f"Error receiving file from {username}: {e}")
        client_socket.send(b"UPLOAD FAILED")

# Error handling for file downloads
def download_file(client_socket, username):
    try:
        client_socket.send(b"SEND FILENAME TO DOWNLOAD")
        filename = os.path.basename(client_socket.recv(1024).decode('utf-8').strip())  # Prevent directory traversal
        file_path = os.path.join(UPLOAD_DIR, username, filename)
        
        if os.path.isfile(file_path):
            client_socket.send(b"FILE EXISTS. SENDING FILE...")
            with open(file_path, 'rb') as f:
                while chunk := f.read(4096):
                    client_socket.send(chunk)
            client_socket.send(b'EOF')
            logging.info(f"File '{filename}' sent to {username}")
        else:
            raise FileNotFoundError(f"File '{filename}' not found.")
    except Exception as e:
        logging.error(f"Error during download for {username}: {e}")
        client_socket.send(b"DOWNLOAD FAILED")

# Preview file content
def preview_file(client_socket, username):
    try:
        client_socket.send(b"SEND FILENAME TO PREVIEW")
        filename = os.path.basename(client_socket.recv(1024).decode('utf-8').strip())  # Prevent directory traversal
        file_path = os.path.join(UPLOAD_DIR, username, filename)
        
        if os.path.isfile(file_path):
            with open(file_path, 'rb') as f:
                preview_data = f.read(1024)
                client_socket.send(preview_data)
            client_socket.send(b'EOF')
        else:
            raise FileNotFoundError(f"File '{filename}' not found.")
    except Exception as e:
        logging.error(f"Error previewing file for {username}: {e}")
        client_socket.send(b"PREVIEW FAILED")

# File deletion
def delete_file(client_socket, username):
    try:
        client_socket.send(b"SEND FILENAME TO DELETE")
        filename = os.path.basename(client_socket.recv(1024).decode('utf-8').strip())  # Prevent directory traversal
        file_path = os.path.join(UPLOAD_DIR, username, filename)
        
        if os.path.isfile(file_path):
            os.remove(file_path)
            client_socket.send(f"FILE '{filename}' DELETED SUCCESSFULLY.".encode('utf-8'))
            logging.info(f"File '{filename}' deleted by {username}")
        else:
            raise FileNotFoundError(f"File '{filename}' not found.")
    except Exception as e:
        logging.error(f"Error deleting file for {username}: {e}")
        client_socket.send(b"DELETE FAILED")

# Directory listing
def list_directory(client_socket, username):
    try:
        user_dir = os.path.join(UPLOAD_DIR, username)
        if os.path.exists(user_dir):
            files = os.listdir(user_dir)
            file_list = "\n".join(files) if files else "NO FILES FOUND"
            client_socket.send(f"FILES:\n{file_list}".encode('utf-8'))
        else:
            raise FileNotFoundError(f"Directory for user '{username}' not found.")
    except Exception as e:
        logging.error(f"Error listing directory for {username}: {e}")
        client_socket.send(b"LIST DIRECTORY FAILED")

# Client handler
def handle_client(client_socket):
    authenticated, username = authenticate_client(client_socket)
    if authenticated:
        sockets_list.append(client_socket)
        clients[client_socket] = (client_socket.getpeername(), username)
        authenticated_clients.add(client_socket)
        logging.info(f"Authenticated client {username} from {client_socket.getpeername()}")
        
        try:
            while True:
                data = client_socket.recv(1024)
                if data:
                    command = data.decode('utf-8').strip()
                    if command == 'UPLOAD':
                        receive_file_chunks(client_socket, username)
                    elif command == 'DOWNLOAD':
                        download_file(client_socket, username)
                    elif command == 'PREVIEW':
                        preview_file(client_socket, username)
                    elif command == 'DELETE':
                        delete_file(client_socket, username)
                    elif command == 'LIST':
                        list_directory(client_socket, username)
                    else:
                        client_socket.send(b"INVALID COMMAND")
                        logging.warning(f"Invalid command received from {username}")
                else:
                    break
        except ConnectionResetError:
            logging.warning(f"Connection reset by client {username}")
        finally:
            sockets_list.remove(client_socket)
            authenticated_clients.discard(client_socket)
            del clients[client_socket]
            client_socket.close()
    else:
        client_socket.close()

# Server main loop
with ThreadPoolExecutor(max_workers=10) as executor:
    logging.info(f"Server running on {HOST}:{PORT}")
    while True:
        read_sockets, _, exception_sockets = select.select(sockets_list, [], sockets_list)
        for notified_socket in read_sockets:
            if notified_socket == server_socket:
                client_socket, client_address = server_socket.accept()
                logging.info(f"New connection from {client_address}")
                executor.submit(handle_client, client_socket)
        
        for notified_socket in exception_sockets:
            sockets_list.remove(notified_socket)
            if notified_socket in clients:
                authenticated_clients.discard(notified_socket)
                del clients[notified_socket]
