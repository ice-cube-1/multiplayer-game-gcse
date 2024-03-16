from flasksetup import socketio
import globalvars
from datetime import datetime
import utils


def message(msg):
    '''emits received message to everyone'''
    name, message = msg[0].split(': ')
    if message[:6] == '/ally ':
        allywith = message[6:]
        if allywith[:7] == 'remove ':
            toremove = allywith[7:]
            toremoveidx = None
            for i in range(len(globalvars.players)):
                if globalvars.players[i].name == name:
                    removeridx = i
                elif globalvars.players[i].name == toremove:
                    toremoveidx = i
            if toremove in globalvars.players[removeridx].ally:
                globalvars.players[toremoveidx].ally.remove(name)
                globalvars.players[removeridx].ally.append(toremove)
                socketio.emit(
                    'message', [[f'{name} has revoked their ally with {toremove}']])
            else:
                socketio.emit(
                    'message', [[f'You have not allied with {toremove}', 'black']], room=removeridx)
        elif allywith == 'confirm':
            for i in range(len(globalvars.allygroups)):
                if globalvars.allygroups[i][1][0] == name:
                    globalvars.players[globalvars.allygroups[i][1][1]].ally.append(
                        globalvars.allygroups[i][0][0])
                    globalvars.players[globalvars.allygroups[i][0][1]].ally.append(
                        globalvars.allygroups[i][1][0])
                    socketio.emit('message', [
                                  [f'{globalvars.allygroups[i][1][0]} has confirmed your alliance', 'black']], room=globalvars.allygroups[i][0][1])
                    socketio.emit('message', [
                                  [f'You have confirmed your alliance with {globalvars.allygroups[i][0][0]}', 'black']], room=globalvars.allygroups[i][1][1])
                    globalvars.allygroups[i][1][0] = None
                    socketio.emit('allies', globalvars.players[globalvars.allygroups[i][1]
                                  [1]].ally, room=globalvars.players[globalvars.allygroups[i][1][1]])
                    socketio.emit('allies', globalvars.players[globalvars.allygroups[i][0]
                                  [1]].ally, room=globalvars.players[globalvars.allygroups[i][0][1]])
        elif allywith == 'cancel':
            for i in range(len(globalvars.allygroups)):
                if globalvars.allygroups[i][1][0] == name:
                    globalvars.allygroups[i][1][0] = None
        else:
            allywithidx = None
            for i in range(len(globalvars.players)):
                if globalvars.players[i].name == name:
                    ally2idx = i
                elif globalvars.players[i].name == allywith:
                    allywithidx = i
            socketio.emit('message', [[datetime.now().strftime(
                '[%H:%M] ')+msg[0], msg[1]]], room=ally2idx)
            if allywithidx != None:
                socketio.emit('message', [
                              [f'{name} wants to ally with you. Type "/ally confirm" to confirm, /ally cancel to cancel', 'black']], room=allywithidx)
                socketio.emit(
                    'message', [[f'Ally request sent to {allywith}']])
                globalvars.allygroups.append(
                    [[name, ally2idx], [allywith, allywithidx]])
            else:
                socketio.emit(
                    'message', [['There is no player of that name', 'black']], room=ally2idx)
    else:
        msg[0] = datetime.now().strftime("[%H:%M] ")+msg[0]
        globalvars.messages.append(msg)
        socketio.emit('message', [globalvars.messages[-1]])
        utils.saveFiles()


def new_position(data):
    '''Gets the function to process it, just emits stuff'''
    globalvars.players[data['id']].move(data['direction'])
    playersInfo = [i.getInfoInString()
                   for i in globalvars.players if i.displayedAnywhere]
    socketio.emit('PlayersInfo', sorted(
        playersInfo, key=lambda x: int(x[2]), reverse=True))
    socketio.emit('new_positions', {"objects": [
                  i.to_dict() for i in globalvars.players]})
    socketio.emit('specificPlayerInfo', [
                  i.getInfoForSpecificPlayer() for i in globalvars.players])
    utils.saveFiles()
    if not globalvars.canrun:
        socketio.emit('redirect', {'url': '/login'})


def weapon_upgrade(data):
    playerid = data[1]
    toupgrade = data[0]
    if globalvars.players[playerid].items[toupgrade].rarity != 'legendary':
        upgradecost = globalvars.upgradeCosts[globalvars.players[playerid].items[toupgrade].rarity]
        if upgradecost <= globalvars.players[playerid].coinCount:
            globalvars.players[playerid].coinCount -= upgradecost
            globalvars.players[playerid].items[toupgrade].rarity = globalvars.rarities[globalvars.rarities.index(
                globalvars.players[playerid].items[toupgrade].rarity)+1]
            socketio.emit('new_positions', {"objects": [
                          i.to_dict() for i in globalvars.players]})
            socketio.emit('specificPlayerInfo', [
                          i.getInfoForSpecificPlayer() for i in globalvars.players])
    utils.saveFiles()