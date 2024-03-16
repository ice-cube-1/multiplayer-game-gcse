import global_vars
from random import randint, choice


class Item:
    def __init__(self, rarity, type):
        """Creates an item in a random place given a rarity and type"""
        self.x = 0
        self.y = 0
        while not self.check_item():
            self.x = randint(0, global_vars.grid_x - 1)
            self.y = randint(0, global_vars.grid_y - 1)
        self.rarity = rarity
        self.type = type
        if self.type != 'weapon':
            self.weapon_type = ""
        else:
            self.weapon_type = choice(['/sword', '/spear', '/axe', '/bow'])

    def check_item(self):
        """Checks if either an item or wall is in space"""
        if global_vars.grid[self.y][self.x] == 1:
            return False
        for i in global_vars.items:
            if i.x == self.x and i.y == self.y:
                return False
        return True

    def to_dict(self):
        return {
            'rarity': self.rarity,
            'type': self.type,
            'weapon_type': self.weapon_type,
            'x': self.x,
            'y': self.y
        }
