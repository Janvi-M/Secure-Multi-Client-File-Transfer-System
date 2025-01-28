import socket
import os
import signal
import sys

# Define client settings
HOST = '127.0.0.1'
PORT = 12345

# Create a TCP/IP socket
client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
client_socket.connect((HOST, PORT))

# Signal handler for graceful shutdown
def signal_handler(sig, frame):
    print("\nClient is shutting down gracefully...")
    client_socket.close()
    sys.exit(0)

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)

def authenticate():
    response = client_socket.recv(1024).decode('utf-8')
    print("Server:", response)

    username = input("Enter your username: ")
    password = input("Enter your password: ")

    auth_data = f"{username}:{password}"
    client_socket.send(auth_data.encode('utf-8'))

    auth_response = client_socket.recv(1024).decode('utf-8')
    print("Server:", auth_response)
    return auth_response

def handle_upload(response):
    if "READY TO RECEIVE FILE" in response:
        filepath = input("Enter the path of the file to upload: ")
        if os.path.isfile(filepath):
            filename = os.path.basename(filepath)

            client_socket.send(f"FILENAME:{filename}".encode('utf-8'))
            response = client_socket.recv(1024).decode('utf-8')
            print("Server:", response)

            if "RECEIVING CHUNKS" in response:
                with open(filepath, 'rb') as f:
                    while chunk := f.read(4096):
                        client_socket.send(chunk)
                        ack = client_socket.recv(1024).decode('utf-8')
                        if ack != "CHUNK RECEIVED":
                            print("Error in chunk transfer. Retrying...")
                            client_socket.send(chunk)

                client_socket.send(b'EOF')  # Send end-of-file indicator
                final_response = client_socket.recv(1024).decode('utf-8')
                print("Server:", final_response)
        else:
            print("File does not exist.")

def handle_download(response):
    if "SEND FILENAME TO DOWNLOAD" in response:
        filename = input("Enter the filename to download: ")
        client_socket.send(filename.encode('utf-8'))
        response = client_socket.recv(1024).decode('utf-8')
        print("Server:", response)

        if "FILE EXISTS. SENDING FILE..." in response:
            with open(filename, 'wb') as f:
                while True:
                    chunk = client_socket.recv(4096)
                    if chunk == b'EOF':  # End-of-file indicator
                        print("End of file reached.")
                        break
                    elif not chunk:  # Check for empty chunk indicating end
                        print("No more data from server, closing...")
                        break
                    f.write(chunk)
            print(f"File '{filename}' downloaded successfully.")
        else:
            print("Download failed.")

def handle_preview(response):
    if "SEND FILENAME TO PREVIEW" in response:
        filename = input("Enter the filename to preview: ")
        client_socket.send(filename.encode('utf-8'))
        
        preview_data = b""
        while True:
            chunk = client_socket.recv(1024)
            if chunk == b'EOF':
                break  # Stop receiving if EOF marker is found
            elif chunk == b'FILE NOT FOUND':
                print("Server:", chunk.decode('utf-8'))
                preview_data = b""  # Clear any preview data received
                break
            else:
                preview_data += chunk

        if preview_data:
            print("Preview data (first 1024 bytes):", preview_data.decode('utf-8', errors='ignore'))

def handle_delete(response):
    if "SEND FILENAME TO DELETE" in response:
        filename = input("Enter the filename to delete: ")
        client_socket.send(filename.encode('utf-8'))
        delete_response = client_socket.recv(1024).decode('utf-8')
        print("Server:", delete_response)

def handle_list():
    print("Requesting directory listing from the server...")
    directory_listing = b""
    while True:
        chunk = client_socket.recv(4096)
        if chunk == b'EOF':
            break
        directory_listing += chunk
    print("Directory contents:\n", directory_listing.decode('utf-8'))

def main():
    auth_response = authenticate()

    if "SUCCESSFUL" in auth_response:
        while True:
            command = input("Enter command ('UPLOAD', 'DOWNLOAD', 'PREVIEW', 'DELETE', 'LIST', 'exit' to quit): ")

            if command.lower() == 'exit':
                break

            client_socket.send(command.encode('utf-8'))

            try:
                # Check if the server has sent any messages
                client_socket.settimeout(1)  # Set a timeout for the receive operation
                response = client_socket.recv(1024).decode('utf-8')

                if "SERVER SHUTDOWN" in response:
                    print("Server is shutting down. Exiting client.")
                    break

                print("Server:", response)

                if command.upper() == 'UPLOAD':
                    handle_upload(response)
                elif command.upper() == 'DOWNLOAD':
                    handle_download(response)
                elif command.upper() == 'PREVIEW':
                    handle_preview(response)
                elif command.upper() == 'DELETE':
                    handle_delete(response)
                elif command.upper() == 'LIST':
                    handle_list()
                else:
                    print("Invalid command.")

            except socket.timeout:
                # No message received; continue to the next command input
                continue
            except Exception as e:
                print(f"An error occurred: {e}")
                break

    # Close the connection
    client_socket.close()
    print("Client disconnected.")

# Run the client application
if __name__ == "__main__":
    main()
