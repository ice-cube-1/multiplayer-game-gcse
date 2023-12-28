from random import randint,choice
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room
from flask_cors import CORS

gridlx = 80
gridly = 80
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

def attack(player):
    for i in range(len(players)):
        if abs(players[i].x-player.x)<=1 and abs(players[i].y-player.y)<=1 and players[i] != player:
            players[i].hp-=1
            if players[i].hp <= 0:
                players[i].x = 9999
                players[i].y = 9999 

rarities=['common','uncommon','rare','epic','legendary']
healingStats = [2,3,5,7,10]
armourStats = [11,12,13,15,18]
weaponTypes = {"/sword": [8,1,0.3],"/spear":[4,2,0.25],"/axe":[14,1,0.5],"/bow":[6,5,0.5]}
weaponMultiplier = [1,1.25,1.5,2,3]
def interact(player):
    for i in range(len(items)):
        if items[i]['x'] == player.x and items[i]['y'] == player.y:
            if items[i]['type'] == 'healing':
                # improve logic here
                player.hp += healingStats[rarities.index(items[i]['rarity'])]
                if player.hp > player.maxhp:
                    player.hp = player.maxhp
            else:
                player.items.append(items[i])
                if items[i]['type'] == 'armour':
                    player.ac = armourStats[rarities.index(items[i]['rarity'])]
                else:
                    player.damage = weaponTypes[items[i]['weapontype']][0]
                    player.range = weaponTypes[items[i]['weapontype']][1]
                    player.attackSpeed = weaponTypes[items[i]['weapontype']][2]
                    player.damageMultiplier = weaponMultiplier[rarities.index(items[i]['rarity'])]
            items.pop(i)
            socketio.emit('item_positions', items)
            return player


def createItem(rarity,type):
    item={}
    item['x'] = 0
    item['y'] = 0
    while grid[item['y']][item['x']] != 0:
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
    def move(self, charin):
        if charin == "W":
            if grid[self.y-1][self.x] == 0 and checkplayer(self.x,self.y-1):
                self.y-=1
        elif charin == "S":
            if grid[self.y+1][self.x] == 0 and checkplayer(self.x,self.y+1):
                self.y+=1
        elif charin == "A":
            if grid[self.y][self.x-1] == 0 and checkplayer(self.x-1,self.y):
                self.x-=1
        elif charin == "D":
            if grid[self.y][self.x+1] == 0 and checkplayer(self.x+1,self.y):
                self.x+=1
        elif charin == "Space":
            attack(self)
        elif charin == "E":
            self = interact(self)
            print(self.items)
    def to_dict(self):
        return {
            'x': self.x,
            'y': self.y,
            'color': self.color
        }

players = []
items = []


app = Flask(__name__, static_url_path='/static')
app.secret_key='notVerySecret'
socketio = SocketIO(app)
CORS(app)

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        session['playerName'] = request.form.get('player_name')
        return redirect(url_for('main'))
    return render_template('index.html')

@app.route('/main')
def main():
    return render_template('main.html')

@socketio.on('connect')
def handle_connect():
    for i in range(16):
        items.append(createItem("common",'healing'))
        items.append(createItem("common",'armour'))
        items.append(createItem("common",'weapon'))    
        if i%2==0:
            items.append(createItem("uncommon",'healing'))
            items.append(createItem("uncommon",'armour'))            
            items.append(createItem("uncommon",'weapon'))            
        if i%4==0:
            items.append(createItem("rare",'healing'))
            items.append(createItem("rare",'armour'))
            items.append(createItem("rare",'weapon'))
        if i%8==0:
            items.append(createItem("epic",'healing'))
            items.append(createItem("epic",'armour'))
            items.append(createItem("epic",'weapon'))
        if i%16==0:
            items.append(createItem("legendary",'healing'))
            items.append(createItem("legendary",'armour'))
            items.append(createItem("legendary",'weapon'))
    playerName = session.get('playerName','Guest')
    client_id = -1
    for i in range(len(players)):
        if players[i].name == playerName:
            client_id = i
    if client_id == -1:
        players.append(Player(playerName))
        client_id = len(players)-1
    join_room(client_id)
    socketio.emit('client_id', client_id, room=client_id)
    socketio.emit('base_grid', grid)
    socketio.emit('item_positions', items)
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in players]})


@socketio.on('update_position')
def handle_update_position(data):
    players[data['id']].move(data['direction'])
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in players]})
    

if __name__ == '__main__':
    socketio.run(app, debug=True)
