import pygame
import socket
import threading
import json
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

def receive_thread():
    global finished
    while finished == False:
        try:
            data = client.recv(1024).decode("utf-8")
            messages = data.split("\n")
            print(f"[DEBUG] Received from server: {messages}")

            for msg in messages[:-1]:

                if msg.startswith("PLAYER: "):
                    msg = msg[8:]
                    ip, port, new_x, new_y = msg.split(":")
                    key = (ip, int(port))

                    if key not in players:
                        players[key] = {
                            "prev_x": int(new_x),
                            "prev_y": int(new_y),
                            "current_x": int(new_x),
                            "current_y": int(new_y),
                            "last_update": time.time(),
                            "messages": [] 
                        }
                    else:
                        player = players[key]
                        player["prev_x"] = player["current_x"]
                        player["prev_y"] = player["current_y"]
                        player["current_x"] = int(new_x)
                        player["current_y"] = int(new_y)
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
        client.sendall(message.encode("utf-8") + b"\n")
        print(f"[DEBUG] Sent to server: {message}")
    except Exception as e:
        print(f"[ERROR] There was an error sending data: {e}")

def disconnect():
    try:
        print("[INFO] Disconnecting from the server...")
        broadcast("DISCONNECT")
        client.close()
    except Exception as e:
        print(f"[ERROR] There was an error while disconnecting: {e}")
        
def interpolate(value1, value2, alpha):
    return value1 * (1 - alpha) + value2 * alpha

def render_thread():
    global players
    while finished == False:
        clock = pygame.time.Clock()
        clock.tick(60)
        screen.fill(WHITE)

        current_time = time.time()
        for addr, player in players.items():
            time_since_update = current_time - player["last_update"]
            alpha = min(time_since_update / 0.1, 1) 
            x = interpolate(player["prev_x"], player["current_x"], alpha)
            y = interpolate(player["prev_y"], player["current_y"], alpha)
            pygame.draw.rect(screen, BLACK, pygame.Rect(x, y, 20, 20))
            current_time = time.time()
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

AI = False
ai_messages = ["Hello", "Hi", "How are you?", "I'm good, thanks", 
               "What are you doing?", "Nothing much", "How about you?", 
               "I'm just playing this game", "Cool", "Yeah", "I'm bored", "Same", 
               "I'm going to go now", "Bye"]
def ai_behavior():
    global finished
    while AI and not finished:
        directions = random.sample(["W", "A", "S", "D"], k=random.choice([1, 2]))
        for direction in directions:
            broadcast(f"KEYDOWN:{direction}")
        move_duration = random.uniform(0.1, 1.0)
        time.sleep(move_duration)

        for direction in directions:
            broadcast(f"KEYUP:{direction}")

        if random.random() < 0.1:
            ai_message = random.choice(ai_messages)
            broadcast(f"MESSAGE: {ai_message}")

        time.sleep(random.uniform(0.5, 2))

if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 5665))

    if AI:
        ai_thread = threading.Thread(target=ai_behavior)
        ai_thread.start()

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