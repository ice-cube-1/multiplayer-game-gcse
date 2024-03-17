import vars
from random import randint
import os
from item import Item
import utils
import jsonpickle
import coins

CONSTS = vars.consts()


def startData() -> None:
    if not os.path.exists('data'):  # sets up the files from scratch
        os.makedirs('data')
        createGrid()
        to_add = ['healing', 'armour', 'weapon']
        for i in range(16):
            [vars.items.append(Item("common", i)) for i in to_add]
            if i % 2 == 0:
                [vars.items.append(Item("uncommon", i)) for i in to_add]
            if i % 4 == 0:
                [vars.items.append(Item("rare", i)) for i in to_add]
            if i % 8 == 0:
                [vars.items.append(Item("epic", i)) for i in to_add]
            if i % 16 == 0:
                [vars.items.append(Item("legendary", i)) for i in to_add]
        utils.saveFiles()
    else:  # just opens the files
        with open('data/grid.json', 'r') as file:
            vars.grid = jsonpickle.decode(file.read())
        with open('data/player_info.json', 'r') as file:
            vars.players = jsonpickle.decode(file.read())
        with open('data/items_info.json', 'r') as file:
            vars.items = jsonpickle.decode(file.read())
        with open('data/message_info.json', 'r') as file:
            vars.messages = jsonpickle.decode(file.read())
    vars.coins = [coins.addCoin() for _ in range(100)]
    vars.coins.append({'x': 1, 'y': 1})


def createGrid() -> None:
    """creates a grid with walls at the edge and in random places"""
    vars.grid = [
        [0 for _ in range(CONSTS.GRID_X)] for _ in range(CONSTS.GRID_Y)]
    for i in range(CONSTS.GRID_Y):
        if i == 0 or i == CONSTS.GRID_Y-1:
            vars.grid[i] = [1 for i in range(CONSTS.GRID_X)]
        else:
            vars.grid[i][-1] = 1
            vars.grid[i][0] = 1
        for j in range(CONSTS.GRID_X):
            if randint(0, 9) < 1:
                vars.grid[i][j] = 1


startData()
