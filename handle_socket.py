import vars
from datetime import datetime
import utils


def message(global_vars: vars.GLOBAL, msg: list[str]) -> None:
    """processes ally requests by sending out a confirmation, and then adding when confirmed / deleting the option if removed
    also can remove allies without confirmation
    if message does not start with /ally will just output to everyone"""
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
                with global_vars.globals_lock: 
                    global_vars.players[to_remove_idx].ally.remove(name)
                    global_vars.players[remover_idx].ally.append(to_remove)
                global_vars.SOCKETIO.emit(
                    'message', [[f'{name} has revoked their ally with {to_remove}']])
            else:
                global_vars.SOCKETIO.emit(
                    'message', [[f'You have not allied with {to_remove}', 'black']], room=remover_idx)
        elif ally_with == 'confirm':
            for i in range(len(global_vars.ally_groups)):
                if global_vars.ally_groups[i][1][0] == name:
                    with global_vars.globals_lock: 
                        global_vars.players[global_vars.ally_groups[i][1][1]].ally.append(
                            global_vars.ally_groups[i][0][0])
                        global_vars.players[global_vars.ally_groups[i][0][1]].ally.append(
                            global_vars.ally_groups[i][1][0])
                    global_vars.SOCKETIO.emit('message', [
                        [f'{global_vars.ally_groups[i][1][0]} has confirmed your alliance', 'black']],
                                          room=global_vars.ally_groups[i][0][1])
                    global_vars.SOCKETIO.emit('message', [
                        [f'You have confirmed your alliance with {global_vars.ally_groups[i][0][0]}', 'black']],
                                          room=global_vars.ally_groups[i][1][1])
                    with global_vars.globals_lock: global_vars.ally_groups[i][1][0] = None
                    global_vars.SOCKETIO.emit('allies', global_vars.players[global_vars.ally_groups[i][1][1]].ally,
                                          room=global_vars.players[global_vars.ally_groups[i][1][1]])
                    global_vars.SOCKETIO.emit('allies', global_vars.players[global_vars.ally_groups[i][0][1]].ally,
                                          room=global_vars.players[global_vars.ally_groups[i][0][1]])
        elif ally_with == 'cancel':
            for i in range(len(global_vars.ally_groups)):
                if global_vars.ally_groups[i][1][0] == name:
                    with global_vars.globals_lock: global_vars.ally_groups[i][1][0] = None
        else:
            ally_with_idx = None
            for i in range(len(global_vars.players)):
                if global_vars.players[i].name == name:
                    ally2idx = i
                elif global_vars.players[i].name == ally_with:
                    ally_with_idx = i
            global_vars.SOCKETIO.emit('message', [[datetime.now().strftime(
                '[%H:%M] ') + msg[0], msg[1]]], room=ally2idx)
            if ally_with_idx is not None:
                global_vars.SOCKETIO.emit('message', [
                    [f'{name} wants to ally with you. Type "/ally confirm" to confirm, /ally cancel to cancel',
                     'black']], room=ally_with_idx)
                global_vars.SOCKETIO.emit(
                    'message', [[f'Ally request sent to {ally_with}']])
                with global_vars.globals_lock: global_vars.ally_groups.append(
                    [[name, ally2idx], [ally_with, ally_with_idx]])
            else:
                global_vars.SOCKETIO.emit(
                    'message', [['There is no player of that name', 'black']], room=ally2idx)
    else:
        msg[0] = datetime.now().strftime("[%H:%M] ") + msg[0]
        with global_vars.globals_lock: global_vars.messages.append(msg)
        global_vars.SOCKETIO.emit('message', [global_vars.messages[-1]])
        utils.saveFiles(global_vars)


def new_position(global_vars: vars.GLOBAL, data: dict[str, str | int]) -> None:
    """handled properly in the player class, but 'moves' the correct player and emits the results to everyone - 
    also will redirect back to login page if game should have gone offline since last connect"""
    global_vars.players[data['id']].move(global_vars, data['direction'])
    players_info = [i.getInfoInString() for i in global_vars.players if i.displayed_anywhere]
    global_vars.SOCKETIO.emit('PlayersInfo', sorted(players_info, key=lambda x: int(x[2]), reverse=True))
    global_vars.SOCKETIO.emit('new_positions', {"objects": [i.to_dict() for i in global_vars.players]})
    global_vars.SOCKETIO.emit('specificPlayerInfo', [i.getInfoForSpecificPlayer() for i in global_vars.players])
    utils.saveFiles(global_vars)
    if not global_vars.can_run:
        global_vars.SOCKETIO.emit('redirect', {'url': '/login'})


def weapon_upgrade(global_vars: vars.GLOBAL, data: list[int]) -> None:
    """if can upgreade weapon (have enough coins and not already legendary) does so and emits the result"""
    player_id = data[1]
    to_upgrade = data[0]
    if global_vars.players[player_id].items[to_upgrade].rarity != 'legendary':
        upgrade_cost = vars.UPGRADE_COSTS[global_vars.players[player_id].items[to_upgrade].rarity]
        if upgrade_cost <= global_vars.players[player_id].coinCount:
            with global_vars.globals_lock: 
                global_vars.players[player_id].coinCount -= upgrade_cost
                global_vars.players[player_id].items[to_upgrade].rarity = vars.RARITIES[vars.RARITIES.index(
                    global_vars.players[player_id].items[to_upgrade].rarity) + 1]
            global_vars.SOCKETIO.emit('new_positions', {"objects": [
                i.to_dict() for i in global_vars.players]})
            global_vars.SOCKETIO.emit('specificPlayerInfo', [
                i.getInfoForSpecificPlayer() for i in global_vars.players])
    utils.saveFiles(global_vars)
