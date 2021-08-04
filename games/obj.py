from enum import IntEnum


class UltraRockPaperScissor(IntEnum):
    ROCK = 1
    GUN = 2
    LIGHTNING = 3
    DEVIL = 4
    DRAGON = 5
    WATER = 6
    AIR = 7
    PAPER =8
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
