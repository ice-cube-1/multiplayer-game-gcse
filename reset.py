import globalvars
from datetime import datetime, timedelta
import threading
from flasksetup import socketio
from player import Player
from setup import createGrid
from item import Item


def TimeTillRun():
    '''Time until next reset'''
    now = datetime.now()
    scheduled = datetime.combine(
        now.date(), datetime.strptime("02:00", "%H:%M").time())
    if now > scheduled:
        scheduled += timedelta(days=1)
    return (scheduled-now).total_seconds()

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

def resetCheck():
    '''waits in a thread until next reset, then possibly does a weekly one before the daily one'''
    while True:
        threading.Event().wait(TimeTillRun())
        if datetime.today().weekday() == 0:
            weeklyReset()
        dailyReset()

thread = threading.Thread(target=resetCheck)
thread.start()