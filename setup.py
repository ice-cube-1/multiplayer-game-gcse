import globalvars
from random import randint
import os
from item import Item
import utils
import jsonpickle
import coins


def startData():
    if not os.path.exists('data'):  # sets up the files from scratch
        os.makedirs('data')
        createGrid()
        toadd = ['healing', 'armour', 'weapon']
        for i in range(16):
            [globalvars.items.append(Item("common", i)) for i in toadd]
            if i % 2 == 0:
                [globalvars.items.append(Item("uncommon", i)) for i in toadd]
            if i % 4 == 0:
                [globalvars.items.append(Item("rare", i)) for i in toadd]
            if i % 8 == 0:
                [globalvars.items.append(Item("epic", i)) for i in toadd]
            if i % 16 == 0:
                [globalvars.items.append(Item("legendary", i)) for i in toadd]
        utils.saveFiles()
    else:  # just opens the files
        with open('data/grid.json', 'r') as file:
            globalvars.grid = jsonpickle.decode(file.read())
        with open('data/playerinfo.json', 'r') as file:
            globalvars.players = jsonpickle.decode(file.read())
        with open('data/itemsinfo.json', 'r') as file:
            globalvars.items = jsonpickle.decode(file.read())
        with open('data/messageinfo.json', 'r') as file:
            globalvars.messages = jsonpickle.decode(file.read())
    globalvars.coins = [coins.addCoin() for i in range(100)]
    globalvars.coins.append({'x': 1, 'y': 1})


def createGrid():
    '''creates a grid with walls at the edge and in random places'''
    globalvars.grid = [
        [0 for i in range(globalvars.gridlx)] for j in range(globalvars.gridly)]
    for i in range(globalvars.gridly):
        if i == 0 or i == globalvars.gridly-1:
            globalvars.grid[i] = [1 for i in range(globalvars.gridlx)]
        else:
            globalvars.grid[i][-1] = 1
            globalvars.grid[i][0] = 1
        for j in range(globalvars.gridlx):
            if randint(0, 9) < 1:
                globalvars.grid[i][j] = 1


startData()
