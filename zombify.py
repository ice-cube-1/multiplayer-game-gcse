from datetime import datetime
import globalvars
import threading
import socketio

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


def waitZombify():
    '''waits between offline checks'''
    while True:
        threading.Event().wait(5)
        print('zombiee')
        zombify()

zombifyThread = threading.Thread(target=waitZombify)
zombifyThread.start()
zombifyLock = threading.Lock()