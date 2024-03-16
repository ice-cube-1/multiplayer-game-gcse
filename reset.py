import global_vars
from datetime import datetime, timedelta
import threading
from flasksetup import socketio
from player import Player
from setup import createGrid
from item import Item


def TimeTillRun():
    """Time until next reset"""
    now = datetime.now()
    scheduled = datetime.combine(
        now.date(), datetime.strptime("02:00", "%H:%M").time())
    if now > scheduled:
        scheduled += timedelta(days=1)
    return (scheduled-now).total_seconds()


def weeklyReset():
    """all characters lose all stats etc., only thing that stays is color, username"""
    for i in range(len(global_vars.players)):
        for j in global_vars.players[i].items:
            global_vars.items.append(j)
        store_color = global_vars.players[i].color
        store_last_move = global_vars.players[i].last_move  # SIMPLIFY STORES
        global_vars.players[i] = Player(global_vars.players[i].name)
        global_vars.players[i].color = store_color
        global_vars.players[i].last_move = store_last_move


def dailyReset():
    """grid regenerates, global_vars.items on board lose"""
    createGrid()
    old_items = [i for i in global_vars.items]
    global_vars.items = []
    for i in old_items:
        global_vars.items.append(Item(i.rarity, i.type))
    # should they be shown on the leaderboard
    if (datetime.now()-global_vars.players[i].last_move).total_seconds() > 60*60*24:
        global_vars.players[i].displayed_anywhere = False
    # SIMPLIFY all of this could go into separate functions
    socketio.emit('base_grid', global_vars.grid)
    players_info = [i.getInfoInString() for i in global_vars.players if i.displayed_anywhere]
    socketio.emit('specificPlayerInfo', [i.getInfoForSpecificPlayer() for i in global_vars.players])
    socketio.emit('PlayersInfo', sorted(players_info, key=lambda x: int(x[2]), reverse=True))
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in global_vars.players]})
    global_vars.messages.append([f'{datetime.now().strftime("[%H:%M] ")}The game has reset overnight', "black"])
    socketio.emit('message', [global_vars.messages[-1]])


def resetCheck():
    """waits in a thread until next reset, then possibly does a weekly one before the daily one"""
    while True:
        threading.Event().wait(TimeTillRun())
        if datetime.today().weekday() == 0:
            weeklyReset()
        dailyReset()


thread = threading.Thread(target=resetCheck)
thread.start()
