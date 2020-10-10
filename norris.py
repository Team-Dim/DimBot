from discord.ext import commands

__version__ = '0'


class Norris(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Norris')
