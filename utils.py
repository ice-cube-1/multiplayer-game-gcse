from random import randint

def rollDice(sides, number):
    '''Returns sum of NdX dice (can be .25)'''
    return sum([randint(1, sides) for i in range(int(number*4))])//4
    