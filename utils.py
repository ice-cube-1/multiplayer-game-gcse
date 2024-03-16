from random import randint
import globalvars
import jsonpickle


def rollDice(sides, number):
    '''Returns sum of NdX dice (can be .25)'''
    return sum([randint(1, sides) for i in range(int(number*4))])//4


def saveFiles():
    open('data/itemsinfo.json','w').write(jsonpickle.encode(globalvars.items))
    open('data/grid.json','w').write(jsonpickle.encode(globalvars.grid))
    open('data/messageinfo.json','w').write(jsonpickle.encode(globalvars.messages))
    open('data/playerinfo.json','w').write(jsonpickle.encode(globalvars.players))