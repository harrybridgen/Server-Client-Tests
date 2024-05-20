import threading
import selectors
import socket
import types
import json
import time
import random
import math

selector = selectors.DefaultSelector()

connections = {}
players = {}
updates = ""

def connect_client(sock):
    global updates
    randomX = random.randint(0, 600)
    randomY = random.randint(0, 600)
    conn, addr = sock.accept()
    print(f"[CONNECTED] {addr} connected to the server.")
    conn.setblocking(False)
    data = types.SimpleNamespace(addr=addr, inb=b'', outb=b'')
    events = selectors.EVENT_READ | selectors.EVENT_WRITE
    selector.register(conn, events, data=data)
    connections[addr] = conn
    players[addr] = {"x": randomX, "y": randomY, 
        "keys": {"W": False, "A": False, "S": False, "D": False}
    }
    send_current_players(conn)
    updates += f"PLAYER: {addr[0]}:{addr[1]}:{randomX}:{randomY}\n"

def send_current_players(conn):
    global players
    for player in players:
        conn.sendall(f"PLAYER: {player[0]}:{player[1]}:{players[player]['x']}:{players[player]['y']}".encode("utf-8") + b"\n")

def disconnect_client(client, data):
    global players
    global updates
    print(f"[DISCONNECT] {data.addr} disconnected from the server.")
    updates += f"DISCONNECT: {data.addr[0]}:{data.addr[1]}\n"
    players.pop(data.addr)
    selector.unregister(client)
    client.close()
    del connections[data.addr]

def receive_client(key, mask):
    client = key.fileobj
    data = key.data
    global updates

    try:
        if mask & selectors.EVENT_READ:
            recv_data = client.recv(1024)
            if recv_data:
                data.inb += recv_data
                if b"\n" in data.inb:
                    messages = data.inb.split(b"\n")
                    for msg in messages[:-1]: 
                        message = msg.decode("utf-8").strip()

                        if message == "DISCONNECT":
                            disconnect_client(client, data)
                            return
                        
                        elif message.startswith("MESSAGE: "):
                            message = message[9:] 
                            updates += f"MESSAGE: {data.addr}: {message}\n"
                            print(f"[MESSAGE] {data.addr}: {message}")

                        elif message.startswith("KEYDOWN:"):
                            key_pressed = message.split(":")[1]
                            players[data.addr]["keys"][key_pressed] = True

                        elif message.startswith("KEYUP:"):
                            key_released = message.split(":")[1]
                            players[data.addr]["keys"][key_released] = False
                        
                        if not message:
                            continue

                        else:
                            print(f"[DEBUG] Received from client {data.addr}: {message}")
                    data.inb = messages[-1]

        if mask & selectors.EVENT_WRITE and data.outb:
            sent = client.send(data.outb)
            data.outb = data.outb[sent:]

    except ConnectionResetError:
        disconnect_client(client, data)

def update_player_positions():
    global players, updates
    map_bounds = {"x_min": 0, "y_min": 0, "x_max": 600, "y_max": 600}
    player_width = 20 
    player_height = 20 

    for addr, player in players.items():
        update = False
        move_x = 0
        move_y = 0

        if player["keys"]["W"]:
            move_y -= 10
            update = True
        if player["keys"]["S"]:
            move_y += 10
            update = True
        if player["keys"]["A"]:
            move_x -= 10
            update = True
        if player["keys"]["D"]:
            move_x += 10
            update = True

        if move_x != 0 and move_y != 0:
            move_x /= math.sqrt(2)
            move_y /= math.sqrt(2)

        new_x = player["x"] + int(move_x)
        new_y = player["y"] + int(move_y)

        max_x_bound = map_bounds["x_max"] - player_width
        max_y_bound = map_bounds["y_max"] - player_height

        new_x = max(map_bounds["x_min"], min(new_x, max_x_bound))
        new_y = max(map_bounds["y_min"], min(new_y, max_y_bound))

        player["x"] = new_x
        player["y"] = new_y

        if update:
            updates += f"PLAYER: {addr[0]}:{addr[1]}:{player['x']}:{player['y']}\n"

def broadcast():
    global updates
    while True:
        update_player_positions()
        if updates:
            for conn in connections.values():
                addr = conn.getpeername()
                print(f"[DEBUG] Sending to {addr} client: {updates}")
                conn.sendall(updates.encode("utf-8") + b"\n")
            updates = ""
        time.sleep(0.1)

def start_server():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5665))
    server.listen()
    print("[STARTED] Server is starting...")
    server.setblocking(False)
    selector.register(server, selectors.EVENT_READ, data=None)
    server.setsockopt(socket.IPPROTO_TCP, socket.TCP_NODELAY, 1)

    broadcast_thread = threading.Thread(target=broadcast)
    broadcast_thread.start()

    while True:
        events = selector.select(timeout=None)
        for key, mask in events:
            if key.data is None:
                connect_client(key.fileobj)
            else:
                receive_client(key, mask)

if __name__ == "__main__":
    start_server()
