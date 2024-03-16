from item import Item
from random import randint
from datetime import datetime
from flasksetup import socketio
import math
from utils import rollDice
from coins import addCoin
import globalvars


class Player:
    def __init__(self, name):
        # all the variables for it - SIMPLIFY
        self.x = 0
        self.y = 0
        while globalvars.grid[self.y][self.x] != 0:
            self.x = randint(0, globalvars.gridlx-1)
            self.y = randint(0, globalvars.gridly-1)
        self.name = name
        self.color = f'rgb({randint(0,255)},{randint(0,255)},{randint(0,255)})'
        self.hp = 40
        self.maxhp = 40
        self.damage = 4
        self.damageMultiplier = 1
        self.ac = 10
        self.range = 1
        self.attackSpeed = 0.3
        self.items = []
        self.proficiency = 0
        self.direction = 'W'
        self.killCount = 0
        self.visible = True
        self.lastMove = datetime.now()
        self.displayedAnywhere = True
        self.ally = [self.name]
        self.coinCount = 0

    def move(self, charin):
        '''deals with client input'''
        self.lastMove = datetime.now()
        if self.visible == False:  # come back online
            self.visible = True
            self.displayedAnywhere = True
            globalvars.messages.append(
                [f'{datetime.now().strftime("[%H:%M] ")}{self.name} has joined', "black"])
            socketio.emit('message', [globalvars.messages[-1]])
        if charin == "W":
            # SIMPLIFY by just putting the globalvars.gridcheck in checkplayer
            if globalvars.grid[self.y-1][self.x] == 0 and self.checkplayer(self.x, self.y-1):
                self.y -= 1
            self.direction = 'W'
        elif charin == "S":
            if globalvars.grid[self.y+1][self.x] == 0 and self.checkplayer(self.x, self.y+1):
                self.y += 1
            self.direction = 'S'
        elif charin == "A":
            if globalvars.grid[self.y][self.x-1] == 0 and self.checkplayer(self.x-1, self.y):
                self.x -= 1
            self.direction = 'A'
        elif charin == "D":
            if globalvars.grid[self.y][self.x+1] == 0 and self.checkplayer(self.x+1, self.y):
                self.x += 1
            self.direction = 'D'
        elif charin == "Space":
            # which actually returns the killcount from the attack function if called
            self.killCount += self.findTarget()
            playersInfo = [i.getInfoInString()
                           for i in globalvars.players if i.displayedAnywhere]
            self.proficiency = math.floor(math.log(self.killCount+1, 2))
            self.maxhp = 40+self.killCount
            socketio.emit('PlayersInfo', sorted(
                playersInfo, key=lambda x: int(x[2]), reverse=True))
        elif charin == "E":
            self.interact()

    def checkplayer(self, x, y):
        '''Checks if a player is in space'''
        for i in globalvars.players:
            if i.x == x and i.y == y and i.visible == True:
                return False
        return True

    def interact(self):
        '''Picks up an item + edits your stats when you press E. Also drops your item if you have one'''
        for i in range(len(globalvars.items)):
            if globalvars.items[i].x == self.x and globalvars.items[i].y == self.y:
                # comparatively simple as you just use it
                if globalvars.items[i].type == 'healing':
                    self.hp += globalvars.healingStats[globalvars.rarities.index(
                        globalvars.items[i].rarity)]
                    if self.hp > self.maxhp:
                        self.hp = self.maxhp
                    globalvars.items.append(
                        Item(globalvars.items[i].rarity, "healing"))
                    globalvars.items.pop(i)
                else:
                    hadType = False
                    for j in range(len(self.items)):
                        # swaps all stats of the old and new globalvars.items
                        if self.items[j].type == globalvars.items[i].type:
                            self.items[j].weapontype, globalvars.items[i].weapontype = globalvars.items[i].weapontype, self.items[j].weapontype
                            self.items[j].type, globalvars.items[i].type = globalvars.items[i].type, self.items[j].type
                            self.items[j].rarity, globalvars.items[i].rarity = globalvars.items[i].rarity, self.items[j].rarity
                            hadType = True
                    if not hadType:  # otherwise adds it to their list of globalvars.items
                        self.items.append(globalvars.items[i])
                        globalvars.items.pop(i)
                    for pickedup in self.items:  # modifies the stats - it does this to both globalvars.items, no good reason as to why but it doesn't take much processing
                        if pickedup.type == 'armour':
                            self.ac = globalvars.armourStats[globalvars.rarities.index(
                                pickedup.rarity)]
                        else:
                            self.damage = globalvars.weaponTypes[pickedup.weapontype][0]
                            self.range = globalvars.weaponTypes[pickedup.weapontype][1]
                            self.attackSpeed = globalvars.weaponTypes[pickedup.weapontype][2]
                            self.damageMultiplier = globalvars.weaponMultiplier[globalvars.rarities.index(
                                pickedup.rarity)]
        for i in range(len(globalvars.coins)):
            if globalvars.coins[i]['x'] == self.x and globalvars.coins[i]['y'] == self.y:
                self.coinCount += 1
                globalvars.coins.pop(i)
                globalvars.coins.insert(i, addCoin())
                socketio.emit('coin_positions', globalvars.coins)
                print(self.coinCount)

    def attack(self, toAttack):
        '''deals damage / kill logic from attack'''
        if rollDice(40, 1)+self.proficiency > globalvars.players[toAttack].ac:  # did it actually hit, if so do damage
            globalvars.players[toAttack].hp -= rollDice(
                self.damage, self.damageMultiplier)+self.proficiency
            if globalvars.players[toAttack].hp <= 0:  # if is dead
                globalvars.players[toAttack].hp = 0
                # drops loot (SIMPLIFY)
                for i in globalvars.players[toAttack].globalvars.items:
                    i.x, i.y = globalvars.players[toAttack].x, globalvars.players[toAttack].y
                    if i.type == 'armour':
                        while not i.checkitem():
                            i.x += 1
                    if i.type == 'weapon':
                        while not i.checkitem():
                            i.y -= 1
                    globalvars.items.append(i)
                socketio.emit('item_positions', [
                              i.to_dict() for i in globalvars.items])
                socketio.emit('new_positions',  {"objects": [
                              i.to_dict() for i in globalvars.players]})
                # stores everything that needs to be kept during respawn (SIMPLIFY)
                storeColor = globalvars.players[toAttack].color
                storemaxHP = globalvars.players[toAttack].maxhp-1
                storeKills = globalvars.players[toAttack].killCount
                storeProficiency = globalvars.players[toAttack].proficiency
                globalvars.players[toAttack] = Player(
                    globalvars.players[toAttack].name)
                globalvars.players[toAttack].color = storeColor
                globalvars.players[toAttack].maxhp = storemaxHP
                globalvars.players[toAttack].killCount = storeKills
                globalvars.players[toAttack].proficiency = storeProficiency
                globalvars.players[toAttack].hp = storemaxHP
                # AT LEAST SOME SHOULD BE MODULARIZED
                globalvars.messages.append(
                    [f'{datetime.now().strftime("[%H:%M] ")}{globalvars.players[toAttack].name} was killed by {self.name}', "black"])
                socketio.emit('message', [globalvars.messages[-1]])
                return 1  # add to kill count
        return 0  # did not kill

    def findTarget(self):
        '''Attacks the first (presumes there's only one) player in range'''
        '''Does this based on both range in a semicircle and direction'''
        for i in range(len(globalvars.players)):
            if (self.x-globalvars.players[i].x)**2+(self.y-globalvars.players[i].y)**2 <= self.range**2 and globalvars.players[i].visible == True and globalvars.players[i].name not in self.ally and self.name not in globalvars.players[i].ally:
                if self.direction == 'W' and self.y - globalvars.players[i].y > 0:
                    return self.attack(i)
                if self.direction == 'S' and globalvars.players[i].y - self.y > 0:
                    return self.attack(i)
                if self.direction == 'A' and self.x - globalvars.players[i].x > 0:
                    return self.attack(i)
                if self.direction == 'D' and globalvars.players[i].x - self.x > 0:
                    return self.attack(i)
        return 0

    def to_dict(self):
        '''only what the client needs - simpler to serialize, more secure + less traffic'''
        weapontype, weaponrarity, armour = False, False, False
        for i in self.items:
            if i.type == 'weapon':
                weaponrarity, weapontype = i.rarity, i.weapontype
            else:
                armour = i.rarity
        return {
            'x': self.x,
            'y': self.y,
            'color': self.color,
            'attackSpeed': self.attackSpeed*1000,
            'hp': self.hp,
            'name': self.name,
            'visible': self.visible,
            'name': str(self.name),
            'weapon': weapontype,
            'weaponrarity': weaponrarity,
            'armour': armour
        }

    def getInfoInString(self):
        '''for the leaderboard'''
        if self.visible:
            status = "online"
        else:
            status = "offline"
        return f'{self.name}: {self.hp}/{self.maxhp} - Level {self.proficiency}, {self.killCount} kills ({status})', self.color, self.killCount

    def getInfoForSpecificPlayer(self):
        upgradeCosts = ['', '']
        for i in range(len(self.items)):
            upgradeCosts[i] = globalvars.upgradeCosts[self.items[i].rarity]
        '''more detailed info about player, formatted by client'''
        return [f'{self.name}:\nLevel: {self.proficiency} ({self.killCount} kills)\nHP: {self.hp}/{self.maxhp}\nArmour class: {self.ac}\nCoins: {self.coinCount}\nUpgrade Cost: {upgradeCosts[0]}',
                f'\nDamage: {math.floor(self.damageMultiplier+self.proficiency)}-{math.floor((self.damageMultiplier*self.damage)+self.proficiency)}\nRange: {self.range}\nAttack speed: {self.attackSpeed}s\n\nUpgrade Cost: {upgradeCosts[1]}',
                [i.to_dict() for i in self.items]]
