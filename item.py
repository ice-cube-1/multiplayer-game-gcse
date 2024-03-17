import vars
from random import randint, choice

CONSTS  = vars.consts()

class Item:
    def __init__(self, rarity: str, type: str) -> None:
        """Creates an item in a random place given a rarity and type"""
        self.x = 0
        self.y = 0
        while not self.check_item():
            self.x = randint(0, CONSTS.GRID_X - 1)
            self.y = randint(0, CONSTS.GRID_Y - 1)
        self.rarity = rarity
        self.type = type
        if self.type != 'weapon':
            self.weapon_type = ""
        else:
            self.weapon_type = choice(['/sword', '/spear', '/axe', '/bow'])

    def check_item(self) -> bool:
        """Checks if either an item or wall is in space"""
        if vars.grid[self.y][self.x] == 1:
            return False
        for i in vars.items:
            if i.x == self.x and i.y == self.y:
                return False
        return True

    def to_dict(self) -> dict[str, str | int]:
        return {
            'rarity': self.rarity,
            'type': self.type,
            'weapon_type': self.weapon_type,
            'x': self.x,
            'y': self.y
        }
