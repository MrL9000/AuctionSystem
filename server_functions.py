import socket
import threading
import time

# =========================
# Configuration
# =========================
HOST = "127.0.0.1"
PORT = 5000

AUCTION_DURATION = 20
MIN_INCREMENT = 50
EXPECTED_CLIENTS = 3

# =========================
# Log
# =========================
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


# =========================
# Global State
# =========================

items = [
    {"name": "Laptop", "base_price": 500},
    {"name": "Phone", "base_price": 300},
    {"name": "Tablet", "base_price": 400},
]
items_in_use = [
    {"current_winner": None, "current_name": "Laptop", "current_price": 500},
    {"current_winner": None, "current_name": "Phone", "current_price": 300},
    {"current_winner": None, "current_name": "Tablet", "current_price": 400},
]

# variables needed to keep the record of connected clients.
clients = []
client_names = []
client_files = []
client_active = []
passed_current_item = []

# synchronization objects needed by the server.
clients_lock = threading.Lock()
auction_lock = threading.Lock()
bid_event = threading.Event()
stop_event = threading.Event()

# TODO:
# Create the global variables needed for:
server_socket = None
Thread_accept_1 = None
Thread_accept_2 = None
Thread_accept_3 = None
Thread_auction = None
client_threads = [None, None, None]

auction_started = False
current_item_index = None
current_price = None
current_winner = None
current_winner_name = None
auction_active = None
auction_end_time = None


# =========================
# Utilities
# =========================
def safe_shutdown_close(sock):
    # TODO:
    # Close the socket correctly.
    #
    # Suggested syntax:
    try:
        sock.shutdown(socket.SHUT_RDWR)
    except:
        pass
    
    try:
        sock.close()
    except:
        pass
    pass


def send_message(sock, message):
    # TODO:
    # Send one complete line to a client socket.
    #
    # Suggested syntax:
    try:
        sock.sendall((message + "\n").encode("utf-8"))
        return True
    except:
        return False
    pass


def broadcast(message):
    global clients_lock
    global clients

    # TODO:
    # Send the same message to all active clients.
    #
    # General steps:
    # 1. Make a copy of the connected client list while protected by clients_lock.
    # 2. Iterate over that copy.
    # 3. For each active client, call send_message(sock, message).
    # 4. If sending fails, remove that client.
    with clients_lock:
        clients_copy = clients
    for sock in clients_copy:
        #log_message("tried to broadcast" + str(sock))
        try: send_message(sock, message)
        except: remove_client(sock)
    pass


def remove_client(sock):
    global clients_lock
    global clients
    global client_active
    global client_names
    global client_files
    # TODO:
    # Remove one client from the server record.
    #
    # General steps:
    # 1. Enter the critical section protected by clients_lock.
    # 2. Mark the client as inactive.
    # 3. Remove the socket from the client list.
    # 4. Remove its name, file object, and PASS flag from dictionaries.
    # 5. After leaving the critical section, close the file object if it exists.
    # 6. Close the socket with safe_shutdown_close(sock).
    with clients_lock:
        i = 0
        for sock_old in clients:
            if sock_old == sock:
                clients[i] = None
                client_active[i] = False
                client_names[i] = None
                #file = client_files
                client_files = False
                break
    #file.close()
    safe_shutdown_close(sock)
    pass


def close_all_clients():
    # TODO:
    # Close every connected client.
    #
    # Suggested logic:
    # 1. Make a copy of the client list.
    # 2. Iterate over the copy.
    # 3. Call remove_client(sock) for each one.
    for sock in clients:
        remove_client(sock)
    pass


def get_current_item():
    # TODO:
    # Return the current item from the item list.
    #
    # Suggested logic:
    # - If current_item_index is valid, return items[current_item_index]
    # - Otherwise return None
    if 0<= current_item_index <= 2:
      return items_in_use[current_item_index]
    else:
      return None
    pass


def reset_pass_flags():
    global passed_current_item
    # TODO:
    # Reset the PASS flag of all connected clients.
    #
    # Suggested logic:
    # - Enter clients_lock
    # - For every client in the client list:
    #       passed_current_item[sock] = False
    for item in passed_current_item:
        item = False
    pass


# =========================
# Command Processing
# =========================
def process_view(sock):
    send_message(sock, "VIEW")
    # TODO:
    # Answer the VIEW command.
    #
    # General logic:
    # 1. Enter auction_lock.
    # 2. Get the current item.
    # 3. If there are no more items, send NO_MORE_ITEMS.
    # 4. If the auction is active, send:
    #       item name, current price, and current leader
    # 5. Otherwise send VIEW NO_ACTIVE_AUCTION.
    with clients_lock:
        i = 0
        for sock_old in clients:
            if not auction_active:
                send_message(sock, "NO_ACTIVE_AUCTION")
            elif sock_old == sock:
                if (get_current_item() != None):
                    send_message(sock, str(get_current_item()['current_name']) + ", " + str(get_current_item()['current_price']) + ", " + str(get_current_item()['current_winner']))
                else:
                    send_message(sock, "NO_MORE_ITEMS")
    pass


def process_pass(sock):
    send_message(sock, "PASS")
    global client_active
    # TODO:
    # Process the PASS command.
    #
    # General logic:
    # 1. Enter clients_lock.
    # 2. Mark passed_current_item[sock] = True.
    # 3. Get the client name.
    # 4. Send OK PASS to that client.
    # 5. Broadcast that this client passed.
    with clients_lock:
      i = 0
      for sock_old in clients:
          if sock_old == sock:
              passed_current_item[i] = True
    pass


def process_bid(sock, parts):
    send_message(sock, "BID")
    # TODO:
    # Remember:
    # if this function modifies global variables,
    # use the Python keyword global.
    #
    # General logic:
    # 1. Verify that the command has exactly two parts:
    #       BID <amount>
    # 2. Convert parts[1] to an integer.
    # 3. Get the bidder name from the client record.
    # 4. Enter auction_lock.
    # 5. Verify that an auction is active.
    # 6. Compute the minimum valid bid:
    #       min_valid = current_price + MIN_INCREMENT
    # 7. If amount is too low, reject it.
    # 8. If valid:
    #       update current_price
    #       update current_winner
    #       update current_winner_name
    #       restart auction_end_time using time.time() + AUCTION_DURATION
    # 9. Reset this client's PASS flag.
    # 10. Send OK BID_ACCEPTED.
    # 11. Broadcast NEW_BID.
    # 12. Notify the timer thread with bid_event.set().
    pass


def process_exit(sock):
    send_message(sock, "EXIT")
    # TODO:
    # Process EXIT.
    #
    # General logic:
    # 1. Send OK EXIT.
    # 2. Remove the client with remove_client(sock).
    
    send_message("OK EXIT")
    remove_client(sock)
    pass


# =========================
# Threads
# =========================
def handle_client(sock, addr):
    global clients_lock
    global clients
    global client_active
    global client_files
    global client_names
    try:
        # This wrapper allows reading complete lines from the socket.
        file_obj = sock.makefile("r", encoding="utf-8")

        # Ask the client for its name.
        send_message(sock, "[SERVER] ENTER_NAME")

        # TODO:
        # Read the first line from file_obj as the client name.
        #
        # Suggested syntax:
        name = file_obj.readline()
        if not name:
            remove_client(sock)
            return
        name = name.strip()
        if name == "":
            remove_client(sock)
            return
        # TODO:
        # Save the client information in the server record.
        #
        # General logic:
        # - enter clients_lock
        # - store the client name
        # - store file_obj
        # - mark the client as active
        # - initialize its PASS flag as False
        with clients_lock:
            clients.append(sock)
            client_names.append(name)
            client_files.append(file_obj)
            client_active.append(True)
            passed_current_item.append(False)
        send_message(sock, f"[SERVER] HELLO NAME={name}")
        log_message(f"[SERVER] CLIENT_REGISTERED NAME={name} ADDR={addr}")
        while not stop_event.is_set():
            # Read one command line from file_obj.
            line = file_obj.readline()

            if not line:
                break

            message = line.strip()

            if message == "":
                continue

            # Split the command into words.
            parts = message.split()
            command = parts[0].upper()

            # TODO:
            # Process the command:
            log_message(command)
            if command == "VIEW": process_view(sock)
            elif command == "BID": process_bid(sock, parts)
            elif command == "PASS": process_pass(sock)
            elif command == "EXIT":
              process_exit(sock)
              return None
            else: send_message(sock, "ERROR INVALID_COMMAND")

    except Exception as e:
      log_message(e)
      pass
    remove_client(sock)


def accept_clients_loop(i):
    # TODO:
    # If this function modifies global variables,
    # remember to declare them with global.
    #
    # General logic:
    # 1. Print that the server is listening.
    log_message("SERVER " + str(i) + " IS LISTENING")
    # 2. While the server is accepting clients:
    #       accept a new connection
    #       accept() returns:
    #           sock  -> client socket
    #           addr  -> client address
    # 3. If the auction has already started, reject the client.
    # 4. Otherwise, add the client socket to the client list.
    # 5. Create one thread for handle_client(sock, addr).
    # 6. Start the thread and save it in client_threads.
    # 7. When the number of connected clients reaches EXPECTED_CLIENTS,
    #    stop accepting more clients.
    #
    # Suggested socket syntax:
    with clients_lock:
      sock, addr = server_socket.accept()
    client_threads[i] = threading.Thread(target= handle_client, args = (sock, addr))
    client_threads[i].start()
    pass


def auction_loop():
    # TODO:
    # If this function modifies global variables,
    # remember to declare them with global.
    #
    global auction_active
    global auction_end_time
    global items_in_use
    global current_item_index
    # General logic:
    # 1. Mark that the auction phase has started.
    # 2. Iterate through all items in the item list.
    # 3. For each item:
    #       - set current_price to the base price
    #       - clear the winner
    #       - mark auction_active = True
    #       - compute auction_end_time = time.time() + AUCTION_DURATION
    #       - reset PASS flags
    #       - clear bid_event
    #       - broadcast AUCTION_START
    bid_event.clear()
    i = 0
    for item in items_in_use:
        item['current_price'] = items[i]['base_price']
        item['current_winner'] = None
        i+=1
    reset_pass_flags()
    auction_active = True
    current_item_index = 0
    for item in items_in_use:
      log_message("AUCTION_START ITEM= " + item['current_name'])
      auction_end_time = time.time() + AUCTION_DURATION
      #
      # 4. While the auction is active:
      #       - compute remaining = int(auction_end_time - time.time())
      #       - if remaining <= 0, finish this auction
      #       - optionally send TIME_LEFT
      #       - wait for new bids with:
      #             bid_event.wait(timeout=0.5)
      #       - if the event was set, clear it with bid_event.clear()
      remaining = int(auction_end_time - time.time())
      while (remaining > 0):
          broadcast("TIME_LEFT " + str(remaining))
          bid_event.wait(timeout=0.5)
          bid_event.clear()
          remaining = int(auction_end_time - time.time())
      #
      # 5. When the timer finishes:
      #       - mark auction_active = False
      #       - if there is a winner, send AUCTION_END with winner and price
      #       - otherwise send AUCTION_END with WINNER=None
      #
      auction_active = False
      for item in items_in_use:
          if item['current_winner'] != None:
              broadcast("AUCTION_END, WINNER IS " + item['current_winner'] + " AND PRICE IS " + str(item['current_price']))
          else:
              broadcast("AUCTION_END, WINNER=None")
      current_item_index += 1
      reset_pass_flags()
            
    # 6. After all items:
    #       - broadcast SERVER_SHUTDOWN
    #       - set stop_event
    broadcast("SERVER_SHUTDOWN")
    stop_event.set()
    pass


# =========================
# Start / Shutdown
# =========================
def start_server():
    # If this function modifies global variables,
    # remember to declare them with global.
    #
    global server_socket
    global Thread_accept_1
    global Thread_accept_2
    global Thread_accept_3
    # General logic:
    # 1. Create the server socket.
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    #
    # 2. Allow fast reuse of the port.
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    #
    # 3. Bind the socket to the server address.
    server_socket.bind((HOST, PORT))
    #
    # 4. Start listening for connections.
    server_socket.listen(EXPECTED_CLIENTS)
    # *5. Create and start the thread that accepts clients.
    Thread_accept_1 = threading.Thread(target= accept_clients_loop, args = ([0]))
    Thread_accept_1.start()
    Thread_accept_2 = threading.Thread(target= accept_clients_loop, args = ([1]))
    Thread_accept_2.start()
    Thread_accept_3 = threading.Thread(target= accept_clients_loop, args = ([2]))
    Thread_accept_3.start()
    # *6. Wait until all expected clients are connected and
    #
    # *10. Wait for the accept threads.
    Thread_accept_1.join()
    Thread_accept_2.join()
    Thread_accept_3.join()
    # 7. Create and start the auction thread.
    Thread_auction = threading.Thread(target= auction_loop, args = ([]))
    Thread_auction.start()
    # 8. Wait for the auction thread to finish.
    Thread_auction.join()
    # 9. Close the server socket.
    server_socket.close()
    # 11. Close all client sockets.
    close_all_clients()    # 12. Wait for all client threads.
    client_threads[0].join()
    client_threads[1].join()
    client_threads[2].join()
    # 13. Print SERVER_CLOSED.
    log_message("SERVER_CLOSED")
    pass