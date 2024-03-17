import vars
from datetime import datetime, timedelta
import threading
from player import Player
from setup import createGrid
from item import Item


def TimeTillRun() -> float:
    """Time until next reset"""
    now = datetime.now()
    scheduled = datetime.combine(
        now.date(), datetime.strptime("02:00", "%H:%M").time())
    if now > scheduled:
        scheduled += timedelta(days=1)
    return (scheduled-now).total_seconds()


def weeklyReset() -> None:
    """all characters lose all stats etc., only thing that stays is color, username"""
    for i in range(len(vars.players)):
        for j in vars.players[i].items:
            vars.items.append(j)
        store_color = vars.players[i].color
        store_last_move = vars.players[i].last_move  # SIMPLIFY STORES
        vars.players[i] = Player(vars.players[i].name)
        vars.players[i].color = store_color
        vars.players[i].last_move = store_last_move


def dailyReset() -> None:
    """grid regenerates, vars.items on board lose"""
    createGrid()
    old_items = [i for i in vars.items]
    vars.items = []
    for i in old_items:
        vars.items.append(Item(i.rarity, i.type))
    # should they be shown on the leaderboard
    if (datetime.now()-vars.players[i].last_move).total_seconds() > 60*60*24:
        vars.players[i].displayed_anywhere = False
    # SIMPLIFY all of this could go into separate functions
    vars.SOCKETIO.emit('base_grid', vars.grid)
    players_info = [i.getInfoInString() for i in vars.players if i.displayed_anywhere]
    vars.SOCKETIO.emit('specificPlayerInfo', [i.getInfoForSpecificPlayer() for i in vars.players])
    vars.SOCKETIO.emit('PlayersInfo', sorted(players_info, key=lambda x: int(x[2]), reverse=True))
    vars.SOCKETIO.emit('new_positions', {"objects": [i.to_dict() for i in vars.players]})
    vars.messages.append([f'{datetime.now().strftime("[%H:%M] ")}The game has reset overnight', "black"])
    vars.SOCKETIO.emit('message', [vars.messages[-1]])


def resetCheck() -> None:
    """waits in a thread until next reset, then possibly does a weekly one before the daily one"""
    while True:
        threading.Event().wait(TimeTillRun())
        if datetime.today().weekday() == 0:
            weeklyReset()
        dailyReset()


thread = threading.Thread(target=resetCheck)
thread.start()
