from item import Item
from random import randint
from datetime import datetime
import vars
import math
from utils import rollDice
from coins import addCoin

CONSTS = vars.consts()


def check_player(x: int, y: int) -> bool:
    """Checks if a player is in space"""
    for i in vars.players:
        if i.x == x and i.y == y and i.visible:
            return False
    return True


class Player:
    def __init__(self, name: str) -> None:
        # all the variables for it - SIMPLIFY
        self.x = 0
        self.y = 0
        while vars.grid[self.y][self.x] != 0:
            self.x = randint(0, CONSTS.GRID_X - 1)
            self.y = randint(0, CONSTS.GRID_Y - 1)
        self.name = name
        self.color = f'rgb({randint(0, 255)},{randint(0, 255)},{randint(0, 255)})'
        self.hp = 40
        self.max_hp = 40
        self.damage = 4
        self.damageMultiplier = 1
        self.ac = 10
        self.range = 1
        self.attackSpeed = 0.3
        self.items = []
        self.proficiency = 0
        self.direction = 'W'
        self.kill_count = 0
        self.visible = True
        self.last_move = datetime.now()
        self.displayed_anywhere = True
        self.ally = [self.name]
        self.coinCount = 0

    def move(self, charin: str) -> None:
        """deals with client input"""
        self.last_move = datetime.now()
        if not self.visible:  # come back online
            self.visible = True
            self.displayed_anywhere = True
            vars.messages.append(
                [f'{datetime.now().strftime("[%H:%M] ")}{self.name} has joined', "black"])
            vars.SOCKETIO.emit('message', [vars.messages[-1]])
        if charin == "W":
            if vars.grid[self.y - 1][self.x] == 0 and check_player(self.x, self.y - 1):
                self.y -= 1
            self.direction = 'W'
        elif charin == "S":
            if vars.grid[self.y + 1][self.x] == 0 and check_player(self.x, self.y + 1):
                self.y += 1
            self.direction = 'S'
        elif charin == "A":
            if vars.grid[self.y][self.x - 1] == 0 and check_player(self.x - 1, self.y):
                self.x -= 1
            self.direction = 'A'
        elif charin == "D":
            if vars.grid[self.y][self.x + 1] == 0 and check_player(self.x + 1, self.y):
                self.x += 1
            self.direction = 'D'
        elif charin == "Space":
            # which actually returns the kill count from the attack function if called
            self.kill_count += self.findTarget()
            players_info = [i.getInfoInString() for i in vars.players if i.displayed_anywhere]
            self.proficiency = math.floor(math.log(self.kill_count + 1, 2))
            self.max_hp = 40 + self.kill_count
            vars.SOCKETIO.emit('PlayersInfo', sorted(players_info, key=lambda x: int(x[2]), reverse=True))
        elif charin == "E":
            self.interact()

    def interact(self) -> None:
        """Picks up an item + edits your stats when you press E. Also drops your item if you have one"""
        for i in range(len(vars.items)):
            if vars.items[i].x == self.x and vars.items[i].y == self.y:
                # comparatively simple as you just use it
                if vars.items[i].type == 'healing':
                    self.hp += CONSTS.HEALING_STATS[CONSTS.RARITIES.index(
                        vars.items[i].rarity)]
                    if self.hp > self.max_hp:
                        self.hp = self.max_hp
                    vars.items.append(
                        Item(vars.items[i].rarity, "healing"))
                    vars.items.pop(i)
                else:
                    had_type = False
                    for j in range(len(self.items)):
                        # swaps all stats of the old and new vars.items
                        if self.items[j].type == vars.items[i].type:
                            self.items[j].weapon_type, vars.items[i].weapon_type = vars.items[i].weapon_type, self.items[j].weapon_type
                            self.items[j].type, vars.items[i].type = vars.items[i].type, self.items[j].type
                            self.items[j].rarity, vars.items[i].rarity = vars.items[i].rarity, self.items[j].rarity
                            had_type = True
                    if not had_type:  # otherwise adds it to their list of vars.items
                        self.items.append(vars.items[i])
                        vars.items.pop(i)
                    for picked_up in self.items:  # modifies the stats - it does this to both vars.items,
                        # no good reason as to why, but it doesn't take much processing
                        if picked_up.type == 'armour':
                            self.ac = CONSTS.ARMOUR_STATS[CONSTS.RARITIES.index(picked_up.rarity)]
                        else:
                            self.damage = CONSTS.WEAPON_TYPES[picked_up.weapon_type][0]
                            self.range = CONSTS.WEAPON_TYPES[picked_up.weapon_type][1]
                            self.attackSpeed = CONSTS.WEAPON_TYPES[picked_up.weapon_type][2]
                            self.damageMultiplier = CONSTS.WEAPON_MULTIPLIER[CONSTS.RARITIES.index(picked_up.rarity)]
                vars.SOCKETIO.emit('item_positions', [i.to_dict() for i in vars.items])
        for i in range(len(vars.coins)):
            if vars.coins[i]['x'] == self.x and vars.coins[i]['y'] == self.y:
                self.coinCount += 1
                vars.coins.pop(i)
                vars.coins.insert(i, addCoin())
                vars.SOCKETIO.emit('coin_positions', vars.coins)
                print(self.coinCount)

    def attack(self, to_attack: int) -> int:
        """deals damage / kill logic from attack"""
        if rollDice(40, 1) + self.proficiency > vars.players[to_attack].ac:  # did it actually hit, if so do
            # damage
            vars.players[to_attack].hp -= rollDice(
                self.damage, self.damageMultiplier) + self.proficiency
            if vars.players[to_attack].hp <= 0:  # if is dead
                vars.players[to_attack].hp = 0
                # drops loot (SIMPLIFY)
                for i in vars.players[to_attack].vars.items:
                    i.x, i.y = vars.players[to_attack].x, vars.players[to_attack].y
                    if i.type == 'armour':
                        while not i.check_item():
                            i.x += 1
                    if i.type == 'weapon':
                        while not i.check_item():
                            i.y -= 1
                    vars.items.append(i)
                vars.SOCKETIO.emit('item_positions', [i.to_dict() for i in vars.items])
                vars.SOCKETIO.emit('new_positions', {"objects": [i.to_dict() for i in vars.players]})
                # stores everything that needs to be kept during respawn (SIMPLIFY)
                store_color = vars.players[to_attack].color
                store_max_hp = vars.players[to_attack].max_hp - 1
                store_kills = vars.players[to_attack].kill_count
                store_proficiency = vars.players[to_attack].proficiency
                vars.players[to_attack] = Player(vars.players[to_attack].name)
                vars.players[to_attack].color = store_color
                vars.players[to_attack].max_hp = store_max_hp
                vars.players[to_attack].kill_count = store_kills
                vars.players[to_attack].proficiency = store_proficiency
                vars.players[to_attack].hp = store_max_hp
                # AT LEAST SOME SHOULD BE MODULARIZED
                vars.messages.append(
                    [
                        f'{datetime.now().strftime("[%H:%M] ")}{vars.players[to_attack].name} was killed by {self.name}',
                        "black"])
                vars.SOCKETIO.emit('message', [vars.messages[-1]])
                return 1  # add to kill count
        return 0  # did not kill

    def findTarget(self) -> int:
        """Attacks the first (presumes there's only one) player in range"""
        '''Does this based on both range in a semicircle and direction'''
        for i in range(len(vars.players)):
            if (self.x - vars.players[i].x) ** 2 + (
                    self.y - vars.players[i].y) ** 2 <= self.range ** 2 and vars.players[
                i].visible and vars.players[i].name not in self.ally and self.name not in \
                    vars.players[i].ally:
                if self.direction == 'W' and self.y - vars.players[i].y > 0:
                    return self.attack(i)
                if self.direction == 'S' and vars.players[i].y - self.y > 0:
                    return self.attack(i)
                if self.direction == 'A' and self.x - vars.players[i].x > 0:
                    return self.attack(i)
                if self.direction == 'D' and vars.players[i].x - self.x > 0:
                    return self.attack(i)
        return 0

    def to_dict(self) -> dict[str, str | int]:
        """only what the client needs - simpler to serialize, more secure + less traffic"""
        weapon_type, weapon_rarity, armour = False, False, False
        for i in self.items:
            if i.type == 'weapon':
                weapon_rarity, weapon_type = i.rarity, i.weapon_type
            else:
                armour = i.rarity
        return {
            'x': self.x,
            'y': self.y,
            'color': self.color,
            'attackSpeed': self.attackSpeed * 1000,
            'hp': self.hp,
            'name': self.name,
            'visible': self.visible,
            'weapon': weapon_type,
            'weapon_rarity': weapon_rarity,
            'armour': armour
        }

    def getInfoInString(self) -> tuple[str, str, int]:
        """for the leaderboard"""
        if self.visible:
            status = "online"
        else:
            status = "offline"
        return f'{self.name}: {self.hp}/{self.max_hp} - Level {self.proficiency}, {self.kill_count} kills ({status})', self.color, self.kill_count

    def getInfoForSpecificPlayer(self) -> list:
        upgrade_costs = ['', '']
        for i in range(len(self.items)):
            upgrade_costs[i] = CONSTS.UPGRADE_COSTS[self.items[i].rarity]
        '''more detailed info about player, formatted by client'''
        return [
            f'{self.name}:\nLevel: {self.proficiency} ({self.kill_count} kills)\nHP: {self.hp}/{self.max_hp}\nArmour class: {self.ac}\nCoins: {self.coinCount}\nUpgrade Cost: {upgrade_costs[0]}',
            f'\nDamage: {math.floor(self.damageMultiplier + self.proficiency)}-{math.floor((self.damageMultiplier * self.damage) + self.proficiency)}\nRange: {self.range}\nAttack speed: {self.attackSpeed}s\n\nUpgrade Cost: {upgrade_costs[1]}',
            [i.to_dict() for i in self.items]]
