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
    async def urps_cmd(self, ctx: commands.Context, h: int = 15):
        if not 0 <= h <= 14:
            h = randint(0, 14)
        if ctx.author.id not in self.urps:
            self.urps[ctx.author.id] = (ctx.message, UltraRockPaperScissor(h), 0)
        if len(self.urps) == 2:
            await asyncio.sleep(10)
            keys = tuple(self.urps)
            for i, key in enumerate(keys):
                for opponent in keys[i+1:]:
                    

            return
            votes = {}
            for _, choice in self.urps.values():
                if choice in votes:
                    votes[choice] += 1
                else:
                    votes[choice] = 1
            resp = 'Total votes:\n'
            for v in votes:
                resp += f'**{v.name}**: {votes[v]} '
            await ctx.reply(resp)
