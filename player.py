from item import Item
from random import randint
from datetime import datetime
import vars
import math
from utils import rollDice
from coins import addCoin


def check_player(global_vars: vars.GLOBAL, x: int, y: int) -> bool:
    """Checks if a player is in space"""
    for i in global_vars.players:
        if i.x == x and i.y == y and i.visible:
            return False
    return True


class Player:
    def __init__(self, global_vars: vars.GLOBAL, name: str) -> None:
        """sets the default values for a character"""
        self.x = 0
        self.y = 0
        while global_vars.grid[self.y][self.x] != 0:
            self.x = randint(0, vars.GRID_X - 1)
            self.y = randint(0, vars.GRID_Y - 1)
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

    def move(self, global_vars: vars.GLOBAL, charin: str) -> None:
        """deals with client input - either moves, or calls attack / interact functions"""
        self.last_move = datetime.now()
        if not self.visible:  # come back online
            self.visible = True
            self.displayed_anywhere = True
            with global_vars.globals_lock:
                global_vars.messages.append(
                    [f'{datetime.now().strftime("[%H:%M] ")}{self.name} has joined', "black"])
            global_vars.SOCKETIO.emit('message', [global_vars.messages[-1]])
        if charin == "W":
            if global_vars.grid[self.y - 1][self.x] == 0 and check_player(global_vars, self.x, self.y - 1):
                self.y -= 1
            self.direction = 'W'
        elif charin == "S":
            if global_vars.grid[self.y + 1][self.x] == 0 and check_player(global_vars, self.x, self.y + 1):
                self.y += 1
            self.direction = 'S'
        elif charin == "A":
            if global_vars.grid[self.y][self.x - 1] == 0 and check_player(global_vars, self.x - 1, self.y):
                self.x -= 1
            self.direction = 'A'
        elif charin == "D":
            if global_vars.grid[self.y][self.x + 1] == 0 and check_player(global_vars, self.x + 1, self.y):
                self.x += 1
            self.direction = 'D'
        elif charin == "Space":
            # which actually returns the kill count from the attack function if called
            self.kill_count += self.findTarget(global_vars)
            players_info = [i.getInfoInString()
                            for i in global_vars.players if i.displayed_anywhere]
            self.proficiency = math.floor(math.log(self.kill_count + 1, 2))
            self.max_hp = 40 + self.kill_count
            global_vars.SOCKETIO.emit('PlayersInfo', sorted(
                players_info, key=lambda x: int(x[2]), reverse=True))
        elif charin == "E":
            self.interact(global_vars)

    def interact(self, global_vars: vars.GLOBAL) -> None:
        """Picks up an item + edits your stats when you press E. Also drops your item if you have one (N/A for healing or coins)"""
        for i in range(len(global_vars.items)):
            if global_vars.items[i].x == self.x and global_vars.items[i].y == self.y:
                # comparatively simple as you just use it
                if global_vars.items[i].type == 'healing':
                    self.hp += vars.HEALING_STATS[vars.RARITIES.index(
                        global_vars.items[i].rarity)]
                    if self.hp > self.max_hp:
                        self.hp = self.max_hp
                    with global_vars.globals_lock:
                        global_vars.items.append(
                            Item(global_vars, global_vars.items[i].rarity, "healing"))
                        global_vars.items.pop(i)
                else:
                    had_type = False
                    for j in range(len(self.items)):
                        # swaps all stats of the old and new global_vars.items
                        if self.items[j].type == global_vars.items[i].type:
                            with global_vars.globals_lock:
                                self.items[j].weapon_type, global_vars.items[
                                    i].weapon_type = global_vars.items[i].weapon_type, self.items[j].weapon_type
                                self.items[j].type, global_vars.items[i].type = global_vars.items[i].type, self.items[j].type
                                self.items[j].rarity, global_vars.items[i].rarity = global_vars.items[i].rarity, self.items[j].rarity
                            had_type = True
                    if not had_type:  # otherwise adds it to their list of global_vars.items
                        self.items.append(global_vars.items[i])
                        with global_vars.globals_lock:
                            global_vars.items.pop(i)
                    for picked_up in self.items:  # modifies the stats - it does this to both global_vars.items,
                        # no good reason as to why, but it doesn't take much processing
                        if picked_up.type == 'armour':
                            self.ac = vars.ARMOUR_STATS[vars.RARITIES.index(
                                picked_up.rarity)]
                        else:
                            self.damage = vars.WEAPON_TYPES[picked_up.weapon_type][0]
                            self.range = vars.WEAPON_TYPES[picked_up.weapon_type][1]
                            self.attackSpeed = vars.WEAPON_TYPES[picked_up.weapon_type][2]
                            self.damageMultiplier = vars.WEAPON_MULTIPLIER[vars.RARITIES.index(
                                picked_up.rarity)]
                global_vars.SOCKETIO.emit(
                    'item_positions', [i.to_dict() for i in global_vars.items])
        for i in range(len(global_vars.coins)):
            if global_vars.coins[i]['x'] == self.x and global_vars.coins[i]['y'] == self.y:
                self.coinCount += 1
                with global_vars.globals_lock:
                    global_vars.coins[i] = addCoin(global_vars)
                global_vars.SOCKETIO.emit('coin_positions', global_vars.coins)
                print(self.coinCount)

    def attack(self, global_vars: vars.GLOBAL, to_attack: int) -> int:
        """deals damage / kill logic - returns the kill count to add (1 if succesful kill)"""
        if rollDice(40, 1) + self.proficiency > global_vars.players[to_attack].ac:
            with global_vars.globals_lock:
                global_vars.players[to_attack].hp -= rollDice(
                    self.damage, self.damageMultiplier) + self.proficiency
            if global_vars.players[to_attack].hp <= 0:  # if is dead
                global_vars.players[to_attack].hp = 0
                for i in global_vars.players[to_attack].global_vars.items:
                    i.x, i.y = global_vars.players[to_attack].x, global_vars.players[to_attack].y
                    if i.type == 'armour':
                        while not i.check_item():
                            i.x += 1
                    if i.type == 'weapon':
                        while not i.check_item():
                            i.y -= 1
                    with global_vars.globals_lock:
                        global_vars.items.append(i)
                global_vars.SOCKETIO.emit(
                    'item_positions', [i.to_dict() for i in global_vars.items])
                global_vars.SOCKETIO.emit(
                    'new_positions', {"objects": [i.to_dict() for i in global_vars.players]})
                store_color = global_vars.players[to_attack].color
                store_max_hp = global_vars.players[to_attack].max_hp - 1
                store_kills = global_vars.players[to_attack].kill_count
                store_proficiency = global_vars.players[to_attack].proficiency
                with global_vars.globals_lock:
                    global_vars.players[to_attack] = Player(
                        global_vars, global_vars.players[to_attack].name)
                    global_vars.players[to_attack].color = store_color
                    global_vars.players[to_attack].max_hp = store_max_hp
                    global_vars.players[to_attack].kill_count = store_kills
                    global_vars.players[to_attack].proficiency = store_proficiency
                    global_vars.players[to_attack].hp = store_max_hp
                    global_vars.messages.append(
                        [
                            f'{datetime.now().strftime("[%H:%M] ")}{global_vars.players[to_attack].name} was killed by {self.name}',
                            "black"])
                global_vars.SOCKETIO.emit(
                    'message', [global_vars.messages[-1]])
                return 1
        return 0

    def findTarget(self, global_vars: vars.GLOBAL) -> int:
        """Attacks the first (presumes there's only one) player in range"""
        for i in range(len(global_vars.players)):
            if (self.x - global_vars.players[i].x) ** 2 + (
                    self.y - global_vars.players[i].y) ** 2 <= self.range ** 2 and global_vars.players[
                i].visible and global_vars.players[i].name not in self.ally and self.name not in \
                    global_vars.players[i].ally:
                if self.direction == 'W' and self.y - global_vars.players[i].y > 0:
                    return self.attack(global_vars, i)
                if self.direction == 'S' and global_vars.players[i].y - self.y > 0:
                    return self.attack(global_vars, i)
                if self.direction == 'A' and self.x - global_vars.players[i].x > 0:
                    return self.attack(global_vars, i)
                if self.direction == 'D' and global_vars.players[i].x - self.x > 0:
                    return self.attack(global_vars, i)
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
        """more detailed info - only displayed by one player, and formatted into columns in the JS"""
        upgrade_costs = ['', '']
        for i in range(len(self.items)):
            upgrade_costs[i] = vars.UPGRADE_COSTS[self.items[i].rarity]
        return [
            f'{self.name}:\nLevel: {self.proficiency} ({self.kill_count} kills)\nHP: {self.hp}/{self.max_hp}\nArmour class: {self.ac}\nCoins: {self.coinCount}\nUpgrade Cost: {upgrade_costs[0]}',
            f'\nDamage: {math.floor(self.damageMultiplier + self.proficiency)}-{math.floor((self.damageMultiplier * self.damage) + self.proficiency)}\nRange: {self.range}\nAttack speed: {self.attackSpeed}s\n\nUpgrade Cost: {upgrade_costs[1]}',
            [i.to_dict() for i in self.items]]
