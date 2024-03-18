from random import randint
import jsonpickle
import vars


def rollDice(sides: int, number: float) -> int:
    '''Returns sum of NdX dice (can be .25)'''
    return sum([randint(1, sides) for i in range(int(number*4))])//4


def saveFiles(global_vars: vars.GLOBAL) -> None:
    open('data/items_info.json', 'w').write(jsonpickle.encode(global_vars.items))
    open('data/grid.json','w').write(jsonpickle.encode(global_vars.grid))
    open('data/message_info.json', 'w').write(jsonpickle.encode(global_vars.messages))
    open('data/player_info.json', 'w').write(jsonpickle.encode(global_vars.players))