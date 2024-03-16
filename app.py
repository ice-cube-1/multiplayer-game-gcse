from random import randint, choice
from flask import Flask, render_template, request, redirect, url_for, session
from flask_socketio import SocketIO, join_room
from flask_cors import CORS
from datetime import datetime, timedelta
import jsonpickle
import os
import threading
from werkzeug.middleware.proxy_fix import ProxyFix
import identity
import identity.web
from flask_session import Session
import app_config
from player import Player
from item import Item
#from globalvars import globalvars.gridlx, globalvars.gridly, globalvars.allygroups, globalvars.rarities, globalvars.upgradeCosts
import globalvars
import coins

def zombify():
    '''Checks if there are any globalvars.players that should be offline and if so makes them invisible'''
    currentTime = datetime.now()
    with zombifyLock:
        for i in range(len(globalvars.players)):
            delta = currentTime - globalvars.players[i].lastMove
            if delta.total_seconds() > 120 and globalvars.players[i].visible:
                globalvars.players[i].visible = False
                globalvars.messages.append(
                    [f'{datetime.now().strftime("[%H:%M] ")}{globalvars.players[i].name} has gone offline', "black"])
                socketio.emit('message', [globalvars.messages[-1]])
        socketio.emit('new_positions', {"objects": [
                      i.to_dict() for i in globalvars.players]})
        playersInfo = [i.getInfoInString()
                       for i in globalvars.players if i.displayedAnywhere]
        socketio.emit('PlayersInfo', sorted(
            playersInfo, key=lambda x: int(x[2]), reverse=True))


def createGrid():
    '''creates a grid with walls at the edge and in random places'''
    globalvars.grid = [[0 for i in range(globalvars.gridlx)] for j in range(globalvars.gridly)]
    for i in range(globalvars.gridly):
        if i == 0 or i == globalvars.gridly-1:
            globalvars.grid[i] = [1 for i in range(globalvars.gridlx)]
        else:
            globalvars.grid[i][-1] = 1
            globalvars.grid[i][0] = 1
        for j in range(globalvars.gridlx):
            if randint(0, 9) < 1:
                globalvars.grid[i][j] = 1

def weeklyReset():
    '''all characters lose all stats etc, only thing that stays is color, username'''
    for i in range(len(globalvars.players)):
        for j in globalvars.players[i].items:
            globalvars.items.append(j)
        storeColor = globalvars.players[i].color
        storelastmove = globalvars.players[i].lastMove  # SIMPLIFY STORES
        globalvars.players[i] = Player(globalvars.players[i].name)
        globalvars.players[i].color = storeColor
        globalvars.players[i].lastMove = storelastmove


def dailyReset():
    '''grid regeneates, globalvars.items on board lose'''
    createGrid()
    olditems = [i for i in globalvars.items]
    globalvars.items = []
    for i in olditems:
        globalvars.items.append(Item(i.rarity, i.type))
    # should they be shown on the leaderboard
    if (datetime.now()-globalvars.players[i].lastMove).total_seconds() > 60*60*24:
        globalvars.players[i].displayedAnywhere = False
    # SIMPLIFY all of this could go into separate functions
    socketio.emit('base_grid', globalvars.grid)
    playersInfo = [i.getInfoInString() for i in globalvars.players if i.displayedAnywhere]
    socketio.emit('specificPlayerInfo', [
                  i.getInfoForSpecificPlayer() for i in globalvars.players])
    socketio.emit('PlayersInfo', sorted(
        playersInfo, key=lambda x: int(x[2]), reverse=True))
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in globalvars.players]})
    globalvars.messages.append(
        [f'{datetime.now().strftime("[%H:%M] ")}The game has reset overnight', "black"])
    socketio.emit('message', [globalvars.messages[-1]])


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
if not os.path.exists('data'): # sets up the files from scratch
    os.makedirs('data')
    createGrid()
    toadd=['healing','armour','weapon']
    for i in range(16):
        [globalvars.items.append(Item("common", i)) for i in toadd]
        if i % 2 == 0:
            [globalvars.items.append(Item("uncommon", i)) for i in toadd]
        if i % 4 == 0:
            [globalvars.items.append(Item("rare", i)) for i in toadd]
        if i % 8 == 0:
            [globalvars.items.append(Item("epic", i)) for i in toadd]
        if i % 16 == 0:
            [globalvars.items.append(Item("legendary", i)) for i in toadd]
    open('data/grid.json', 'w').write(jsonpickle.encode(globalvars.grid))
    open('data/playerinfo.json', 'w').write(jsonpickle.encode(globalvars.players))
    open('data/itemsinfo.json', 'w').write(jsonpickle.encode(globalvars.items))
    open('data/messageinfo.json', 'w').write(jsonpickle.encode(globalvars.messages))
else: # just opens the files
    with open('data/grid.json', 'r') as file:
        globalvars.grid = jsonpickle.decode(file.read())
    with open('data/playerinfo.json', 'r') as file:
        globalvars.players = jsonpickle.decode(file.read())
    with open('data/itemsinfo.json', 'r') as file:
        globalvars.items = jsonpickle.decode(file.read())
    with open('data/messageinfo.json', 'r') as file:
        globalvars.messages = jsonpickle.decode(file.read())
coins=[coins.addCoin() for i in range(100)]
coins.append({'x':1,'y':1})

@app.route("/login")
def login():
    return render_template("login.html", version=identity.__version__, **auth.log_in(
        scopes=app_config.SCOPE, # Have user consent to scopes during log-in
        redirect_uri=url_for("auth_response", _external=True), # Optional. If present, this absolute URL must match your app's redirect_uri registered in Azure Portal
        ))

@app.route(app_config.REDIRECT_PATH)
def auth_response():
    auth.complete_log_in(request.args)
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
    for i in range(len(globalvars.players)):
        if username == globalvars.players[i].name:
            client_id = i
    if client_id == -1:
        globalvars.players.append(Player(username))
        open('data/playerinfo.json', 'w').write(jsonpickle.encode(globalvars.players))
        client_id = len(globalvars.players)-1
    session['ClientID'] = client_id
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
            for i in range(len(globalvars.players)):
                if globalvars.players[i].name == name:
                    removeridx = i
                elif globalvars.players[i].name == toremove:
                    toremoveidx = i
            if toremove in globalvars.players[removeridx].ally:
                globalvars.players[toremoveidx].ally.remove(name)
                globalvars.players[removeridx].ally.append(toremove)
                socketio.emit('message',[[f'{name} has revoked their ally with {toremove}']])
            else:
                socketio.emit('message',[[f'You have not allied with {toremove}','black']],room=removeridx)
        elif allywith == 'confirm':
            for i in range(len(globalvars.allygroups)):
                if globalvars.allygroups[i][1][0] == name:
                    globalvars.players[globalvars.allygroups[i][1][1]].ally.append(globalvars.allygroups[i][0][0])
                    globalvars.players[globalvars.allygroups[i][0][1]].ally.append(globalvars.allygroups[i][1][0])
                    socketio.emit('message',[[f'{globalvars.allygroups[i][1][0]} has confirmed your alliance','black']],room=globalvars.allygroups[i][0][1])
                    socketio.emit('message',[[f'You have confirmed your alliance with {globalvars.allygroups[i][0][0]}','black']],room=globalvars.allygroups[i][1][1])
                    globalvars.allygroups[i][1][0] = None
                    socketio.emit('allies',globalvars.players[globalvars.allygroups[i][1][1]].ally, room=globalvars.players[globalvars.allygroups[i][1][1]])
                    socketio.emit('allies',globalvars.players[globalvars.allygroups[i][0][1]].ally, room=globalvars.players[globalvars.allygroups[i][0][1]])
        elif allywith == 'cancel':
            for i in range(len(globalvars.allygroups)):
                if globalvars.allygroups[i][1][0] == name:
                    globalvars.allygroups[i][1][0] = None
        else:
            allywithidx=None
            for i in range(len(globalvars.players)):
                if globalvars.players[i].name == name:
                    ally2idx = i
                elif globalvars.players[i].name == allywith:
                    allywithidx = i
            socketio.emit('message',[[datetime.now().strftime('[%H:%M] ')+msg[0],msg[1]]], room = ally2idx)
            if allywithidx!=None:
                socketio.emit('message',[[f'{name} wants to ally with you. Type "/ally confirm" to confirm, /ally cancel to cancel','black']],room = allywithidx)
                socketio.emit('message',[[f'Ally request sent to {allywith}']])
                globalvars.allygroups.append([[name,ally2idx],[allywith,allywithidx]])
            else:
                socketio.emit('message',[['There is no player of that name','black']],room=ally2idx)
    else:
        msg[0] = datetime.now().strftime("[%H:%M] ")+msg[0]
        globalvars.messages.append(msg)
        socketio.emit('message', [globalvars.messages[-1]]) #SIMPLIFY?? may have to change what's emitted by the client
        open('data/messageinfo.json', 'w').write(jsonpickle.encode(globalvars.messages))


@socketio.on('connect')
def handle_connect():
    # emits everything the client needs and sends a message to everyone that they've joined
    socketio.emit('item_positions', [i.to_dict() for i in globalvars.items])
    client_id = session.get('ClientID', 'Guest')
    if globalvars.players[client_id].hp > 0:
        globalvars.players[client_id].visible = True
        globalvars.players[client_id].displayedAnywhere = True
    join_room(client_id)
    socketio.emit('coin_positions',coins)
    socketio.emit('client_id', client_id, room=client_id) # SIMPLIFY the emits
    socketio.emit('base_grid', globalvars.grid)
    playersInfo = [i.getInfoInString() for i in globalvars.players if i.displayedAnywhere]
    socketio.emit('specificPlayerInfo', [
                  i.getInfoForSpecificPlayer() for i in globalvars.players])
    socketio.emit('PlayersInfo', sorted(
        playersInfo, key=lambda x: int(x[2]), reverse=True))
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in globalvars.players]})
    socketio.emit('message', globalvars.messages[len(globalvars.messages)-40:], room=client_id)
    socketio.emit('allies',globalvars.players[client_id].ally, room=client_id)
    globalvars.messages.append(
        [f'{datetime.now().strftime("[%H:%M] ")}{globalvars.players[client_id].name} has joined', "black"])
    socketio.emit('message', [globalvars.messages[-1]])


@socketio.on('update_position')
def handle_update_position(data):
    '''Gets the function to process it, just emits stuff'''
    globalvars.players[data['id']].move(data['direction'])
    playersInfo = [i.getInfoInString() for i in globalvars.players if i.displayedAnywhere]
    socketio.emit('PlayersInfo', sorted(
        playersInfo, key=lambda x: int(x[2]), reverse=True))
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in globalvars.players]})
    socketio.emit('specificPlayerInfo', [
                  i.getInfoForSpecificPlayer() for i in globalvars.players])
    open('data/playerinfo.json', 'w').write(jsonpickle.encode(globalvars.players)) #again SIMPLIFY
    open('data/itemsinfo.json', 'w').write(jsonpickle.encode(globalvars.items))
    if not canrun:
        socketio.emit('redirect', {'url': '/login'})

@socketio.on('upgrade_weapon')
def handle_upgrade_weapon(data):
    print('test')
    playerid=data[1]
    toupgrade=data[0]
    if globalvars.players[playerid].items[toupgrade].rarity!='legendary':
        upgradecost=globalvars.upgradeCosts[globalvars.players[playerid].items[toupgrade].rarity]
        if upgradecost<=globalvars.players[playerid].coinCount :
            globalvars.players[playerid].coinCount-=upgradecost
            globalvars.players[playerid].items[toupgrade].rarity = globalvars.rarities[globalvars.rarities.index(globalvars.players[playerid].items[toupgrade].rarity)+1]
            socketio.emit('new_positions', {"objects": [i.to_dict() for i in globalvars.players]})
            socketio.emit('specificPlayerInfo', [i.getInfoForSpecificPlayer() for i in globalvars.players])
    print(playerid,toupgrade)

if __name__ == '__main__':
    socketio.run(app, debug=True, port='5000')  # LOCALTEST
    # socketio.run(app, debug=True,host='0.0.0.0',allow_unsafe_werkzeug=True, port=443, ssl_context=(app_config.FULL_CHAIN, app_config.PRIV_KEY)) # SERVER