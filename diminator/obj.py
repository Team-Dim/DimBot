from enum import IntEnum
from random import random

from discord.ext.commands import CommandError


class UltraRockPaperScissor(IntEnum):
    ROCK = 1
    GUN = 2
    LIGHTNING = 3
    DEVIL = 4
    DRAGON = 5
    WATER = 6
    AIR = 7
    PAPER = 8
    SPONGE = 9
    WOLF = 10
    TREE = 11
    HUMAN = 12
    SNAKE = 13
    SCISSOR = 14
    FIRE = 15

    def resolve(self, opponent):
        if self == opponent:
            return 0
        if opponent < self:
            opponent += 15
        if opponent - self > 7:
            return 1
        return -1


class BasePPException(CommandError):
    def __init__(self, message=None, *args):
        self.message = message
        super().__init__(message, args)

    def __str__(self):
        return self.message


class PPNotFound(BasePPException):

    def __init__(self, target_is_sender: bool):
        if target_is_sender:
            super().__init__("Please set up your pp by `{0}pp`!")
        else:
            super().__init__('Target has no pp.')


class PPStunned(BasePPException):
    def __init__(self, target_is_sender: bool):
        if target_is_sender:
            super().__init__('Your pp is stunned! Please use `{0}pp sf` to remove the effect!')
        else:
            super().__init__('Target is stunned!')


class PPLocked(BasePPException):
    def __init__(self, target_is_sender: bool):
        if target_is_sender:
            super().__init__('Your pp is locked! Please use `{0}pp lock` to unlock!')
        else:
            super().__init__('Target has enabled lock!')


class PPTransAm(BasePPException):
    def __init__(self):
        super().__init__('https://i.imgur.com/3NQgZAC.gif\nYour opponent is in TRANS-AM! He is too fast!')


max_pp_size = 69


class PP:

    def __init__(self, size: int, viagra, sesami, stun=0):
        self.size: int = size
        self.viagra: int = viagra  # -1: Not available 0: Not activated 1-3: rounds left
        self.score = 0
        self.sesami_oil: bool = sesami
        self.stun: int = stun
        self.lock: bool = False
        self.transam: int = 0

    def draw(self) -> str:
        """Returns the string for displaying pp"""
        description = f'Ɛ{"Ξ" * self.size}＞'
        bold = False
        extra = '🔒Locked' if self.lock else ''
        if self.transam <= 100:
            extra += f'TRANS-AM: Charging ({self.transam}%)\n'
        else:
            bold = True
            extra += '**TRANS-AM**\n'
        if self.viagra > 0:
            bold = True
            extra += f'Viagra rounds left: {self.viagra}\n'
        elif self.viagra == 0:
            extra += 'Viagra available!\n'
        if self.sesami_oil:
            extra += 'Sesami oil\n'
        if self.size == max_pp_size:
            extra += '**MAX POWER**\n'
        if self.stun:
            extra += f'**STUNNED:** {self.stun} rounds left'
        if bold:
            description = f'**{description}**'
        return description + '\n' + extra

    def check_lock(self, b):
        if self.lock:
            raise PPLocked(b)
        return self

    def check_stun(self, b):
        if self.stun:
            raise PPStunned(b)
        return self

    def check_transam_deflect(self):
        if self.transam == 101 and random() < 0.8:
            raise PPTransAm
        return self

    def check_all(self, b):
        return self.check_lock(b).check_stun(b)


class GF:
    ingredients_table = ('Cooking oil', 'Radish', 'Sausage', 'Mushroom', 'Rice flour', 'Sugar', 'Lotus', 'Peanut',
                         'Water chestnut', 'Egg', 'Flour')
    food_names = ('radish cake', 'year cake', 'rice ball', 'sugar lotus', 'water chestnut cake', 'oily angle', 'fried rice ball'
                  'sunflower seed', 'pumpkin seed', 'melon seed', 'candies', 'chocolate')
    food_energy = (30, 10, 15, 5, 10, 80, 70, 1, 2, 2, 4, 5)
    recipe = ((1, 2, 3, 4), (4, 5), (4, 5, 7), (5, 6), (4, 5, 8), (0, 7, 9, 10), (0, 4, 5, 7))

    def __init__(self):
        self.energy: int = 0
        self.ingredients = {}
        self.food = {}

    def add_ingredient(self, index: int):
        if index in self.ingredients:
            self.ingredients[index] += 1
        else:
            self.ingredients[index] = 1

    def add_food(self, index: int):
        if index in self.food:
            self.food[index] += 1
        else:
            self.food[index] = 1
