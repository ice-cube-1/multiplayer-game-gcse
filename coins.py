from random import randint
import vars


def addCoin(global_vars: vars.GLOBAL) -> dict[str, int]:
    """creates a coin in an unnocupied space, returns the x and y"""
    while True:
        x, y = randint(0, 79), randint(0, 79)
        can_place = True
        for i in global_vars.items:
            if i.x == y and i.y == x:
                can_place = False
        if global_vars.grid[y][x] == 1:
            can_place = False
        if can_place:
            return {'x': x, 'y': y}
