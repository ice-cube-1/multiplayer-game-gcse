import vars
from random import randint, choice

class Item:
    def __init__(self, global_vars: vars.GLOBAL, rarity: str, type: str) -> None:
        """Creates an item in a random place given a rarity and type"""
        self.x = 0
        self.y = 0
        while not self.check_item(global_vars):
            self.x = randint(0, vars.GRID_X - 1)
            self.y = randint(0, vars.GRID_Y - 1)
        self.rarity = rarity
        self.type = type
        if self.type != 'weapon':
            self.weapon_type = ""
        else:
            self.weapon_type = choice(['/sword', '/spear', '/axe', '/bow'])

    def check_item(self, global_vars: vars.GLOBAL) -> bool:
        """Checks if either an item or wall is in space"""
        if global_vars.grid[self.y][self.x] == 1:
            return False
        for i in global_vars.items:
            if i.x == self.x and i.y == self.y:
                return False
        return True

    def to_dict(self) -> dict[str, str | int]:
        """returns the item's rarity, type and position"""
        return {
            'rarity': self.rarity,
            'type': self.type,
            'weapon_type': self.weapon_type,
            'x': self.x,
            'y': self.y
        }
