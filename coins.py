from random import randint
#from globalvars import items, grid
import globalvars

def addCoin():
    x,y=0,0
    while True:
        x,y=randint(0,79),randint(0,79)
        canplace=True
        for i in globalvars.items:
            if i.x == y and i.y == x:
                canplace = False
        if globalvars.grid[y][x]==1:
            canplace=False
        if canplace == True:
            return {'x':x,'y':y}