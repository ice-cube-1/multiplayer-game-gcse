from datetime import datetime
import threading
import vars


def zombify(global_vars: vars.GLOBAL) -> None:
    """Checks if there are any players that should be offline and if so makes them invisible"""
    currentTime = datetime.now()
    for i in range(len(global_vars.players)):
        delta = currentTime - global_vars.players[i].last_move
        if delta.total_seconds() > 120 and global_vars.players[i].visible:
            with global_vars.globals_lock:
                global_vars.players[i].visible = False
                global_vars.messages.append(
                    [f'{datetime.now().strftime("[%H:%M] ")}{global_vars.players[i].name} has gone offline', "black"])
            global_vars.SOCKETIO.emit(
                'message', [global_vars.messages[-1]])
    global_vars.SOCKETIO.emit('new_positions', {"objects": [
        i.to_dict() for i in global_vars.players]})
    playersInfo = [i.getInfoInString()
                    for i in global_vars.players if i.displayed_anywhere]
    global_vars.SOCKETIO.emit('PlayersInfo', sorted(
        playersInfo, key=lambda x: int(x[2]), reverse=True))


def waitZombify(global_vars: vars.GLOBAL) -> None:
    """waits between offline checks"""
    while True:
        threading.Event().wait(5)
        zombify(global_vars)


def start(global_vars: vars.GLOBAL):
    """initialises zombie thread and the lock"""
    zombifyThread = threading.Thread(
        target=waitZombify, args=(global_vars,))
    zombifyThread.start()
