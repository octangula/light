from pynput import keyboard, mouse
import os
import time
import random
from socket import *
import threading
import json

x = 270
y = 68
team_colours = ["5", "1"]
players = [{"x": 0, "y": 0, "xvel": 0, "yvel": 0, "deaths": 0, "dead": False, "colour": t, "keys_pressed": [], "dash_cooldown": 0, "powerups": []} for t in team_colours]
me = players[0]
dash_cooldown = 200
player_speed = 0.025
player_max_speed = 0.8
friction = 0.95
bullet_friction = 0.98
tick_speed = 0.01
game_ticks = 0
mp = mouse.Controller()
world = []
bullets = []
max_bullet_speed = 1
lr = 20

#░▒▓█

port_receive = 31337
port_send = 1337

ip = input("ip:\n")

rec_sock = socket(AF_INET, SOCK_DGRAM)
rec_sock.bind(("", port_receive))
send_sock = socket(AF_INET, SOCK_DGRAM)
send_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

while True:
    if rec_sock.recvfrom(1024)[0] == b"ready!":
        send_sock.sendto((f"{x}`{y}").encode("utf-8"), (ip, port_send))
        break

os.system("") # fix colours/ansi

def receive_input():
    global rec_sock, port_receive, ip

    while True:
        try:
            p2 = rec_sock.recvfrom(1024)[0].decode("utf-8").split("`")

            if len(p2[0]) > 1:
                x, y, mx, my = p2[0].split(";")
                team = 1
                create_bullet(float(x), float(y), float(mx), float(my), int(team))
            else:
                players[1]["keys_pressed"] = p2

        except TimeoutError:
            pass

def send_state():
    global x, y, world, players, me, transition, bullets, lr, team_colours, send_sock, port_send, ip, to_remove

    stuff = ["d", json.dumps(players), json.dumps(players[1]), str(int(transition)), json.dumps(bullets), str(lr), json.dumps(team_colours)]

    send_sock.sendto("`".join(stuff).encode("utf-8"), (ip, port_send))

def create_world():
    global x, y, world, players, me

    world = [[["e", " "] for i in range(x)] for j in range(y)]

    for i in range(y):
        world[i][0] = ["w", "\033[30;47m█\033[0m"]
        world[i][x - 1] = ["w", "\033[30;47m█\033[0m"]
    for i in range(x):
        world[0][i] = ["w", "\033[30;47m█\033[0m"]
        world[y - 1][i] = ["w", "\033[30;47m█\033[0m"]

    p = [0, 0]
    d = [1, 0]
    for i in range(2000):
        if random.randint(1,30) == 1:
            d = random.choice([[1, 0], [-1, 0], [0, 1], [0, -1]])
        if random.randint(1,3) > 1:
            world[p[1] % y][p[0] % x] = ["w", "\033[30;47m█\033[0m"]
        p[0] += d[0]
        p[1] += d[1]

    for player in players:
        world[round(player["y"])][round(player["x"])] = ["e", " "]
    
def display():
    global x, y, world, players, me, bullets, team_colours, transition, lr
    print(f"\033[{y + 4}A") # move cursor to top

    brightness = {
        "░": 0.2,
        "▒": 0.4,
        "▓": 0.6,
        "█": 0.9
    }

    display = [[" " for i in range(x)] for j in range(y)]

    #lit += [[round(p[0]), round(p[1]), distance([round(me["x"]), round(me["y"])], [p[0], p[1]])] for p in circle([me["x"], me["y"]], 20)]
    lit = [[round(i + me["x"] - lr), round(j + me["y"] - int(lr/2)), me["x"], me["y"], 4 / (distance([i + round(me["x"]) - lr, j + round(me["y"]) - int(lr/2)], [me["x"], me["y"]]) + 0.0001), "37"] for i in range(lr*2 + 1) for j in range(lr + 1)]

    if transition:
        lit = [[i, j, i, j, 1, "37"] for i in range(x) for j in range(y)]

    for b in bullets:
        lit += [[round(p[0]), round(p[1]), round(b[0]), round(b[1]), 2 / (distance([round(b[0]), round(b[1])], [p[0], p[1]]) + 0.01), (f"3{team_colours[b[4]]}" if b[6] else "37")] for p in circle([b[0], b[1]], b[5])]
    
    for tile in lit:
        if tile[4] <= 0.2 or tile[0] >= x or tile[0] < 0 or tile[1] >= y or tile[1] < 0:
            continue
        if all([world[p[1]][p[0]][0] == "e" for p in line([tile[2] % x, tile[3] % y], [tile[0], tile[1]])]):
            if world[tile[1]][tile[0]][0] == "w":
                if tile[4] > 0.2:
                    display[tile[1]][tile[0]] = world[tile[1]][tile[0]][1]
                
            elif world[tile[1]][tile[0]][0] == "e":
                if display[tile[1]][tile[0]][-5:-4] in brightness.keys():
                    tile[4] += brightness[display[tile[1]][tile[0]][-5:-4]]
                    
                display[tile[1]][tile[0]] = f"\033[{tile[5]}m"
                if tile[4] > 0.9:
                    display[tile[1]][tile[0]] += "█"
                elif tile[4] > 0.6:
                    display[tile[1]][tile[0]] += "▓"
                elif tile[4] > 0.4:
                    display[tile[1]][tile[0]] += "▒"
                elif tile[4] > 0.2:
                    display[tile[1]][tile[0]] += "░"
                display[tile[1]][tile[0]] += "\033[0m"

            for p in players:
                if [tile[0], tile[1]] == [round(p["x"]), round(p["y"])] and not p["dead"]:
                    if tile[4] > 0.2:
                        display[tile[1]][tile[0]] = f"\033[3{p['colour']}m■\033[0m"
                    if tile[4] > 0.6:
                        display[tile[1]][tile[0]] = f"\033[3{p['colour']};47m■\033[0m"

    if not me["dead"]:
        display[round(me["y"]) % y][round(me["x"]) % x] = f"\033[3{me['colour']};47m■\033[0m"

    for b in bullets:
        display[round(b[1])][round(b[0])] = f"\033[30;4{team_colours[b[4]] if b[6] else 7}m*\033[0m"

    for i in range(y): # add silly border after in order to not mess with playing area
        display[i].insert(0, "|")
        display[i].append("|")
        
    print(f" \033[0mdeath count: " + " | ".join(f"\033[3{p['colour']}m{p['deaths']}\033[0m" for p in players) + "\n" + "-" * (x + 2) + "\n" + "\n".join(["".join(display[i]) for i in range(len(display))]) + "\n" + "-" * (x + 2))

def distance(p1, p2):
    return (abs(p2[0] - p1[0]) ** 2 + (abs(p2[1] - p1[1]) * 2) ** 2) ** 0.5

def circle(c, r): # center point, horizontal radius
    points = [[c[0] + i - r, c[1]] for i in range(r*2 + 1)]
    for i in range(int(r/2)):
        points += [[c[0] - (r - 1) + j + i*2, c[1] + i + 1] for j in range(r*2 - 1 - i*4)]
        points += [[c[0] - (r - 1) + j + i*2, c[1] - i - 1] for j in range(r*2 - 1 - i*4)]
    return points

def line(p1, p2):
    if p2[0] - p1[0] == 0:
        p2[0] += 0.01
    if p2[1] - p1[1] == 0:
        p2[1] += 0.01 # lazy cheats to fix div 0 errors

    points = []
        
    for i in range(abs(round(p2[0] - p1[0]))): # (y = mx + c) for x in points
        if p2[0] < p1[0]: # if negative invert
            i = -1 * i
        points.append([round(p1[0] + i), round(((p2[1] - p1[1])/(p2[0] - p1[0])) * (p1[0] + i) + (p1[1] - (((p2[1] - p1[1])/(p2[0] - p1[0])) * p1[0])))])
        
    for i in range(abs(round(p2[1] - p1[1]))): # (x = (y - c)/m) for y in points
        if p2[1] < p1[1]:
            i = -1 * i
        points.append([round(((p1[1] + i) - (p1[1] - (((p2[1] - p1[1])/(p2[0] - p1[0])) * p1[0])))/((p2[1] - p1[1])/(p2[0] - p1[0]))), round(p1[1] + i)])

    return points

def mouseinblocks():
    cx = 9
    cy = 19 # one character 9px by 19px
    ml = 0
    mt = 44 # 8px margin from left, 20px margin from top
    return [max(min((mp.position[0] - (ml + 2 * cx))/cx, x), 0), max(min((mp.position[1] - (mt + cy * 2))/cy, y), 0)]

def update():
    global x, y, players, me, bullets, player_speed, player_max_speed, friction, game_ticks, world, bullets, bullet_friction, transition, dash_cooldown

    game_ticks += 1

    for player in players:
        if world[round(player["y"]) % y][round((player["x"] + player["xvel"])) % x][0] == "w":
            player["xvel"] = 0
        if world[round((player["y"] + player["yvel"])) % y][round(player["x"]) % x][0] == "w":
            player["yvel"] = 0

        if world[round((player["y"] + player["yvel"]) % y)][round((player["x"] + player["xvel"]) % x)][0] == "e":
            player["x"], player["y"] = (player["x"] + player["xvel"]) % x, (player["y"] + player["yvel"]) % y

        if "w" in player["keys_pressed"]:
            player["yvel"] -= player_speed / 2
        elif "s" in player["keys_pressed"]:
            player["yvel"] += player_speed / 2
        else:
            player["yvel"] = player["yvel"] * friction
            
        if "a" in player["keys_pressed"]:
            player["xvel"] -= player_speed
        elif "d" in player["keys_pressed"]:
            player["xvel"] += player_speed
        else:
            player["xvel"] = player["xvel"] * friction

        player["xvel"] = max(min(player["xvel"], player_max_speed), -1 * player_max_speed)
        player["yvel"] = max(min(player["yvel"], 0.5 * player_max_speed), -0.5 * player_max_speed)

    for b in bullets:
        if world[round(b[1]) % y][round((b[0] + b[2])) % x][0] == "w":
            b[2] *= -1
        if world[round((b[1] + b[3])) % y][round(b[0]) % x][0] == "w":
            b[3] *= -1
        
        b[0] += b[2]
        b[1] += b[3]
        b[2] *= bullet_friction
        b[3] *= bullet_friction

        if b[6]:
            for point in circle([b[0], b[1]], b[5]):
                for p in players:
                    if (not p["dead"]) and [round(p["x"]), round(p["y"])] == [round(point[0]), round(point[1])]:
                        p["deaths"] += 1
                        p["dead"] = True
                if point[0] > 1 and point[0] < x - 2 and point[1] > 1 and point[1] < y - 2 and world[round(point[1])][round(point[0])][0] == "w":
                    world[round(point[1])][round(point[0])] = ["e", " "]
                    send_sock.sendto(("r" + "`" + "`".join([str(round(point[0])), str(round(point[1])), json.dumps(["e", " "])])).encode("utf-8"), (ip, port_send))

            if b[5] == 0:
                bullets.remove(b)

            if game_ticks % 10 == 0:
                b[5] -= 1
        else:
            for p in players:
                if players.index(p) != b[4] and (not p["dead"]) and [round(p["x"]), round(p["y"])] == [round(b[0]), round(b[1])]:
                    p["deaths"] += 1
                    p["dead"] = True

        if round(b[0]) >= x or round(b[0]) < 0 or round(b[1]) >= y or round(b[1]) < 0:
            bullets.remove(b)
        if round(b[2]) == 0 and round(b[3]) == 0:
            b[6] = True

    if [p["dead"] for p in players].count(False) < 2:
        if not transition:
            klistener.stop()
            mlistener.stop()
            transition = game_ticks
        else:
            if game_ticks >= transition + 100:
                start_game()

def on_press(key):
    global me

    try:
        if key.char == "p":
            klistener.stop()
            mlistener.stop()
            quit()
        if key.char == "l":
            klistener.stop()
            mlistener.stop()
            start_game()
        if key.char in ["w", "a", "s", "d"] and key.char not in me["keys_pressed"]:
            me["keys_pressed"].append(key.char)
            
    except AttributeError:
        if key == keyboard.Key.space and "space" not in me["keys_pressed"]:
            me["keys_pressed"].append("space")
            m = mouseinblocks()
            create_bullet(me["x"], me["y"], m[0], m[1], players.index(me))
        #if key == keyboard.Key.shift and "shift" not in me["keys_pressed"]:
            #me["keys_pressed"].append("shift")
            #me["xvel"] *= 10
            #me["yvel"] *= 10

def on_release(key):
    global me

    try:
        if key.char in me["keys_pressed"]:
            me["keys_pressed"].remove(key.char)
            
    except AttributeError:
        if key == keyboard.Key.space and "space" in me["keys_pressed"]:
            me["keys_pressed"].remove("space")
        #if key == keyboard.Key.shift and "shift" in me["keys_pressed"]:
            #me["keys_pressed"].remove("shift")

def on_click(x, y, button, pressed):
    pass

def start_game():
    global klistener, mlistener, started, players, transition, bullets

    bullets = []
    
    transition = False
    started = False
    
    print("\033[2J") # clear screen

    tempdisplay = [[" " for i in range(x)] for j in range(y)]
    for p in players:
        p["x"] = random.randint(1, x - 2)
        p["y"] = random.randint(1, y - 2)
        p["dead"] = False
        p["keys_pressed"] = []
        tempdisplay[round(p["y"]) % y][round(p["x"]) % x] = f"\033[3{p['colour']}m■\033[0m"

    print("-" * (x + 2) + "\n" + "\n".join(["".join(tempdisplay[i]) for i in range(len(tempdisplay))]) + "\n" + "-" * (x + 2))

    if world == []:
        create_world()

        for j in range(len(world)):
            send_sock.sendto((str(j) + "`" + "`".join([json.dumps(i) for i in world[j]])).encode("utf-8"), (ip, port_send))

    #print("3")
    #time.sleep(1)
    #print("2")
    #time.sleep(1)
    #print("1")
    #time.sleep(1)

    print("\033[2J")

    klistener = keyboard.Listener(on_press=on_press, on_release=on_release)
    mlistener = mouse.Listener(on_click=on_click)
    klistener.start()
    mlistener.start()

    started = True

start_game()

rec_sock.settimeout(0.05)

threading.Thread(target=receive_input).start()

while True:
    if started:
        update()
        display()
        send_state()
    time.sleep(tick_speed)
