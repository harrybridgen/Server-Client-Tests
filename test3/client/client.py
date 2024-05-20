import pygame
import socket
import threading
import sys
import time
import random

pygame.init()
finished = False

window_size = (600, 600)
screen = pygame.display.set_mode(window_size)
pygame.display.set_caption("Client")

BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

font = pygame.font.Font(None, 32)

input_box = pygame.Rect(100, window_size[1] - 40, 400, 32)
text = ''
is_typing = False

players = {}

shutdown_event = threading.Event()

server_address = ("localhost", 5665)
client_address = ("", 0)

def receive_thread():
    global finished
    while not finished:
        try:
            data, _ = client.recvfrom(1024)
            data = data.decode("utf-8")
            messages = data.split("\n")
            print(f"[DEBUG] Received from server: {messages}")

            for msg in messages[:-1]:
                if msg.startswith("PLAYER: "):
                    msg = msg[8:]
                    ip, port, new_x, new_y, dx, dy = msg.split(":")
                    key = (ip, int(port))

                    if key not in players:
                        players[key] = {
                            "x": int(new_x),
                            "y": int(new_y),
                            "dx": int(dx),
                            "dy": int(dy),
                            "last_update": time.time(),
                            "messages": []
                        }
                    else:
                        player = players[key]
                        player["x"] = int(new_x)
                        player["y"] = int(new_y)
                        player["dx"] = int(dx)
                        player["dy"] = int(dy)
                        player["last_update"] = time.time()

                elif msg.startswith("MESSAGE: "):
                    _, sender_info, message = msg.split(": ", 2)
                    ip, port = sender_info[1:-1].split(", ")
                    addr = (ip.strip("'"), int(port))
                    if addr in players:
                        if 'messages' in players[addr] and len(players[addr]['messages']) > 0:
                            players[addr]['messages'].pop(0)
                        players[addr]['messages'].append((message, time.time()))

                elif msg.startswith("DISCONNECT: "):
                    msg = msg[12:]
                    msg = msg.split(":")
                    players.pop((msg[0], int(msg[1])))
                    print(f"[DEBUG] Players: {players}")

                if not msg:
                    continue

        except Exception as e:
            print(f"[ERROR] There was an error receiving data: {e}")
            continue

def broadcast(message):
    try:
        client.sendto(message.encode("utf-8") + b"\n", server_address)
        print(f"[DEBUG] Sent to server: {message}")
    except Exception as e:
        print(f"[ERROR] There was an error sending data: {e}")

def disconnect():
    try:
        print("[INFO] Disconnecting from the server...")
        broadcast("DISCONNECT")
    except Exception as e:
        print(f"[ERROR] There was an error while disconnecting: {e}")

def render_thread():
    global players
    while not finished:
        clock = pygame.time.Clock()
        clock.tick(144)
        screen.fill(WHITE)

        current_time = time.time()

        for addr, player in players.items():
            elapsed_time = (current_time - player["last_update"]) * 10
            x = round(player["x"] + player["dx"] * elapsed_time)
            y = round(player["y"] + player["dy"] * elapsed_time)

            pygame.draw.rect(screen, BLACK, pygame.Rect(x, y, 20, 20))

            for message, msg_time in player['messages']:
                if current_time - msg_time < 4:
                    msg_surface = font.render(message, True, BLACK)
                    screen.blit(msg_surface, (x, y - 20))
                else:
                    player['messages'].remove((message, msg_time))

        color = BLACK if is_typing else (200, 200, 200)
        pygame.draw.rect(screen, color, input_box, 2)
        txt_surface = font.render(text, True, color)
        screen.blit(txt_surface, (input_box.x+5, input_box.y+5))
        pygame.display.flip()

if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    client.bind(client_address) 
    print(f"[INFO] Client bound to address: {client.getsockname()}")
    broadcast("CONNECT")

    receive_thread = threading.Thread(target=receive_thread)
    receive_thread.start()

    render_thread = threading.Thread(target=render_thread)
    render_thread.start()

    done = False
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                done = True
                finished = True
            elif event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    is_typing = not is_typing
                    broadcast("KEYUP:W")
                    broadcast("KEYUP:S")
                    broadcast("KEYUP:A")
                    broadcast("KEYUP:D")
                else:
                    is_typing = False
            elif event.type == pygame.KEYDOWN:
                if is_typing:
                    if event.key == pygame.K_RETURN:
                        is_typing = False
                        if text:
                            broadcast(f"MESSAGE: {text}")
                            text = ''
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode
                elif not is_typing:
                    if event.key == pygame.K_w:
                        broadcast("KEYDOWN:W")
                    elif event.key == pygame.K_s:
                        broadcast("KEYDOWN:S")
                    elif event.key == pygame.K_a:
                        broadcast("KEYDOWN:A")
                    elif event.key == pygame.K_d:
                        broadcast("KEYDOWN:D")

            elif event.type == pygame.KEYUP and not is_typing:
                if event.key == pygame.K_w:
                    broadcast("KEYUP:W")
                elif event.key == pygame.K_s:
                    broadcast("KEYUP:S")
                elif event.key == pygame.K_a:
                    broadcast("KEYUP:A")
                elif event.key == pygame.K_d:
                    broadcast("KEYUP:D")

        time.sleep(0.01)

    disconnect()
    pygame.quit()
    sys.exit()
