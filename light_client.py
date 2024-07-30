from pynput import keyboard, mouse
import os
import time
import random
from socket import *
import json

mp = mouse.Controller()
keys_pressed = []

#░▒▓█

port_receive = 1337
port_send = 31337

ip = input("ip:\n")

rec_sock = socket(AF_INET, SOCK_DGRAM)
rec_sock.bind(("", port_receive))
rec_sock.settimeout(5)
send_sock = socket(AF_INET, SOCK_DGRAM)
send_sock.setsockopt(SOL_SOCKET, SO_BROADCAST, 1)

send_sock.sendto(b"ready!", (ip, port_send))
x, y = [int(i) for i in rec_sock.recvfrom(16384)[0].decode("utf-8").split("`")]
world = [[["e", " "] for i in range(x)] for j in range(y)]
rec = 0
while rec < len(world):
    data = rec_sock.recvfrom(65535)[0].decode("utf-8").split("`")
    world[int(data[0])] = json.loads("[" + ",".join(data[1:]) + "]")
    rec += 1
rec_sock.settimeout(5)

os.system("") # fix colours/ansi
    
def display():
    global x, y, world, players, me, transition, bullets, lr, team_colours
    
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

def on_press(key):
    global keys_pressed, send_sock, me
    
    try:
        if key.char in ["w", "a", "s", "d"] and key.char not in keys_pressed:
            keys_pressed.append(key.char)
            
    except AttributeError:
        if key == keyboard.Key.space:
            m = mouseinblocks()
            send_sock.sendto((f"{me['x']};{me['y']};{m[0]};{m[1]}").encode("utf-8"), (ip, port_send))

    send_sock.sendto("`".join(keys_pressed).encode("utf-8"), (ip, port_send))
    
def on_release(key):
    global keys_pressed, send_sock

    try:
        if key.char in keys_pressed:
            keys_pressed.remove(key.char)
            
    except AttributeError:
        pass

    send_sock.sendto("`".join(keys_pressed).encode("utf-8"), (ip, port_send))

def on_click(x, y, button, pressed):
    pass

klistener = keyboard.Listener(on_press=on_press, on_release=on_release)
mlistener = mouse.Listener(on_click=on_click)
klistener.start()
mlistener.start()

while True:
    data = rec_sock.recvfrom(65535)[0].decode("utf-8").split("`")
    if data[0] == "d":
        players = json.loads(data[1])
        me = json.loads(data[2])
        transition = bool(int(data[3]))
        bullets = json.loads(data[4])
        lr = int(data[5])
        team_colours = json.loads(data[6])
    elif data[0] == "r":
        world[int(data[2])][int(data[1])] = json.loads(data[3])
    else:
        world[int(data[0])] = json.loads("[" + ",".join(data[1:]) + "]")
        
    display()
