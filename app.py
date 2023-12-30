import asyncio
import json
import math
from random import randint, choice
import websockets
from flask import Flask, render_template, request, redirect, url_for, session

gridlx = 80
gridly = 80

grid = [[0 for i in range(gridlx)] for j in range(gridly)]
for i in range(gridly):
    if i == 0 or i == gridly - 1:
        grid[i] = [1 for i in range(gridlx)]
    else:
        grid[i][-1] = 1
        grid[i][0] = 1
    for j in range(gridlx):
        if randint(0, 9) < 1:
            grid[i][j] = 1

players = []
items = []
websockets_list = set()

grid = [[0 for i in range(gridlx)] for j in range(gridly)]
for i in range(gridly):
    if i == 0 or i == gridly-1:
        grid[i] = [1 for i in range(gridlx)]
    else:
        grid[i][-1] = 1
        grid[i][0] = 1
    for j in range(gridlx):
        if randint(0,9) < 1:
            grid[i][j] = 1

def checkplayer(x,y):
    for i in players:
        if i.x == x and i.y == y:
            return False
    return True

def checkitem(x,y):
    if grid[y][x] == 1:
        return False
    for i in items:
        if (i['x'] == x and i['y'] == y):
            return False
    return True

def rollDice(sides,number):
    return sum([randint(1,sides) for i in range(int(number*4))])//4

def attack(toAttack,attacker):
    if rollDice(20,1)+attacker.proficiency > players[toAttack].ac:
        players[toAttack].hp-=rollDice(attacker.damage,attacker.damageMultiplier)+attacker.proficiency
        if players[toAttack].hp <= 0:
            for i in players[toAttack].items:
                tryx,tryy=players[toAttack].x,players[toAttack].y
                if i['type'] == 'armour':
                    while not checkitem(tryx,tryy):
                        tryx+=1
                if i['type'] == 'weapon':
                    while not checkitem(tryx,tryy):
                        tryy-=1
                i['x'],i['y'] = tryx,tryy
                items.append(i)
            broadcast_item_positions()    
            broadcast_positions()                                              
            players[toAttack].x = 9999
            players[toAttack].y = 9999 
            return 1
    return 0


def findTarget(player):
    for i in range(len(players)):
        if (player.x-players[i].x)**2+(player.y-players[i].y)**2 <= player.range**2:
            if player.direction == 'W' and player.y - players[i].y > 0:
                return attack(i,player)
            elif player.direction == 'S' and players[i].y - player.y > 0:
                return attack(i,player)
            if player.direction == 'A' and player.x - players[i].x > 0:
                return attack(i,player)
            elif player.direction == 'D' and players[i].x - player.x > 0:
                return attack(i,player)
    return 0


rarities=['common','uncommon','rare','epic','legendary']
healingStats = [2,3,5,7,10]
armourStats = [11,12,13,15,18]
weaponTypes = {"/sword": [8,1,0.3],"/spear":[4,2,0.25],"/axe":[14,1,0.5],"/bow":[6,5,0.5]}
weaponMultiplier = [1,1.25,1.5,2,3]
proficiencyBonuses = [-1,0,1,2,4,8]
def interact(player):
    for i in range(len(items)):
        if items[i]['x'] == player.x and items[i]['y'] == player.y:
            if items[i]['type'] == 'healing':
                player.hp += healingStats[rarities.index(items[i]['rarity'])]
                if player.hp > player.maxhp:
                    player.hp = player.maxhp
                items.pop(i)
                createItem(items[i]['rarity'],"healing")
            else:
                pickedup = items[i]
                hadType = False
                for j in range(len(player.items)):
                    if player.items[j]['type'] == items[i]['type']:
                        player.items[j]['weapontype'],items[i]['weapontype'] = items[i]['weapontype'],player.items[j]['weapontype']
                        player.items[j]['type'],items[i]['type'] = items[i]['type'],player.items[j]['type']
                        player.items[j]['rarity'],items[i]['rarity'] = items[i]['rarity'],player.items[j]['rarity']
                        hadType = True
                if not hadType:
                    player.items.append(items[i])
                    items.pop(i)

                
                if pickedup['type'] == 'armour':
                    player.ac = armourStats[rarities.index(pickedup['rarity'])]
                else:
                    player.damage = weaponTypes[pickedup['weapontype']][0]
                    player.range = weaponTypes[pickedup['weapontype']][1]
                    player.attackSpeed = weaponTypes[pickedup['weapontype']][2]
                    player.damageMultiplier = weaponMultiplier[rarities.index(items[i]['rarity'])]
            broadcast_item_positions()
            return player
    return player


def createItem(rarity,type):
    item={}
    item['x'] = 0
    item['y'] = 0
    while not checkitem(item['x'],item['y']):
        item['x'] = randint(0,gridlx-1)
        item['y'] = randint(0,gridlx-1)
    item['rarity'] = rarity
    item['type'] = type
    if type != 'weapon':
        item['weapontype'] = ""
    else:
        item['weapontype'] = choice(['/sword','/spear','/axe','/bow'])
    return item   

class Player:
    def __init__(self,name):
        self.x = 0
        self.y = 0
        while grid[self.y][self.x] != 0:
            self.x = randint(0,gridlx-1)
            self.y = randint(0,gridlx-1)
        self.name = name
        self.color = [randint(0,255),randint(0,255),randint(0,255)]
        self.hp = 40
        self.maxhp = 40
        self.damage = 4
        self.damageMultiplier = 1
        self.ac = 10
        self.range = 1
        self.attackSpeed = 0.3
        self.items = []
        self.proficiency = 0
        self.direction = 'W'
        self.killCount = 0
        print(self.items)
    def move(self, charin):
        if charin == "W":
            if grid[self.y-1][self.x] == 0 and checkplayer(self.x,self.y-1):
                self.y-=1
            self.direction = 'W'
        elif charin == "S":
            if grid[self.y+1][self.x] == 0 and checkplayer(self.x,self.y+1):
                self.y+=1
            self.direction='S'
        elif charin == "A":
            if grid[self.y][self.x-1] == 0 and checkplayer(self.x-1,self.y):
                self.x-=1
            self.direction = 'A'
        elif charin == "D":
            if grid[self.y][self.x+1] == 0 and checkplayer(self.x+1,self.y):
                self.x+=1
            self.direction = 'D'
        elif charin == "Space":
            self.killCount += findTarget(self)
            self.proficiency = math.floor(math.log(self.killCount+1,2))
            print(self.proficiency)
        elif charin == "E":
            self = interact(self)
            print(self)
            print(self.items)
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'color': self.color,
            'attackSpeed': self.attackSpeed*1000,
            'hp': self.hp
        }


async def handle_connection(websocket, path):
    print('iasfd')
    websockets_list.add(websocket)
    client_id = -1
    playerName = session.get('playerName', 'Guest')
    for i in range(len(players)):
        if players[i].name == playerName:
            client_id = i
    if client_id == -1:
        players.append(Player(playerName))
        client_id = len(players) - 1

    await websocket.send(json.dumps({'client_id': client_id}))
    await websocket.send(json.dumps({'base_grid': grid}))
    await broadcast_item_positions()
    await broadcast_positions()

    try:
        async for message in websocket:
            data = json.loads(message)
            players[data['id']].move(data['direction'])
            await asyncio.gather(
                broadcast_positions(),
                broadcast_item_positions(),
            )
    except websockets.exceptions.ConnectionClosedError:
        # Handle client disconnection
        pass
    finally:
        websockets_list.remove(websocket)
        players.pop(client_id)
        await broadcast_positions()

async def broadcast_positions():
    await asyncio.gather(
        *[websocket.send(json.dumps({'new_positions': {'objects': [p.to_dict() for p in players]}})) for websocket in websockets_list],
        return_exceptions=True,
    )

async def broadcast_item_positions():
    await asyncio.gather(
        *[websocket.send(json.dumps({'item_positions': items})) for websocket in websockets_list],
        return_exceptions=True,
    )

app = Flask(__name__, static_url_path='/static')
app.secret_key='notVerySecret'
players = []
items = []

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['playerName'] = request.form.get('player_name')
        return redirect(url_for('main'))
    return render_template('index.html')

@app.route('/main')
def main():
    return render_template('main.html')


if __name__ == "__main__":
    # Start the Flask app
    app.run(debug=True)

    # Start the WebSocket server
    start_server = websockets.serve(handle_connection, "0.0.0.0", 5001)
    asyncio.get_event_loop().run_until_complete(start_server)
    asyncio.get_event_loop().run_forever()