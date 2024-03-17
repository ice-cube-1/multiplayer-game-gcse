from random import randint
import vars


def addCoin() -> dict[str, int]:
    while True:
        x, y = randint(0, 79), randint(0, 79)
        can_place = True
        for i in vars.items:
            if i.x == y and i.y == x:
                can_place = False
        if vars.grid[y][x] == 1:
            can_place = False
        if can_place:
            return {'x': x, 'y': y}
