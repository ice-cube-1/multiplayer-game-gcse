from datetime import datetime
import threading
import vars


def zombify() -> None:
    '''Checks if there are any vars.players that should be offline and if so makes them invisible'''
    currentTime = datetime.now()
    with zombifyLock:
        for i in range(len(vars.players)):
            delta = currentTime - vars.players[i].last_move
            if delta.total_seconds() > 120 and vars.players[i].visible:
                vars.players[i].visible = False
                vars.messages.append(
                    [f'{datetime.now().strftime("[%H:%M] ")}{vars.players[i].name} has gone offline', "black"])
                vars.SOCKETIO.emit('message', [vars.messages[-1]])
        vars.SOCKETIO.emit('new_positions', {"objects": [
                      i.to_dict() for i in vars.players]})
        playersInfo = [i.getInfoInString()
                       for i in vars.players if i.displayed_anywhere]
        vars.SOCKETIO.emit('PlayersInfo', sorted(
            playersInfo, key=lambda x: int(x[2]), reverse=True))


def waitZombify() -> None:
    '''waits between offline checks'''
    while True:
        threading.Event().wait(5)
        zombify()


zombifyThread = threading.Thread(target=waitZombify)
zombifyThread.start()
zombifyLock = threading.Lock()
