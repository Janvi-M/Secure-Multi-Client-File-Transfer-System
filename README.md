# EC-Team-67-distributed-file-orchestration-and-synchronization

# Distributed File Orchestration and Synchronization - Documentation

## Overview

This system enables secure and synchronized file operations between a client and server. The system allows clients to authenticate, upload, download, preview, delete, and list files on the server. The communication between the client and the server occurs over a TCP connection, utilizing a custom application-layer protocol.

---

## System Components

### 1. **Client**

**Purpose:**  
The client interacts with the server, sending commands and receiving file-related responses.

**Key Features:**
- **Authentication:** Clients authenticate using a username and password.
- **File Operations:** Clients can upload, download, preview, and delete files.
- **Directory Listing:** Clients can list files stored on the server.

### 2. **Server**

**Purpose:**  
The server processes the commands from clients and handles file operations securely while enforcing authentication and file access rules.

**Key Features:**
- **Authentication:** The server validates user credentials.
- **Multi-Threading:** Uses `ThreadPoolExecutor` to handle multiple clients concurrently.
- **File Isolation:** Ensures each user has a dedicated directory for file operations.
- **Logging and Error Handling:** Robust logging and error responses to clients.
- **Graceful Shutdown:** Allows the server to shut down cleanly, notifying connected clients.

---

## Protocol Specifications

### 1. **Authentication Protocol**

- **Request:** Client sends `USERNAME: PASSWORD` after receiving the server's prompt.
- **Server Response:**
  - `AUTH SUCCESSFUL. SESSION STARTED.`
  - `AUTH FAILED. CLOSING CONNECTION.`

### 2. **File Operation Commands**

Below is a summary of commands sent by the client and the expected server responses:

| **Command** | **Client Request** | **Server Response** |
|-------------|--------------------|---------------------|
| `UPLOAD`    | `UPLOAD`           | `READY TO RECEIVE FILE` |
| `DOWNLOAD`  | `DOWNLOAD`         | `SEND FILENAME TO DOWNLOAD` |
| `PREVIEW`   | `PREVIEW`          | `SEND FILENAME TO PREVIEW` |
| `DELETE`    | `DELETE`           | `SEND FILENAME TO DELETE` |
| `LIST`      | `LIST`             | Directory listing or `"NO FILES FOUND"` |

### 3. **File Transfer Protocol**

- Files are transferred in chunks of 4KB.
- The server sends an `EOF` (End-of-File) marker to signal the end of a file transfer.
- The server acknowledges each chunk with `CHUNK RECEIVED`.

---

## Key API References

### 1. **Python Standard Library**

The following Python standard libraries are used:
- **socket:** For TCP socket communication.
- **os:** For handling file and directory operations.
- **select:** To manage multiple concurrent client connections.
- **signal:** For handling server shutdown.
- **concurrent.futures:** For thread pool-based concurrency.
- **logging:** For logging server and client events.

---

## Security Considerations

### 1. **Authentication**
- User credentials are stored in `id_passwd.txt` in plain text. It is recommended to implement password hashing using libraries such as `bcrypt` or `hashlib`.

### 2. **Directory Isolation**
- Each user has a dedicated directory under `uploads/<username>` to ensure file isolation and prevent unauthorized access.

### 3. **Input Validation**
- File paths are validated to prevent directory traversal attacks.

### 4. **Encryption (Future Enhancement)**
- The system should implement SSL/TLS encryption using Python's `ssl` module for secure communication between the client and server.

---

## Error Handling

### 1. **Server-Side Errors**
- Server errors during file operations or invalid commands are logged, and meaningful error messages are sent to the client.

### 2. **Client-Side Errors**
- Clients receive error messages when sending invalid commands or file paths.

---

## Future Enhancements

### 1. **Encryption**
- Implement SSL/TLS encryption for secure client-server communication:
  python
  import ssl
  context = ssl.create_default_context(ssl.Purpose.CLIENT_AUTH)
  secure_socket = context.wrap_socket(server_socket, server_side=True)

## Future Enhancements

### 2. Persistent Storage
**Goal:**  
Replace the plain-text `id_passwd.txt` file with a database for securely storing user credentials.

**How to Implement:**
- Use a secure database like SQLite, MySQL, or PostgreSQL to store `username:password` pairs.
- Ensure passwords are stored using secure hashing and salting techniques (e.g., using `bcrypt` or `hashlib`).

---

### 3. Rate Limiting
**Goal:**  
Introduce throttling for file upload/download to prevent misuse and optimize server load.

**How to Implement:**
- Implement rate-limiting logic that restricts the number of uploads or downloads a user can perform within a specific time period.
- Use tools like `redis` or custom in-memory caching to track request rates and enforce limits.

---

### 4. Compression
**Goal:**  
Use compression (e.g., `gzip`) for file transfers to reduce bandwidth consumption.

**How to Implement:**
- Implement compression for files before transmission and decompression upon receipt.
- Integrate libraries like `gzip` to compress files during upload and download processes.

---

### 5. Log Aggregation
**Goal:**  
Integrate centralized logging systems (e.g., Elasticsearch and Kibana) for efficient monitoring and troubleshooting.

**How to Implement:**
- Set up an Elasticsearch cluster to store logs.
- Use Kibana to visualize logs and configure alerts for monitoring server performance or errors.
- Configure the server to push logs to a centralized logging system for better traceability.

---

## Deployment Instructions

### 1. Server

1. Place the `server.py` file on a machine with a fixed IP address.
2. Create and populate the `id_passwd.txt` file with `username:password` entries.
3. Run the server with the following command:
   ```bash
   python server.py

### 2. Client

1. Place the `client.py` file on the user's machine.
2. Run the client with the following command:
   ```bash
   python client.py

### Conclusion
This system provides a secure way to handle file operations between a client and server while ensuring data integrity, confidentiality, and efficient error handling. Future enhancements include encryption for secure communication and more advanced features like rate limiting and compression.
