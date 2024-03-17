from random import randint
# from global_vars import items, grid
import global_vars


def addCoin() -> dict[str, int]:
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
