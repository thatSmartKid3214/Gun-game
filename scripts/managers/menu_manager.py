# Menu manager
import pygame
pygame.init()
from pygame.locals import *
from scripts import *
import socket,threading,json
import sys,pickle,subprocess,random

def get_wifi_ip():
    data = subprocess.run(["ipconfig"],capture_output=True).stdout.decode() #get ipconfig data as a string
    data_list = data.split("\n")
    index = data_list[data_list.index("Wireless LAN adapter Wi-Fi:\r")+2].lstrip()
    if index == "Media State . . . . . . . . . . . : Media disconnected\r":
        ip = ""
    else:
        ip = data_list[data_list.index("Wireless LAN adapter Wi-Fi:\r")+4].lstrip().split("IPv4 Address. . . . . . . . . . . : ")[1].split("\r")[0] # get ip when connected to wifi
    return ip

addresses = []
can_send = True

def UDP_find_games(port,obj):
    global addresses,can_send
    can_send = True
    addresses = []
    sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)

    ip = get_wifi_ip()
    ip_search = ip.split('.')
    ip_search = f"{ip_search[0]}.{ip_search[1]}.{ip_search[2]}."
    #get the range of the ip addresses
    data = subprocess.run(["ipconfig"],capture_output=True).stdout.decode()
    data = data.split("\n")
    index = data[data.index("Wireless LAN adapter Wi-Fi:\r")+2].lstrip()
    count = 0
    if index == "Media State . . . . . . . . . . . : Media disconnected\r":
        pass
    else:
        ip_range = int(data[data.index("Wireless LAN adapter Wi-Fi:\r")+5].lstrip().split("Subnet Mask . . . . . . . . . . . : ")[1].replace('\r','').split('.')[0])
    
    while True:
        if can_send == True:
            if can_send == False:
                sock.close()
                break
            for i in range(ip_range+1):
                address = f"{ip_search}{i}"
                try:
                    sock.sendto("FIND_GAME:GUN_GAME".encode(),(address,port))
                except Exception as e:
                    print(e)

            try:
                data,addr = sock.recvfrom(2048)
                if not data or data == "":
                    addresses.remove(addr)
                if data.decode() == "I_AM_HERE":
                    if addr not in addresses:
                        addresses.append(addr)
            except Exception as e:
                print(e)
            count += 1
            obj.games = addresses
        else:
            print("no games found")

def get_address(ip,port,obj):
    global addresses,can_send
    sock = socket.socket(socket.AF_INET,socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    connected = False
    index = 0
    while True:
        if can_send == True:
            try:
                if connected == False:
                    sock.connect((ip,port))
                    connected = True
                sock.send("FIND_GAME:GUN_GAME".encode())
                if sock.recv(2048).decode() == "I_AM_HERE":
                    if (ip,port) not in addresses:
                        addresses.append((ip,port))
                        indexes = len(addresses)
                obj.games = addresses
            except Exception as e:
                if len(addresses) != 0:
                    addr = addresses[index]
                    if addr == (ip,port):
                        addresses.remove(addr)
        else:
            try:
                sock.send("stop".encode())
                sock.close()
                break
            except Exception as e:
                #print(e)
                break

def TCP_find_games(port,obj):
    global addresses,can_send
    can_send = True
    addresses = []

    ip = get_wifi_ip()
    ip_search = ip.split('.')
    ip_search = f"{ip_search[0]}.{ip_search[1]}.{ip_search[2]}."
    #get the range of the ip addresses
    data = subprocess.run(["ipconfig"],capture_output=True).stdout.decode()
    data = data.split("\n")
    index = data[data.index("Wireless LAN adapter Wi-Fi:\r")+2].lstrip()
    count = 0
    if index == "Media State . . . . . . . . . . . : Media disconnected\r":
        pass
    else:
        ip_range = int(data[data.index("Wireless LAN adapter Wi-Fi:\r")+5].lstrip().split("Subnet Mask . . . . . . . . . . . : ")[1].replace('\r','').split('.')[0])
    
    for i in range(ip_range+1):
        ip_address = f"{ip_search}{i}"
        get_thread = threading.Thread(target=get_address, args=(ip_address,port,obj))
        get_thread.daemon = True
        get_thread.start()

class Menu:
    def __init__(self, game):
        self.state = "Menu"
        self.game = game
        self.clicked = False
        self.click_tick = 20
        self.font = Text("data/images/font.png",1,2)

        #Main menu screen
        self.play_button = Button(30, 35, 2, "SinglePlayer", 4,"Big", True)
        self.multiplayer_btn = Button(30, 90, 2, "Multiplayer", 4, "Big",True)
        self.level_btn = Button(30, 145, 2, "Level Editor", 4, "Big",True)
        
        #Multiplayer screen
        self.LAN_btn = Button(45,70,3,"LAN Game",5,"Big",True)
        self.Online_btn = Button(275,70,3,"Online",5,"Big",True)
        self.Host_btn = Button(45,70,3,"Host",5,"small",True)
        self.Join_btn = Button(275,70,3,"Join",5,"small",True)
        self.port = self.game.settings["networking"]["port"]
        self.can_send = True
        self.clock = pygame.time.Clock()
        self.games = []
        self.udp_sock = socket.socket(socket.AF_INET,socket.SOCK_DGRAM)
        self.udp_sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)        
    
    def run(self):
        global can_send
        self.game.display.fill((90,90,90))
        self.clock.tick(self.game.FPS)
        pos = pygame.mouse.get_pos()
        size_dif = float(self.game.screen.get_width()/self.game.display.get_width())
        pos = [round(pos[0]/size_dif), round(pos[1]/size_dif)]

        for event in pygame.event.get():
            if event.type == QUIT:
                pygame.quit()
                sys.exit()
            if event.type == KEYDOWN:
                if event.key == K_F11:
                    if self.game.fullscreen != True:
                        self.game.screen = pygame.display.set_mode((int(self.game.win_dims[0]*self.game.scale),int(self.game.win_dims[1]*self.game.scale)),pygame.FULLSCREEN)
                        self.game.fullscreen = True
                    else:
                        self.game.screen = pygame.display.set_mode((int(self.game.win_dims[0]*self.game.scale),int(self.game.win_dims[1]*self.game.scale)),pygame.RESIZABLE)
                        self.game.fullscreen = False
        
        if self.state == "Menu":
            self.play_button.update(self.game.display, pos)
            self.multiplayer_btn.update(self.game.display,pos)
            self.level_btn.update(self.game.display, pos)

            self.Online_btn.disabled = True
            self.LAN_btn.disabled = True

            if self.play_button.clicked == True and self.clicked == False:
                self.game.create_game_manager("Singleplayer")
                self.game.state = "Play"
                self.clicked = True
            if self.level_btn.clicked == True and self.clicked == False:
                self.game.state = 'Level_Editor'
                self.game.create_Level_editor()
                self.clicked = True
            if self.multiplayer_btn.clicked == True and self.clicked == False:
                self.Online_btn.disabled = False
                self.LAN_btn.disabled = False
                self.clicked = True
                self.state = "Mult_Screen"
                
        if self.state == "Mult_Screen":
            self.LAN_btn.update(self.game.display,pos)

            self.play_button.disabled = True
            self.multiplayer_btn.disabled = True
            self.level_btn.disabled = True
            
            if self.LAN_btn.clicked == True and self.clicked == False:
                self.state = "LAN screen"
                self.clicked = True

        if self.state == "LAN screen":
            self.Host_btn.update(self.game.display, pos)
            self.Join_btn.update(self.game.display,pos)

            if self.Host_btn.clicked == True and self.clicked == False:
                self.game.create_game_manager("Multiplayer")
                map_name = "Debug_level_0"
                map_type = "Normal"
                data = None
                game_info = ["Classic",12,[]]
                
                try:
                    with open(f"data/maps/{map_name}.level","rb") as file:
                        data = pickle.load(file)
                        file.close()
                        for pos in data["data"]["spawnpoints"]:
                            game_info[2].append(pos[1])
                except:
                    with open(f"data/maps/custom_maps/{map_name}.level","rb") as file:
                        data = pickle.load(file)
                        file.close()
                        for pos in data["data"]["spawnpoints"]:
                            game_info[2].append(pos[1])
                    map_type = "Custom"

                game_info.append(map_type)
                items = []
                for item in data["data"]["items"]:
                    item[1][0] *= self.game.TILESIZE
                    item[1][1] *= self.game.TILESIZE
                    item.append([0,0])
                    item.append("normal")
                    item.append(random.randint(0,1500))
                    item.append([])
                    items.append(item)

                game_info.append(items)
                game_info.append(map_name)

                self.game.game_manager.setup_mult(True,self.port,"0",game_info)
                self.game.state = "Play"
                self.clicked = True
                
            if self.Join_btn.clicked == True and self.clicked == False:
                if self.game.protocol == "UDP":
                    find_game_thread = threading.Thread(target=UDP_find_games, args=(self.port,self))
                    find_game_thread.daemon = True
                    find_game_thread.start()
                elif self.game.protocol == "TCP":
                    find_game_thread = threading.Thread(target=TCP_find_games, args=(self.port,self))
                    find_game_thread.daemon = True
                    find_game_thread.start()
                self.state = "Join_screen"
                self.clicked = True
                
        if self.state == "Join_screen":
            self.font.render(self.game.display,"Available games",10,4,(255,255,255))
            #print(addresses,self.games)
            for i,game in enumerate(self.games):
                button = Button(10+(i*24),19, 2, f"Game {i+1}",6,"small",True)
                button.update(self.game.display,pos)
                if button.clicked and self.clicked == False:
                    self.game.create_game_manager("Multiplayer")
                    self.game.game_manager.items = []
                    self.game.game_manager.setup_mult(False,game[1],game[0])
                    can_send = False
                    self.game.state = "Play"
                    self.clicked = True

        if self.clicked == True:
            self.click_tick -= 1
            if self.click_tick <= 0:
                self.clicked = False
                self.click_tick = 30
        self.game.screen.blit(pygame.transform.scale(self.game.display, (self.game.screen.get_width(),self.game.screen.get_height())), (0,0))
        pygame.display.update()
