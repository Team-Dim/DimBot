import asyncio
from random import randint

from discord.ext import commands

from games.obj import UltraRockPaperScissor


class Games(commands.Cog):
    """Mini games
    Version 0"""

    def __init__(self, bot):
        self.bot = bot
        self.urps = {}

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name='urps')
    async def urps_cmd(self, ctx: commands.Context, h: int = randint(0, 15)):
        if not 0 <= h < 16:
            h = randint(0, 15)
        h = UltraRockPaperScissor(h)
        if ctx.author.id not in self.urps:
            self.urps[ctx.author.id] = (ctx.message, h)
        if len(self.urps) == 2:
            await asyncio.sleep(10)
