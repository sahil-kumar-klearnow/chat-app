import socket
import threading
import datetime
import logging
import sys

# Configure basic logging
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

# Constants
HOST = '0.0.0.0'
PORT = 65432
BUFFER_SIZE = 4096

# Global lists of connected clients
clients_lock = threading.Lock()
# Mapping of socket connection -> username
clients = {}
# Chat history could be stored here if required for history feature
chat_history = []

def broadcast(message, sender_conn=None):
    """Broadcasts a message to all connected clients except the sender."""
    with clients_lock:
        for conn in list(clients.keys()):
            # If sender_conn is None, it's a server message broadcast to everyone.
            if conn != sender_conn:
                try:
                    conn.sendall(message.encode('utf-8'))
                except Exception as e:
                    logging.error(f"Error broadcasting to a client: {e}")
                    remove_client(conn)

def remove_client(conn):
    """Removes a client from the active list and closes their connection."""
    with clients_lock:
        if conn in clients:
            username = clients[conn]
            del clients[conn]
            conn.close()
            logging.info(f"Client disconnected: {username}")
            disconnect_msg = f"[Server] {username} has left the chat."
            # Call broadcast without lock to prevent deadlock
            threading.Thread(target=broadcast, args=(disconnect_msg,)).start()

def handle_client(conn, addr):
    """Handles an individual client connection."""
    logging.info(f"New connection from {addr}")
    username = None

    try:
        # Phase 1: Wait for JOIN
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            
            message = data.decode('utf-8').strip()
            if message.startswith("JOIN "):
                username = message.split(" ", 1)[1].strip()
                if not username:
                    conn.sendall("Error: Username cannot be empty.\n".encode('utf-8'))
                    continue
                
                with clients_lock:
                    if username in clients.values():
                        # Simple naive check. Better would be mapping username -> conn
                        pass # Allowed for simple application, but could reject duplicate usernames
                    clients[conn] = username
                
                logging.info(f"User joined: {username} ({addr})")
                
                # Send welcome message
                # Optional feature: Send chat history
                conn.sendall("Welcome to the Chat Server! Type /quit to exit.\n".encode('utf-8'))
                
                # Broadcast join
                join_msg = f"[Server] {username} has joined the chat."
                broadcast(join_msg, conn)
                break
            else:
                conn.sendall("Error: Must send JOIN <username> first.\n".encode('utf-8'))
        
        # Phase 2: Handle regular messages
        while True:
            data = conn.recv(BUFFER_SIZE)
            if not data:
                break
            
            message = data.decode('utf-8').strip()
            
            if message == "QUIT":
                logging.info(f"Received QUIT from {username}")
                break
            elif message == "LIST":
                with clients_lock:
                    user_list = ", ".join(clients.values())
                conn.sendall(f"[Server] Connected users: {user_list}\n".encode('utf-8'))
            elif message.startswith("MSG "):
                msg_text = message.split(" ", 1)[1] if len(message) > 4 else ""
                if msg_text:
                    timestamp = datetime.datetime.now().strftime('%H:%M:%S')
                    formatted_msg = f"[{timestamp}] {username}: {msg_text}"
                    logging.info(f"Message from {username}: {msg_text}")
                    broadcast(formatted_msg, conn)
            else:
                conn.sendall("Error: Unknown command. Use MSG <text>, LIST, or QUIT.\n".encode('utf-8'))
                
    except ConnectionResetError:
        pass
    except Exception as e:
        logging.error(f"Error handling client {addr}: {e}")
    finally:
        remove_client(conn)

def start_server():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    # Allow port reuse
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    
    try:
        server_socket.bind((HOST, PORT))
        server_socket.listen()
        logging.info(f"Server started on {HOST}:{PORT}. Listening for connections...")
        
        while True:
            # Accept new connections
            conn, addr = server_socket.accept()
            # Start a new thread to handle the client
            client_thread = threading.Thread(target=handle_client, args=(conn, addr))
            client_thread.daemon = True
            client_thread.start()
            
    except KeyboardInterrupt:
        logging.info("Server shutting down...")
    except Exception as e:
        logging.error(f"Server error: {e}")
    finally:
        server_socket.close()

if __name__ == "__main__":
    start_server()
