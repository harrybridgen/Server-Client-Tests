import threading
import socket
import json
import time
import random
import math

server_address = ("0.0.0.0", 5665)
server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server_socket.bind(server_address)

connections = {}
players = {}
updates = ""

def connect_client(addr):
    global updates
    randomX = random.randint(0, 600)
    randomY = random.randint(0, 600)
    print(f"[CONNECTED] {addr} connected to the server.")
    connections[addr] = addr
    players[addr] = {
        "x": randomX, 
        "y": randomY,
        "keys": {"W": False, "A": False, "S": False, "D": False},
        "dx": 0, 
        "dy": 0
    }
    send_current_players(addr)
    updates += f"PLAYER: {addr[0]}:{addr[1]}:{randomX}:{randomY}:0:0\n"

def send_current_players(addr):
    global players
    for player in players:
        message = f"PLAYER: {player[0]}:{player[1]}:{players[player]['x']}:{players[player]['y']}:{players[player]['dx']}:{players[player]['dy']}"
        server_socket.sendto(message.encode("utf-8") + b"\n", addr)

def disconnect_client(addr):
    global players
    global updates
    print(f"[DISCONNECT] {addr} disconnected from the server.")
    updates += f"DISCONNECT: {addr[0]}:{addr[1]}\n"
    players.pop(addr)
    del connections[addr]

def receive_client():
    global updates
    while True:
        data, addr = server_socket.recvfrom(1024)
        message = data.decode("utf-8").strip()
        if message == "CONNECT":
            if addr not in connections:
                connect_client(addr)
            return

        if message == "DISCONNECT":
            if addr in connections:
                disconnect_client(addr)
            return

        elif message.startswith("MESSAGE: "):
            message = message[9:]
            updates += f"MESSAGE: {addr}: {message}\n"
            print(f"[MESSAGE] {addr}: {message}")

        elif message.startswith("KEYDOWN:") or message.startswith("KEYUP:"):
            key_action, key = message.split(":")
            if key_action == "KEYDOWN":
                players[addr]["keys"][key] = True
            else:
                players[addr]["keys"][key] = False
            update_player_direction(addr)

        if not message:
            continue

        else:
            print(f"[DEBUG] Received from client {addr}: {message}")

def update_player_direction(addr):
    global players
    global updates

    player = players[addr]
    old_dx, old_dy = player["dx"], player["dy"]

    move_x = 0
    move_y = 0

    if player["keys"]["W"]:
        move_y -= 20
    if player["keys"]["S"]:
        move_y += 20
    if player["keys"]["A"]:
        move_x -= 20
    if player["keys"]["D"]:
        move_x += 20

    if move_x != 0 and move_y != 0:
        move_x /= math.sqrt(2)
        move_y /= math.sqrt(2)

    player["dx"] = int(round(move_x))
    player["dy"] = int(round(move_y))

    if (move_x, move_y) != (old_dx, old_dy):
        updates += f"PLAYER: {addr[0]}:{addr[1]}:{player['x']}:{player['y']}:{player['dx']}:{player['dy']}\n"

def update_player_positions():
    global players
    map_bounds = {"x_min": 0, "y_min": 0, "x_max": 600, "y_max": 600}
    player_width = 20
    player_height = 20

    for addr, player in players.items():
        move_x = player["dx"]
        move_y = player["dy"]

        new_x = player["x"] + int(move_x)
        new_y = player["y"] + int(move_y)

        max_x_bound = map_bounds["x_max"] - player_width
        max_y_bound = map_bounds["y_max"] - player_height

        new_x = max(map_bounds["x_min"], min(new_x, max_x_bound))
        new_y = max(map_bounds["y_min"], min(new_y, max_y_bound))

        player["x"] = new_x
        player["y"] = new_y

def broadcast():
    global updates
    while True:
        update_player_positions()
        if updates:
            for addr in connections.values():
                print(f"[DEBUG] Sending to {addr} client: {updates}")
                server_socket.sendto(updates.encode("utf-8") + b"\n", addr)
            updates = ""
        time.sleep(0.1)

def start_server():
    print("[STARTED] Server is starting...")

    broadcast_thread = threading.Thread(target=broadcast)
    broadcast_thread.start()

    while True:
        receive_client()

if __name__ == "__main__":
    start_server()
