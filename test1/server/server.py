import threading
import time
import json
import socket
import random

players_lock = threading.Lock() 
players = {}
connections = {}
disconnected_players = {}

buffer = ""

updates = {}
def handle_client(connection, address):
    global buffer
    global updates
    player_id = None 
    try:
        player_id = int(connection.recv(1024).decode("utf-8"))
        print(f"[NEW CONNECTION] {address} connected with player ID: {player_id}")

        if player_id in disconnected_players:
            players[player_id] = disconnected_players[player_id]
            del disconnected_players[player_id]
        else:
            color = (
                random.randint(0, 255),
                random.randint(0, 255),
                random.randint(0, 255),
            )
            randomX = random.randint(0, 476)
            randomY = random.randint(0, 476)
            players[player_id] = {"x": randomX, "y": randomY, "id": player_id, "color": color}
            data = {"CONNECTED":player_id, "x": randomX, "y": randomY, "color": color}
            updates = data

        connections[player_id] = connection

        while True:
            data = connection.recv(1024).decode("utf-8")
            buffer += data
            while "\n" in buffer:
                msg, buffer = buffer.split("\n", 1) 
                try:
                    data = json.loads(msg)
                    new_x = players[player_id]["x"]
                    new_y = players[player_id]["y"]

              
                    if data["input"] == "w":
                        new_y -= 1
                    elif data["input"] == "s":
                        new_y += 1
                    elif data["input"] == "a":
                        new_x -= 1
                    elif data["input"] == "d":
                        new_x += 1

                    
                    if (
                        0 <= new_x < 476 and 0 <= new_y < 476
                    ): 
                        updates[player_id] = {"x": new_x, "y": new_y}
                        players[player_id]["x"] = new_x
                        players[player_id]["y"] = new_y
                except json.JSONDecodeError:
                    print(f"[ERROR] Malformed JSON from client {address}")
                    continue  
    except Exception as e:
        print(f"[ERROR] There was an error with client {address}: {e}")
        if player_id is not None and player_id in players:
            disconnected_players[player_id] = players[player_id]
            del players[player_id]
            del connections[player_id]
        connection.close()


def broadcast():
    global updates
    while True:
        try:
            msg = json.dumps(updates) + "\n"
            with players_lock:
                for player_id, conn in list(connections.items()):
                    try:
                        conn.sendall(msg.encode("utf-8"))
                    except (ConnectionResetError, BrokenPipeError):
                        print(f"[ERROR] Connection with player {player_id} was lost.")
                        if player_id in players:
                            disconnected_players[player_id] = players[player_id]
                            del players[player_id]
                        del connections[player_id]
                        msg = f"DISCONNECTED:{player_id}\n"
                        for conn in connections.values():
                            conn.sendall(msg.encode("utf-8"))
                        conn.close()
            updates = {} 
        except Exception as e:
            print(f"[ERROR] There was an error during broadcasting: {e}")
        time.sleep(0.01)


def start():
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(("0.0.0.0", 5665)) 
    server.listen()
    print("[STARTED] Server is starting...")

    broadcast_thread = threading.Thread(target=broadcast)
    broadcast_thread.start()

    while True:
        conn, addr = server.accept()
        client_thread = threading.Thread(target=handle_client, args=(conn, addr))
        client_thread.start()


if __name__ == "__main__":
    start()
