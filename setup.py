import globalvars
from random import randint

def createGrid():
    '''creates a grid with walls at the edge and in random places'''
    globalvars.grid = [[0 for i in range(globalvars.gridlx)] for j in range(globalvars.gridly)]
    for i in range(globalvars.gridly):
        if i == 0 or i == globalvars.gridly-1:
            globalvars.grid[i] = [1 for i in range(globalvars.gridlx)]
        else:
            globalvars.grid[i][-1] = 1
            globalvars.grid[i][0] = 1
        for j in range(globalvars.gridlx):
            if randint(0, 9) < 1:
                globalvars.grid[i][j] = 1