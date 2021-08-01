from enum import Enum


class UltraRockPaperScissor(Enum):
    ROCK = 0
    GUN = 1
    LIGHTNING = 2
    DEVIL = 3
    DRAGON = 4
    WATER = 5
    AIR = 6
    PAPER = 7
    SPONGE = 8
    WOLF = 9
    TREE = 10
    HUMAN = 11
    SNAKE = 12
    SCISSOR = 13
    FIRE = 14

    def resolve(self, opponent):
        if self == opponent:
            return 0
        if opponent < self:
            opponent += 15
        if opponent - self > 7:
            return 1
        return -1
