from random import randint, choice
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room
from flask_cors import CORS
import math
from datetime import datetime, timedelta
import jsonpickle
import os
import threading
from werkzeug.middleware.proxy_fix import ProxyFix
import identity
import identity.web
from flask_session import Session
import app_config


def checkplayer(x, y):
    '''Checks if a player is in space'''
    for i in players:
        if i.x == x and i.y == y and i.visible == True:
            return False
    return True


def checkitem(x, y):
    '''Checks if either an item or wall is in space'''
    if grid[y][x] == 1:
        return False
    for i in items:
        if (i['x'] == x and i['y'] == y):
            return False
    return True


def rollDice(sides, number):
    '''Returns sum of NdX dice (can be .25)'''
    return sum([randint(1, sides) for i in range(int(number*4))])//4


def attack(toAttack, attacker):
    '''deals damage / kill logic from attack'''
    if rollDice(40, 1)+attacker.proficiency > players[toAttack].ac:  # did it actually hit, if so do damage
        players[toAttack].hp -= rollDice(attacker.damage, attacker.damageMultiplier)+attacker.proficiency
        if players[toAttack].hp <= 0:  # if is dead
            players[toAttack].hp = 0
            for i in players[toAttack].items:  # drops loot (SIMPLIFY)
                tryx, tryy = players[toAttack].x, players[toAttack].y
                if i['type'] == 'armour':
                    while not checkitem(tryx, tryy):
                        tryx += 1
                if i['type'] == 'weapon':
                    while not checkitem(tryx, tryy):
                        tryy -= 1
                i['x'], i['y'] = tryx, tryy
                items.append(i)
            socketio.emit('item_positions', items)
            socketio.emit('new_positions',  {"objects": [i.to_dict() for i in players]})
            # stores everything that needs to be kept during respawn (SIMPLIFY)
            storeColor = players[toAttack].color
            storemaxHP = players[toAttack].maxhp-1
            storeKills = players[toAttack].killCount
            storeProficiency = players[toAttack].proficiency
            players[toAttack] = Player(players[toAttack].name)
            players[toAttack].color = storeColor
            players[toAttack].maxhp = storemaxHP
            players[toAttack].killCount = storeKills
            players[toAttack].proficiency = storeProficiency
            players[toAttack].hp = storemaxHP
            # AT LEAST SOME SHOULD BE MODULARIZED
            messages.append([f'{datetime.now().strftime("[%H:%M] ")}{players[toAttack].name} was killed by {attacker.name}', "black"])
            socketio.emit('message', [messages[-1]])
            return 1  # add to kill count
    return 0  # did not kill


def findTarget(player):
    '''Attacks the first (presumes there's only one) player in range'''
    '''Does this based on both range in a semicircle and direction'''
    for i in range(len(players)):
        if (player.x-players[i].x)**2+(player.y-players[i].y)**2 <= player.range**2 and players[i].visible == True and players[i].name not in player.ally and player.name not in players[i].ally:
            if player.direction == 'W' and player.y - players[i].y > 0:
                return attack(i, player)
            elif player.direction == 'S' and players[i].y - player.y > 0:
                return attack(i, player)
            if player.direction == 'A' and player.x - players[i].x > 0:
                return attack(i, player)
            elif player.direction == 'D' and players[i].x - player.x > 0:
                return attack(i, player)
    return 0


def interact(player):
    '''Picks up an item + edits your stats when you press E. Also drops your item if you have one'''
    for i in range(len(items)):
        if items[i]['x'] == player.x and items[i]['y'] == player.y:
            if items[i]['type'] == 'healing':  # comparatively simple as you just use it
                player.hp += healingStats[rarities.index(items[i]['rarity'])]
                if player.hp > player.maxhp:
                    player.hp = player.maxhp
                items.append(createItem(items[i]['rarity'], "healing"))
                items.pop(i)
            else:
                hadType = False
                for j in range(len(player.items)):
                    # swaps all stats of the old and new items
                    if player.items[j]['type'] == items[i]['type']:
                        player.items[j]['weapontype'], items[i]['weapontype'] = items[i]['weapontype'], player.items[j]['weapontype']
                        player.items[j]['type'], items[i]['type'] = items[i]['type'], player.items[j]['type']
                        player.items[j]['rarity'], items[i]['rarity'] = items[i]['rarity'], player.items[j]['rarity']
                        hadType = True
                if not hadType:  # otherwise adds it to their list of items
                    player.items.append(items[i])
                    items.pop(i)
                for pickedup in player.items:  # modifies the stats - it does this to both items, no good reason as to why but it doesn't take much processing
                    if pickedup['type'] == 'armour':
                        player.ac = armourStats[rarities.index(
                            pickedup['rarity'])]
                    else:
                        player.damage = weaponTypes[pickedup['weapontype']][0]
                        player.range = weaponTypes[pickedup['weapontype']][1]
                        player.attackSpeed = weaponTypes[pickedup['weapontype']][2]
                        player.damageMultiplier = weaponMultiplier[rarities.index(
                            pickedup['rarity'])]
            # writes the new info to a file - more of a failsafe although useless as players is old
            open('data/playerinfo.json', 'w').write(jsonpickle.encode(players))
            open('data/itemsinfo.json', 'w').write(jsonpickle.encode(items))
            socketio.emit('item_positions', items)
    return player  # player has changed


def zombify():
    '''Checks if there are any players that should be offline and if so makes them invisible'''
    currentTime = datetime.now()
    with zombifyLock:
        for i in range(len(players)):
            delta = currentTime - players[i].lastMove
            if delta.total_seconds() > 120 and players[i].visible:
                players[i].visible = False
                messages.append(
                    [f'{datetime.now().strftime("[%H:%M] ")}{players[i].name} has gone offline', "black"])
                socketio.emit('message', [messages[-1]])
        socketio.emit('new_positions', {"objects": [
                      i.to_dict() for i in players]})
        playersInfo = [i.getInfoInString()
                       for i in players if i.displayedAnywhere]
        socketio.emit('PlayersInfo', sorted(
            playersInfo, key=lambda x: int(x[2]), reverse=True))


def createItem(rarity, type):
    '''Creates an item in a random place given a rarity and type'''
    item = {}
    item['x'] = 0
    item['y'] = 0
    while not checkitem(item['x'], item['y']):
        item['x'] = randint(0, gridlx-1)
        item['y'] = randint(0, gridlx-1)
    item['rarity'] = rarity
    item['type'] = type
    if type != 'weapon':
        item['weapontype'] = ""
    else:
        item['weapontype'] = choice(['/sword', '/spear', '/axe', '/bow'])
    return item


class Player:
    def __init__(self, name):
        # all the variables for it - SIMPLIFY
        self.x = 0
        self.y = 0
        while grid[self.y][self.x] != 0:
            self.x = randint(0, gridlx-1)
            self.y = randint(0, gridlx-1)
        self.name = name
        self.color = f'rgb({randint(0,255)},{randint(0,255)},{randint(0,255)})'
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
        self.visible = True
        self.lastMove = datetime.now()
        self.displayedAnywhere = True
        self.ally=[self.name]
    def move(self, charin):
        '''deals with client input'''
        self.lastMove = datetime.now()
        if self.visible == False:  # come back online
            self.visible = True
            self.displayedAnywhere = True
            messages.append(
                [f'{datetime.now().strftime("[%H:%M] ")}{self.name} has joined', "black"])
            socketio.emit('message', [messages[-1]])
        if charin == "W":
            # SIMPLIFY by just putting the gridcheck in checkplayer
            if grid[self.y-1][self.x] == 0 and checkplayer(self.x, self.y-1):
                self.y -= 1
            self.direction = 'W'
        elif charin == "S":
            if grid[self.y+1][self.x] == 0 and checkplayer(self.x, self.y+1):
                self.y += 1
            self.direction = 'S'
        elif charin == "A":
            if grid[self.y][self.x-1] == 0 and checkplayer(self.x-1, self.y):
                self.x -= 1
            self.direction = 'A'
        elif charin == "D":
            if grid[self.y][self.x+1] == 0 and checkplayer(self.x+1, self.y):
                self.x += 1
            self.direction = 'D'
        elif charin == "Space":
            # which actually returns the killcount from the attack function if called
            self.killCount += findTarget(self)
            playersInfo = [i.getInfoInString()
                           for i in players if i.displayedAnywhere]
            self.proficiency = math.floor(math.log(self.killCount+1, 2))
            self.maxhp = 40+self.killCount
            socketio.emit('PlayersInfo', sorted(
                playersInfo, key=lambda x: int(x[2]), reverse=True))
        elif charin == "E":
            self = interact(self)

    def to_dict(self):
        '''only what the client needs - simpler to serialize, more secure + less traffic'''
        weapontype, weaponrarity, armour = False, False, False
        for i in self.items:
            if i['type'] == 'weapon':
                weaponrarity,weapontype = i['rarity'],i['weapontype']
            else:
                armour = i['rarity']
        return {
            'x': self.x,
            'y': self.y,
            'color': self.color,
            'attackSpeed': self.attackSpeed*1000,
            'hp': self.hp,
            'name': self.name,
            'visible': self.visible,
            'name': str(self.name),
            'weapon': weapontype,
            'weaponrarity' : weaponrarity,
            'armour': armour
        }

    def getInfoInString(self):
        '''for the leaderboard'''
        if self.visible:
            status = "online"
        else:
            status = "offline"
        return f'{self.name}: {self.hp}/{self.maxhp} - Level {self.proficiency}, {self.killCount} kills ({status})', self.color, self.killCount

    def getInfoForSpecificPlayer(self):
        '''more detailed info about player, formatted by client'''
        return [f'{self.name}:\nLevel: {self.proficiency} ({self.killCount} kills)\nHP: {self.hp}/{self.maxhp}\nArmour class: {self.ac}',
                f'\nDamage: {math.floor(self.damageMultiplier+self.proficiency)}-{math.floor((self.damageMultiplier*self.damage)+self.proficiency)}\nRange: {self.range}\nAttack speed: {self.attackSpeed}s',
                self.items]


def createGrid():
    '''creates a grid with walls at the edge and in random places'''
    grid = [[0 for i in range(gridlx)] for j in range(gridly)]
    for i in range(gridly):
        if i == 0 or i == gridly-1:
            grid[i] = [1 for i in range(gridlx)]
        else:
            grid[i][-1] = 1
            grid[i][0] = 1
        for j in range(gridlx):
            if randint(0, 9) < 1:
                grid[i][j] = 1
    return grid


def weeklyReset():
    '''all characters lose all stats etc, only thing that stays is color, username'''
    for i in range(len(players)):
        for j in players[i].items:
            items.append(j)
        storeColor = players[i].color
        storelastmove = players[i].lastMove  # SIMPLIFY STORES
        players[i] = Player(players[i].name)
        players[i].color = storeColor
        players[i].lastMove = storelastmove


def dailyReset():
    '''grid regeneates, items on board lose'''
    global items
    grid = createGrid()
    olditems = [i for i in items]
    items = []
    for i in olditems:
        items.append(createItem(i['rarity'], i['type']))
    # should they be shown on the leaderboard
    if (datetime.now()-players[i].lastMove).total_seconds() > 60*60*24:
        players[i].displayedAnywhere = False
    # SIMPLIFY all of this could go into separate functions
    socketio.emit('base_grid', grid)
    playersInfo = [i.getInfoInString() for i in players if i.displayedAnywhere]
    socketio.emit('specificPlayerInfo', [
                  i.getInfoForSpecificPlayer() for i in players])
    socketio.emit('PlayersInfo', sorted(
        playersInfo, key=lambda x: int(x[2]), reverse=True))
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in players]})
    messages.append(
        [f'{datetime.now().strftime("[%H:%M] ")}The game has reset overnight', "black"])
    socketio.emit('message', [messages[-1]])


def TimeTillRun():
    '''Time until next reset'''
    now = datetime.now()
    scheduled = datetime.combine(
        now.date(), datetime.strptime("02:00", "%H:%M").time())
    if now > scheduled:
        scheduled += timedelta(days=1)
    return (scheduled-now).total_seconds()

def timeUntilMorning():
    now = datetime.now()
    scheduled = datetime.combine(
        now.date(), datetime.strptime("08:30", "%H:%M").time())
    if now > scheduled:
        scheduled += timedelta(days=1)
    return (scheduled-now).total_seconds()

def checkRunnable():
    global canrun
    while True:
        canrun = True
        threading.Event().wait(timeUntilMorning())
        if datetime.today().weekday() < 5:
            canrun = False
        threading.Event().wait(3.75*60*60)
        canrun = True
        threading.Event.wait(45*60)
        if datetime.today().weekday() < 5:
            canrun = False
        threading.Event.wait(3.25*60*60)
        canrun = True

def resetCheck():
    '''waits in a thread until next reset, then possibly does a weekly one before the daily one'''
    while True:
        threading.Event().wait(TimeTillRun())
        if datetime.today().weekday() == 0:
            weeklyReset()
        dailyReset()


def waitZombify():
    '''waits between offline checks'''
    while True:
        threading.Event().wait(5)
        zombify()

# initialises constants + web / thread stuff
app = Flask(__name__, static_url_path='/static')
app.secret_key = 'notVerySecret'
socketio = SocketIO(app, async_mode='threading')
CORS(app)
app.config.from_object(app_config)
Session(app)
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)
auth = identity.web.Auth(session=session, authority=app.config.get("AUTHORITY"), client_id=app.config["CLIENT_ID"], client_credential=app.config["CLIENT_SECRET"],)
thread = threading.Thread(target=resetCheck)
thread.start()
zombifyThread = threading.Thread(target=waitZombify)
zombifyThread.start()
zombifyLock = threading.Lock()
offlineThread = threading.Thread(target=checkRunnable)
offlineThread.start()
gridlx, gridly = 80, 80
rarities = ['common', 'uncommon', 'rare', 'epic', 'legendary']
healingStats = [4, 6, 10, 16, 24]
armourStats = [12, 14, 16, 19, 22]
weaponTypes = {"/sword": [8, 1, 0.3], "/spear": [4, 2, 0.25], "/axe": [14, 1, 0.5], "/bow": [6, 5, 0.5]}
weaponMultiplier = [1, 1.25, 1.5, 2, 3]
allygroups = []
if not os.path.exists('data'): # sets up the files from scratch
    os.makedirs('data')
    players, items, messages = [], [], []
    grid = createGrid()
    for i in range(16):
        items.append(createItem("common", 'healing'))
        items.append(createItem("common", 'armour'))
        items.append(createItem("common", 'weapon'))
        if i % 2 == 0:
            items.append(createItem("uncommon", 'healing'))
            items.append(createItem("uncommon", 'armour'))
            items.append(createItem("uncommon", 'weapon'))
        if i % 4 == 0:
            items.append(createItem("rare", 'healing'))
            items.append(createItem("rare", 'armour'))
            items.append(createItem("rare", 'weapon'))
        if i % 8 == 0:
            items.append(createItem("epic", 'healing'))
            items.append(createItem("epic", 'armour'))
            items.append(createItem("epic", 'weapon'))
        if i % 16 == 0:
            items.append(createItem("legendary", 'healing'))
            items.append(createItem("legendary", 'armour'))
            items.append(createItem("legendary", 'weapon'))
    open('data/grid.json', 'w').write(jsonpickle.encode(grid))
    open('data/playerinfo.json', 'w').write(jsonpickle.encode(players))
    open('data/itemsinfo.json', 'w').write(jsonpickle.encode(items))
    open('data/messageinfo.json', 'w').write(jsonpickle.encode(messages))
else: # just opens the files
    with open('data/grid.json', 'r') as file:
        grid = jsonpickle.decode(file.read())
    with open('data/playerinfo.json', 'r') as file:
        players = jsonpickle.decode(file.read())
    with open('data/itemsinfo.json', 'r') as file:
        items = jsonpickle.decode(file.read())
    with open('data/messageinfo.json', 'r') as file:
        messages = jsonpickle.decode(file.read())


@app.route("/login")
def login():
    return render_template("login.html", version=identity.__version__, **auth.log_in(
        scopes=app_config.SCOPE, # Have user consent to scopes during log-in
        redirect_uri=url_for("auth_response", _external=True), # Optional. If present, this absolute URL must match your app's redirect_uri registered in Azure Portal
        ))

@app.route(app_config.REDIRECT_PATH)
def auth_response():
    result = auth.complete_log_in(request.args)
    session['username'] = auth.get_user().get('name')
    print(auth.get_user().get('name'))
    return redirect(url_for("index"))

@app.route("/logout")
def logout():
    return redirect(auth.log_out(url_for("index", _external=True)))

@app.route("/")
def index():
    username = session.get('username', 'Guest')
    if not username or username == 'Guest':
        return redirect(url_for("login"))
    client_id = -1
    for i in range(len(players)):
        if username == players[i].name:
            client_id = i
    if client_id == -1:
        players.append(Player(username))
        print(players)
        open('data/playerinfo.json', 'w').write(jsonpickle.encode(players))
        client_id = len(players)-1
    session['ClientID'] = client_id
    print(client_id)
    print(username)
    print(canrun)
    if canrun:
        return render_template('index.html')
    else:
        return render_template('login.html')


@app.route('/help')
def help():
    '''just a plain HTML with an href'''
    return render_template('help.html')


@socketio.on('message')
def handle_message(msg):
    '''emits received message to everyone'''
    name, message = msg[0].split(': ')
    if message[:6] == '/ally ':
        allywith = message[6:]
        if allywith[:7] == 'remove ':
            toremove = allywith[7:]
            toremoveidx=None
            for i in range(len(players)):
                if players[i].name == name:
                    removeridx = i
                elif players[i].name == toremove:
                    toremoveidx = i
            if toremove in players[removeridx].ally:
                players[toremoveidx].ally.remove(name)
                players[removeridx].ally.append(toremove)
                socketio.emit('message',[[f'{name} has revoked their ally with {toremove}']])
            else:
                socketio.emit('message',[[f'You have not allied with {toremove}','black']],room=removeridx)
        elif allywith == 'confirm':
            for i in range(len(allygroups)):
                if allygroups[i][1][0] == name:
                    players[allygroups[i][1][1]].ally.append(allygroups[i][0][0])
                    players[allygroups[i][0][1]].ally.append(allygroups[i][1][0])
                    socketio.emit('message',[[f'{allygroups[i][1][0]} has confirmed your alliance','black']],room=allygroups[i][0][1])
                    socketio.emit('message',[[f'You have confirmed your alliance with {allygroups[i][0][0]}','black']],room=allygroups[i][1][1])
                    allygroups[i][1][0] = None
                    socketio.emit('allies',players[allygroups[i][1][1]].ally, room=players[allygroups[i][1][1]])
                    socketio.emit('allies',players[allygroups[i][0][1]].ally, room=players[allygroups[i][0][1]])
        elif allywith == 'cancel':
            for i in range(len(allygroups)):
                if allygroups[i][1][0] == name:
                    allygroups[i][1][0] = None
        else:
            allywithidx=None
            for i in range(len(players)):
                print(allywith==players[i].name)
                if players[i].name == name:
                    ally2idx = i
                elif players[i].name == allywith:
                    allywithidx = i
            socketio.emit('message',[[datetime.now().strftime('[%H:%M] ')+msg[0],msg[1]]], room = ally2idx)
            if allywithidx!=None:
                socketio.emit('message',[[f'{name} wants to ally with you. Type "/ally confirm" to confirm, /ally cancel to cancel','black']],room = allywithidx)
                socketio.emit('message',[[f'Ally request sent to {allywith}']])
                allygroups.append([[name,ally2idx],[allywith,allywithidx]])
            else:
                socketio.emit('message',[['There is no player of that name','black']],room=ally2idx)
    else:
        msg[0] = datetime.now().strftime("[%H:%M] ")+msg[0]
        messages.append(msg)
        socketio.emit('message', [messages[-1]]) #SIMPLIFY?? may have to change what's emitted by the client
        open('data/messageinfo.json', 'w').write(jsonpickle.encode(messages))


@socketio.on('connect')
def handle_connect():
    # emits everything the client needs and sends a message to everyone that they've joined
    socketio.emit('item_positions', items)
    client_id = session.get('ClientID', 'Guest')
    if players[client_id].hp > 0:
        players[client_id].visible = True
        players[client_id].displayedAnywhere = True
    join_room(client_id)
    socketio.emit('client_id', client_id, room=client_id) # SIMPLIFY the emits
    socketio.emit('base_grid', grid)
    playersInfo = [i.getInfoInString() for i in players if i.displayedAnywhere]
    socketio.emit('specificPlayerInfo', [
                  i.getInfoForSpecificPlayer() for i in players])
    socketio.emit('PlayersInfo', sorted(
        playersInfo, key=lambda x: int(x[2]), reverse=True))
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in players]})
    socketio.emit('message', messages[len(messages)-40:], room=client_id)
    socketio.emit('allies',players[client_id].ally, room=client_id)
    messages.append(
        [f'{datetime.now().strftime("[%H:%M] ")}{players[client_id].name} has joined', "black"])
    socketio.emit('message', [messages[-1]])


@socketio.on('update_position')
def handle_update_position(data):
    '''Gets the function to process it, just emits stuff'''
    players[data['id']].move(data['direction'])
    playersInfo = [i.getInfoInString() for i in players if i.displayedAnywhere]
    socketio.emit('PlayersInfo', sorted(
        playersInfo, key=lambda x: int(x[2]), reverse=True))
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in players]})
    socketio.emit('specificPlayerInfo', [
                  i.getInfoForSpecificPlayer() for i in players])
    open('data/playerinfo.json', 'w').write(jsonpickle.encode(players)) #again SIMPLIFY
    open('data/itemsinfo.json', 'w').write(jsonpickle.encode(items))
    if not canrun:
        socketio.emit('redirect', {'url': '/login'})


if __name__ == '__main__':
    socketio.run(app, debug=True, port='5000')  # LOCALTEST
    # socketio.run(app, debug=True,host='0.0.0.0',allow_unsafe_werkzeug=True, port=443, ssl_context=(app_config.FULL_CHAIN, app_config.PRIV_KEY)) # SERVER