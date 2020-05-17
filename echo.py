import sqlite3

from discord.ext import commands

__version__ = '0'


class Echo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Echo')
        self.db = sqlite3.connect('DimBot.db')
        self.cursor = self.db.cursor()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')

    @commands.group()
    async def quote(self, ctx):
        pass

    @quote.command()
    async def add(self, ctx, *, args):
        pass
