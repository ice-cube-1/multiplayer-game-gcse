import vars
from datetime import datetime
import utils

CONSTS = vars.consts()

def message(msg: list[str]) -> None:
    """emits received message to everyone"""
    name, message = msg[0].split(': ')
    if message[:6] == '/ally ':
        ally_with = message[6:]
        if ally_with[:7] == 'remove ':
            to_remove = ally_with[7:]
            to_remove_idx = None
            for i in range(len(vars.players)):
                if vars.players[i].name == name:
                    remover_idx = i
                elif vars.players[i].name == to_remove:
                    to_remove_idx = i
            if to_remove in vars.players[remover_idx].ally:
                vars.players[to_remove_idx].ally.remove(name)
                vars.players[remover_idx].ally.append(to_remove)
                vars.SOCKETIO.emit(
                    'message', [[f'{name} has revoked their ally with {to_remove}']])
            else:
                vars.SOCKETIO.emit(
                    'message', [[f'You have not allied with {to_remove}', 'black']], room=remover_idx)
        elif ally_with == 'confirm':
            for i in range(len(vars.ally_groups)):
                if vars.ally_groups[i][1][0] == name:
                    vars.players[vars.ally_groups[i][1][1]].ally.append(
                        vars.ally_groups[i][0][0])
                    vars.players[vars.ally_groups[i][0][1]].ally.append(
                        vars.ally_groups[i][1][0])
                    vars.SOCKETIO.emit('message', [
                        [f'{vars.ally_groups[i][1][0]} has confirmed your alliance', 'black']],
                                  room=vars.ally_groups[i][0][1])
                    vars.SOCKETIO.emit('message', [
                        [f'You have confirmed your alliance with {vars.ally_groups[i][0][0]}', 'black']],
                                  room=vars.ally_groups[i][1][1])
                    vars.ally_groups[i][1][0] = None
                    vars.SOCKETIO.emit('allies', vars.players[vars.ally_groups[i][1][1]].ally,
                                  room=vars.players[vars.ally_groups[i][1][1]])
                    vars.SOCKETIO.emit('allies', vars.players[vars.ally_groups[i][0][1]].ally,
                                  room=vars.players[vars.ally_groups[i][0][1]])
        elif ally_with == 'cancel':
            for i in range(len(vars.ally_groups)):
                if vars.ally_groups[i][1][0] == name:
                    vars.ally_groups[i][1][0] = None
        else:
            ally_with_idx = None
            for i in range(len(vars.players)):
                if vars.players[i].name == name:
                    ally2idx = i
                elif vars.players[i].name == ally_with:
                    ally_with_idx = i
            vars.SOCKETIO.emit('message', [[datetime.now().strftime(
                '[%H:%M] ') + msg[0], msg[1]]], room=ally2idx)
            if ally_with_idx is not None:
                vars.SOCKETIO.emit('message', [
                    [f'{name} wants to ally with you. Type "/ally confirm" to confirm, /ally cancel to cancel',
                     'black']], room=ally_with_idx)
                vars.SOCKETIO.emit(
                    'message', [[f'Ally request sent to {ally_with}']])
                vars.ally_groups.append(
                    [[name, ally2idx], [ally_with, ally_with_idx]])
            else:
                vars.SOCKETIO.emit(
                    'message', [['There is no player of that name', 'black']], room=ally2idx)
    else:
        msg[0] = datetime.now().strftime("[%H:%M] ") + msg[0]
        vars.messages.append(msg)
        vars.SOCKETIO.emit('message', [vars.messages[-1]])
        utils.saveFiles()


def new_position(data: dict[str, str | int]) -> None:
    """Gets the function to process it, just emits stuff"""
    vars.players[data['id']].move(data['direction'])
    players_info = [i.getInfoInString() for i in vars.players if i.displayed_anywhere]
    vars.SOCKETIO.emit('PlayersInfo', sorted(players_info, key=lambda x: int(x[2]), reverse=True))
    vars.SOCKETIO.emit('new_positions', {"objects": [i.to_dict() for i in vars.players]})
    vars.SOCKETIO.emit('specificPlayerInfo', [i.getInfoForSpecificPlayer() for i in vars.players])
    utils.saveFiles()
    if not vars.can_run:
        vars.SOCKETIO.emit('redirect', {'url': '/login'})


def weapon_upgrade(data: list[int]) -> None:
    player_id = data[1]
    to_upgrade = data[0]
    if vars.players[player_id].items[to_upgrade].rarity != 'legendary':
        upgrade_cost = CONSTS.UPGRADE_COSTS[vars.players[player_id].items[to_upgrade].rarity]
        if upgrade_cost <= vars.players[player_id].coinCount:
            vars.players[player_id].coinCount -= upgrade_cost
            vars.players[player_id].items[to_upgrade].rarity = CONSTS.RARITIES[CONSTS.RARITIES.index(
                vars.players[player_id].items[to_upgrade].rarity) + 1]
            vars.SOCKETIO.emit('new_positions', {"objects": [
                i.to_dict() for i in vars.players]})
            vars.SOCKETIO.emit('specificPlayerInfo', [
                i.getInfoForSpecificPlayer() for i in vars.players])
    utils.saveFiles()
