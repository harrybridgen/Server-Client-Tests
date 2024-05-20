import socket
import pygame
import threading
import json
import time

pygame.init()
win = pygame.display.set_mode((500, 500))
pygame.display.set_caption("Client")


def render_player(x, y, color):
    pygame.draw.rect(win, color, (x, y, 25, 25))


buffer = ""
players_info = {}  
game_running = True


def receive():
    global buffer
    global players_info
    global game_running
    while game_running:
        try:
            data = client.recv(1024).decode("utf-8")
            #print(f"[DEBUG] Received from server: {data}")
            if not data:
                continue
            buffer += data
            while "\n" in buffer:
                line, buffer = buffer.split("\n", 1)
                try:
                    packet = json.loads(line)
                    #print(f"[DEBUG] Received package: {packet}")
                    if "DISCONNECTED" in packet:
                        print("Disconnected\n")
                        del players_info[packet["DISCONNECTED"]]
                        continue
                    elif "CONNECTED" in packet:
                        print("Connected\n")
                        players_info[packet["CONNECTED"]] = {"x": packet["x"], "y": packet["y"], "color": packet["color"]}
                        continue
                    else:
                        #print("Movement\n")
                        for player_id, movement in packet.items():
                            player_id = int(player_id)
                            if player_id in players_info:
                                players_info[player_id]["x"] = movement["x"]
                                players_info[player_id]["y"] = movement["y"]
                                print(f"[DEBUG] Updated player {player_id} position to {movement['x']}, {movement['y']}")

                except json.JSONDecodeError:
                    print(f"[ERROR] Malformed JSON from server: {line}")
                    continue  
        except Exception as e:
            print(f"[ERROR] There was an error receiving data: {e}")
            continue
        time.sleep(0.01)


def input():
    global game_running
    while game_running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                game_running = False
                break

        if not game_running:
            break

        keys = pygame.key.get_pressed()
        msg = {}
        if keys[pygame.K_w]:
            msg = json.dumps({"input": "w"}) + "\n"  
        elif keys[pygame.K_s]:
            msg = json.dumps({"input": "s"}) + "\n"  
        elif keys[pygame.K_a]:
            msg = json.dumps({"input": "a"}) + "\n"  
        elif keys[pygame.K_d]:
            msg = json.dumps({"input": "d"}) + "\n" 

        if msg:
            # print(f"[DEBUG] Sending to server: {msg}")
            client.send(msg.encode("utf-8"))

        time.sleep(0.01)

    pygame.quit()


def game_loop():
    clock = pygame.time.Clock()
    win.fill((0, 0, 0))
    while game_running:
        fps = clock.get_fps()  
        fps_text = font.render(f"FPS: {int(fps)}", True, (0, 0, 0)) 

        win.fill((255, 255, 255))
        win.blit(fps_text, (10, 10)) 
        for current_info in players_info.items():
            render_player(
                current_info[1]["x"], current_info[1]["y"],current_info[1]["color"]
            )
            #print(
            #    f"[DEBUG] Rendering player {player_id} at {current_info['x']}, {current_info['y']}"
            # )
        pygame.display.flip()
        clock.tick(60)


font = pygame.font.Font(None, 32)
clock = pygame.time.Clock()
input_box = pygame.Rect(100, 100, 140, 32)
color_inactive = pygame.Color("lightskyblue3")
color_active = pygame.Color("dodgerblue2")
color = color_inactive
active = False
text = ""
txt_surface = font.render(text, True, color)
done = False
error_text = None

if __name__ == "__main__":
    client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    client.connect(("localhost", 5665))
    receive_thread = threading.Thread(target=receive)
    receive_thread.start()
    while not done:
        for event in pygame.event.get():
            if event.type == pygame.KEYDOWN:
                if active:
                    if event.key == pygame.K_RETURN:
                        print(players_info)
                        for id in players_info.keys():
                            if id == int(text):
                                error_text = font.render(
                                    "Player ID already taken", True, (255, 0, 0)
                                )
                                break
                        player_id = int(text)
                        done = True
                    elif event.key == pygame.K_BACKSPACE:
                        text = text[:-1]
                    else:
                        text += event.unicode
                    txt_surface = font.render(text, True, color)
            if event.type == pygame.MOUSEBUTTONDOWN:
                if input_box.collidepoint(event.pos):
                    active = not active
                else:
                    active = False
                color = color_active if active else color_inactive
        if error_text:
            win.blit(error_text, (100, 150))
        win.fill((30, 30, 30))
        width = max(200, txt_surface.get_width() + 10)
        input_box.w = width
        win.blit(txt_surface, (input_box.x + 5, input_box.y + 5))
        pygame.draw.rect(win, color, input_box, 2)
        pygame.display.flip()
        clock.tick(60)

    client.send(str(player_id).encode("utf-8")) 

    game_loop_thread = threading.Thread(target=game_loop)
    game_loop_thread.start()
    input()
    game_running = False
    receive_thread.join()
    game_loop_thread.join()
