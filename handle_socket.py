from flasksetup import socketio
import global_vars
from datetime import datetime
import utils


def message(msg):
    """emits received message to everyone"""
    name, message = msg[0].split(': ')
    if message[:6] == '/ally ':
        ally_with = message[6:]
        if ally_with[:7] == 'remove ':
            to_remove = ally_with[7:]
            to_remove_idx = None
            for i in range(len(global_vars.players)):
                if global_vars.players[i].name == name:
                    remover_idx = i
                elif global_vars.players[i].name == to_remove:
                    to_remove_idx = i
            if to_remove in global_vars.players[remover_idx].ally:
                global_vars.players[to_remove_idx].ally.remove(name)
                global_vars.players[remover_idx].ally.append(to_remove)
                socketio.emit(
                    'message', [[f'{name} has revoked their ally with {to_remove}']])
            else:
                socketio.emit(
                    'message', [[f'You have not allied with {to_remove}', 'black']], room=remover_idx)
        elif ally_with == 'confirm':
            for i in range(len(global_vars.ally_groups)):
                if global_vars.ally_groups[i][1][0] == name:
                    global_vars.players[global_vars.ally_groups[i][1][1]].ally.append(
                        global_vars.ally_groups[i][0][0])
                    global_vars.players[global_vars.ally_groups[i][0][1]].ally.append(
                        global_vars.ally_groups[i][1][0])
                    socketio.emit('message', [
                        [f'{global_vars.ally_groups[i][1][0]} has confirmed your alliance', 'black']],
                                  room=global_vars.ally_groups[i][0][1])
                    socketio.emit('message', [
                        [f'You have confirmed your alliance with {global_vars.ally_groups[i][0][0]}', 'black']],
                                  room=global_vars.ally_groups[i][1][1])
                    global_vars.ally_groups[i][1][0] = None
                    socketio.emit('allies', global_vars.players[global_vars.ally_groups[i][1][1]].ally,
                                  room=global_vars.players[global_vars.ally_groups[i][1][1]])
                    socketio.emit('allies', global_vars.players[global_vars.ally_groups[i][0][1]].ally,
                                  room=global_vars.players[global_vars.ally_groups[i][0][1]])
        elif ally_with == 'cancel':
            for i in range(len(global_vars.ally_groups)):
                if global_vars.ally_groups[i][1][0] == name:
                    global_vars.ally_groups[i][1][0] = None
        else:
            ally_with_idx = None
            for i in range(len(global_vars.players)):
                if global_vars.players[i].name == name:
                    ally2idx = i
                elif global_vars.players[i].name == ally_with:
                    ally_with_idx = i
            socketio.emit('message', [[datetime.now().strftime(
                '[%H:%M] ') + msg[0], msg[1]]], room=ally2idx)
            if ally_with_idx is not None:
                socketio.emit('message', [
                    [f'{name} wants to ally with you. Type "/ally confirm" to confirm, /ally cancel to cancel',
                     'black']], room=ally_with_idx)
                socketio.emit(
                    'message', [[f'Ally request sent to {ally_with}']])
                global_vars.ally_groups.append(
                    [[name, ally2idx], [ally_with, ally_with_idx]])
            else:
                socketio.emit(
                    'message', [['There is no player of that name', 'black']], room=ally2idx)
    else:
        msg[0] = datetime.now().strftime("[%H:%M] ") + msg[0]
        global_vars.messages.append(msg)
        socketio.emit('message', [global_vars.messages[-1]])
        utils.saveFiles()


def new_position(data):
    """Gets the function to process it, just emits stuff"""
    global_vars.players[data['id']].move(data['direction'])
    players_info = [i.getInfoInString() for i in global_vars.players if i.displayed_anywhere]
    socketio.emit('PlayersInfo', sorted(players_info, key=lambda x: int(x[2]), reverse=True))
    socketio.emit('new_positions', {"objects": [i.to_dict() for i in global_vars.players]})
    socketio.emit('specificPlayerInfo', [i.getInfoForSpecificPlayer() for i in global_vars.players])
    utils.saveFiles()
    if not global_vars.can_run:
        socketio.emit('redirect', {'url': '/login'})


def weapon_upgrade(data):
    player_id = data[1]
    to_upgrade = data[0]
    if global_vars.players[player_id].items[to_upgrade].rarity != 'legendary':
        upgrade_cost = global_vars.upgradeCosts[global_vars.players[player_id].items[to_upgrade].rarity]
        if upgrade_cost <= global_vars.players[player_id].coinCount:
            global_vars.players[player_id].coinCount -= upgrade_cost
            global_vars.players[player_id].items[to_upgrade].rarity = global_vars.rarities[global_vars.rarities.index(
                global_vars.players[player_id].items[to_upgrade].rarity) + 1]
            socketio.emit('new_positions', {"objects": [
                i.to_dict() for i in global_vars.players]})
            socketio.emit('specificPlayerInfo', [
                i.getInfoForSpecificPlayer() for i in global_vars.players])
    utils.saveFiles()
