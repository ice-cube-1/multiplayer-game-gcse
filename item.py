import globalvars
from random import randint, choice


class Item:
    def __init__(self, rarity, type):
        '''Creates an item in a random place given a rarity and type'''
        self.x = 0
        self.y = 0
        while not self.checkitem():
            self.x = randint(0, globalvars.gridlx-1)
            self.y = randint(0, globalvars.gridly-1)
        self.rarity = rarity
        self.type = type
        if self.type != 'weapon':
            self.weapontype = ""
        else:
            self.weapontype = choice(['/sword', '/spear', '/axe', '/bow'])

    def checkitem(self):
        '''Checks if either an item or wall is in space'''
        if globalvars.grid[self.y][self.x] == 1:
            return False
        for i in globalvars.items:
            if (i.x == self.x and i.y == self.y):
                return False
        return True
    
    def to_dict(self):
        return {
            'rarity':self.rarity,
            'type':self.type,
            'weapontype':self.weapontype,
            'x':self.x,
            'y':self.y
        }