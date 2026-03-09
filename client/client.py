import socket
import threading
import sys

# Configure standard constants
HOST = '127.0.0.1'
PORT = 65432
BUFFER_SIZE = 4096

def receive_messages(sock):
    """Listens for incoming messages from the server."""
    while True:
        try:
            message = sock.recv(BUFFER_SIZE).decode('utf-8')
            if not message:
                # Server disconnected
                print("\n[Disconnected from server]")
                break
            
            # Print the received message and show prompt again
            # Using \r to clear the current line
            print("\r" + message)
            print("> ", end="", flush=True)
            
        except Exception as e:
            # An error occurred (e.g. socket closed)
            print(f"\n[Error receiving message: {e}]")
            break

def start_client():
    client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        client_socket.connect((HOST, PORT))
        print(f"Connected to {HOST}:{PORT}")
    except Exception as e:
        print(f"Unable to connect to server: {e}")
        sys.exit(1)

    try:
        username = input("Enter your username: ").strip()
        while not username:
            print("Username cannot be empty.")
            username = input("Enter your username: ").strip()
            
        join_msg = f"JOIN {username}"
        client_socket.sendall(join_msg.encode('utf-8'))
        
        # Start the receive thread
        receive_thread = threading.Thread(target=receive_messages, args=(client_socket,))
        receive_thread.daemon = True
        receive_thread.start()
        
        # Start reading user input
        while True:
            # We use a simple prompt symbol 
            user_input = input("> ").strip()
            
            if user_input.lower() == '/quit':
                client_socket.sendall("QUIT".encode('utf-8'))
                break
            elif user_input.lower() == '/list':
                client_socket.sendall("LIST".encode('utf-8'))
            elif user_input:
                msg = f"MSG {user_input}"
                client_socket.sendall(msg.encode('utf-8'))
                
    except KeyboardInterrupt:
        print("\nExiting chat...")
        try:
            client_socket.sendall("QUIT".encode('utf-8'))
        except:
            pass
    except Exception as e:
        print(f"Error: {e}")
    finally:
        client_socket.close()

if __name__ == "__main__":
    start_client()
