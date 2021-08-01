import asyncio
from copy import copy
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
        """Ultra Rock Paper Scissor
        `urps [0-14]` to pick a choice. If you didn't provide a number or
        the number is not 0-14, randomly chooses for you.

        If you started the round, you have to wait 10s. During this period, any person can send this command to join."""
        if not 0 <= h <= 14:
            h = randint(0, 14)
        if ctx.author.id not in self.urps:
            self.urps[ctx.author.id] = [ctx.message, UltraRockPaperScissor(h), 0]
        self.bot.loop.create_task(ctx.message.add_reaction('✅'))
        if len(self.urps) == 1:
            fake_ctx = copy(ctx.message)
            fake_ctx.author = self.bot.user
            self.urps[self.bot.user.id] = [fake_ctx, UltraRockPaperScissor(randint(0, 14)), 0]
            await asyncio.sleep(10)
            keys = tuple(self.urps)
            for i, key in enumerate(keys):
                for opponent in keys[i+1:]:
                    score = self.urps[key][1].resolve(self.urps[opponent][1])
                    self.urps[key][2] += score
                    self.urps[opponent][2] -= score
            self.urps = dict(sorted(self.urps.items(), key=lambda e: e[1][2], reverse=True))
            resp = '**Score** | Name | Choice\n'
            for u in self.urps.values():
                resp += f'**{u[2]}** {u[0].author}, {u[1].name}\n'
            dest = []
            for u in self.urps.values():
                if u[0].channel not in dest:
                    await u[0].reply(resp)
                    dest.append(u[0].channel)
            self.urps = {}
