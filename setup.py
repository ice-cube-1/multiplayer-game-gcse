import vars
from random import randint
import os
from item import Item
import utils
import jsonpickle
import coins


def start(global_vars: vars.GLOBAL) -> None:
    """if directory 'data' exists then loads the files, otherwise creates new map / items and saves them"""
    if not os.path.exists('data'):
        os.makedirs('data')
        createGrid(global_vars)
        to_add = ['healing', 'armour', 'weapon']
        for i in range(16):
            [global_vars.items.append(
                Item(global_vars, "common", i)) for i in to_add]
            if i % 2 == 0:
                [global_vars.items.append(
                    Item(global_vars, "uncommon", i)) for i in to_add]
            if i % 4 == 0:
                [global_vars.items.append(
                    Item(global_vars, "rare", i)) for i in to_add]
            if i % 8 == 0:
                [global_vars.items.append(
                    Item(global_vars, "epic", i)) for i in to_add]
            if i % 16 == 0:
                [global_vars.items.append(
                    Item(global_vars, "legendary", i)) for i in to_add]
        utils.saveFiles(global_vars)
    else:
        with open('data/grid.json', 'r') as file:
            global_vars.grid = jsonpickle.decode(file.read())
        with open('data/player_info.json', 'r') as file:
            global_vars.players = jsonpickle.decode(file.read())
        with open('data/items_info.json', 'r') as file:
            global_vars.items = jsonpickle.decode(file.read())
        with open('data/message_info.json', 'r') as file:
            global_vars.messages = jsonpickle.decode(file.read())
    global_vars.coins = [coins.addCoin(global_vars) for _ in range(100)]
    global_vars.coins.append({'x': 1, 'y': 1})


def createGrid(global_vars: vars.GLOBAL) -> None:
    """creates a grid with walls at the edge and in random places"""
    global_vars.grid = [
        [0 for _ in range(vars.GRID_X)] for _ in range(vars.GRID_Y)]
    for i in range(vars.GRID_Y):
        if i == 0 or i == vars.GRID_Y-1:
            global_vars.grid[i] = [1 for i in range(vars.GRID_X)]
        else:
            global_vars.grid[i][-1] = 1
            global_vars.grid[i][0] = 1
        for j in range(vars.GRID_X):
            if randint(0, 9) < 1:
                global_vars.grid[i][j] = 1
