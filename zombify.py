from datetime import datetime
import global_vars
import threading
from flasksetup import socketio


def zombify():
    '''Checks if there are any global_vars.players that should be offline and if so makes them invisible'''
    currentTime = datetime.now()
    with zombifyLock:
        for i in range(len(global_vars.players)):
            delta = currentTime - global_vars.players[i].last_move
            if delta.total_seconds() > 120 and global_vars.players[i].visible:
                global_vars.players[i].visible = False
                global_vars.messages.append(
                    [f'{datetime.now().strftime("[%H:%M] ")}{global_vars.players[i].name} has gone offline', "black"])
                socketio.emit('message', [global_vars.messages[-1]])
        socketio.emit('new_positions', {"objects": [
                      i.to_dict() for i in global_vars.players]})
        playersInfo = [i.getInfoInString()
                       for i in global_vars.players if i.displayed_anywhere]
        socketio.emit('PlayersInfo', sorted(
            playersInfo, key=lambda x: int(x[2]), reverse=True))


def waitZombify():
    '''waits between offline checks'''
    while True:
        threading.Event().wait(5)
        zombify()


zombifyThread = threading.Thread(target=waitZombify)
zombifyThread.start()
zombifyLock = threading.Lock()
