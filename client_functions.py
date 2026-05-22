import socket
import threading
import sys

HOST = "127.0.0.1"
PORT = 5000

stop_event = threading.Event()

LOG_FILE = None


def open_log_file(filename):
    global LOG_FILE
    LOG_FILE = open(filename, "w", encoding="utf-8")


def close_log_file():
    global LOG_FILE
    if LOG_FILE is not None:
        LOG_FILE.close()
        LOG_FILE = None


def log_message(message):
    print(message, flush=True)
    if LOG_FILE is not None:
        LOG_FILE.write(message + "\n")
        LOG_FILE.flush()


def safe_shutdown_close(sock):
    # it closes the socket correctly
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except:
        pass

    try:
        sock.close()
    except:
        pass


def receive_messages(sock):
    try:
        # This creates a text wrapper around the socket,
        # so messages can be read one line at a time
        file_obj = sock.makefile("r", encoding="utf-8")

        while not stop_event.is_set():
            # Read one full line from the server.
            line = file_obj.readline()

            # If the socket is closed, readline() returns an empty string
            if not line:
                break

            # it removes spaces and newline characters
            message = line.strip()

            if message == "":
                continue

            # Shows the message in console and save it in the log
            log_message(message)

            # If the server sends SERVER_SHUTDOWN,
            # it stops the client by setting stop_event
            if message == "SERVER_SHUTDOWN":
                stop_event.set()
                break

        file_obj.close()

    except:
        pass

    stop_event.set()


def send_commands(sock):
    try:
        while not stop_event.is_set():
            # it reads one line written by the user in the console
            line = sys.stdin.readline()

            if not line:
                break

            command = line.strip()

            if command == "":
                continue

            # Sendw the command as a full line to the server
            sock.sendall((command + "\n").encode("utf-8"))

            # If the user typed EXIT, it stops this loop
            if command.upper() == "EXIT":
                stop_event.set()
                break

    except:
        pass

    stop_event.set()


def start_client():
    stop_event.clear()

    # Creates the client socket
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

    # Connects the socket to the server
    sock.connect((HOST, PORT))

    # Create one thread for receive_messages(sock)
    # and one thread for send_commands(sock).
    recv_thread = threading.Thread(target=receive_messages, args=(sock,))
    send_thread = threading.Thread(target=send_commands, args=(sock,))

    # Starts both threads
    recv_thread.start()
    send_thread.start()

    # Waits for the sending thread to finish first
    send_thread.join()

    # Waits for the receiving thread.
    # A timeout can be used to avoid waiting forever
    recv_thread.join(timeout=10)

    # When both threads are done, closes the socket.
    stop_event.set()
    safe_shutdown_close(sock)

    recv_thread.join(timeout=2)
