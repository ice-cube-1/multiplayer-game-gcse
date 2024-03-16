import global_vars
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
        to_add = ['healing', 'armour', 'weapon']
        for i in range(16):
            [global_vars.items.append(Item("common", i)) for i in to_add]
            if i % 2 == 0:
                [global_vars.items.append(Item("uncommon", i)) for i in to_add]
            if i % 4 == 0:
                [global_vars.items.append(Item("rare", i)) for i in to_add]
            if i % 8 == 0:
                [global_vars.items.append(Item("epic", i)) for i in to_add]
            if i % 16 == 0:
                [global_vars.items.append(Item("legendary", i)) for i in to_add]
        utils.saveFiles()
    else:  # just opens the files
        with open('data/grid.json', 'r') as file:
            global_vars.grid = jsonpickle.decode(file.read())
        with open('data/player_info.json', 'r') as file:
            global_vars.players = jsonpickle.decode(file.read())
        with open('data/items_info.json', 'r') as file:
            global_vars.items = jsonpickle.decode(file.read())
        with open('data/message_info.json', 'r') as file:
            global_vars.messages = jsonpickle.decode(file.read())
    global_vars.coins = [coins.addCoin() for _ in range(100)]
    global_vars.coins.append({'x': 1, 'y': 1})


def createGrid():
    """creates a grid with walls at the edge and in random places"""
    global_vars.grid = [
        [0 for _ in range(global_vars.grid_x)] for _ in range(global_vars.grid_y)]
    for i in range(global_vars.grid_y):
        if i == 0 or i == global_vars.grid_y-1:
            global_vars.grid[i] = [1 for i in range(global_vars.grid_x)]
        else:
            global_vars.grid[i][-1] = 1
            global_vars.grid[i][0] = 1
        for j in range(global_vars.grid_x):
            if randint(0, 9) < 1:
                global_vars.grid[i][j] = 1


startData()
