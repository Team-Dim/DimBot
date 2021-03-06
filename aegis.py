import asyncio

import discord
from discord.ext.commands import Cog, Context

import bitbay
import ikaros
from missile import Missile


async def send(ch: discord.TextChannel, content: str):
    return await ch.send('**Aegis:** ' + content)


class Aegis(Cog):
    """AutoMod system
    Version 0.3"""

    def __init__(self, bot):
        self.bot = bot
        self.count = {}

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        if not msg.guild or msg.author.bot or msg.channel.id == bitbay.spam_ch_id:
            return
        if msg.author.id not in self.count:
            self.count[msg.author.id] = [[msg.created_at], 0]
        raw_mention_count = len(msg.raw_mentions)
        if raw_mention_count >= 5:
            self.count[msg.author.id][1] += 1
            res = await send(msg.channel, f'Detected mass ping ({raw_mention_count}). Warn: {self.count[msg.author.id][1]}')
            self.bot.loop.create_task(self.act(msg, res, 'Aegis: Mass ping'))
        else:
            ml = len(self.count[msg.author.id][0])
            if ml == 4:
                if (msg.created_at - self.count[msg.author.id][0][0]).total_seconds() < 5:
                    self.count[msg.author.id][1] += 1
                    res = await send(msg.channel,
                                     'Detected spam, type V. Warn: ' + str(self.count[msg.author.id][1]))
                    self.count[msg.author.id][0] = []
                    self.bot.loop.create_task(self.act(msg, res, 'Aegis: Spam, type V'))
                else:
                    self.count[msg.author.id][0].pop(0)
            ml = len(self.count[msg.author.id][0])
            if ml > 1 > (msg.created_at - self.count[msg.author.id][0][ml - 2]).total_seconds():
                self.count[msg.author.id][1] += 1
                res = await send(msg.channel, 'Detected spam, type I. Warn: ' + str(self.count[msg.author.id][1]))
                self.count[msg.author.id][0] = []
                self.bot.loop.create_task(self.act(msg, res, 'Aegis: Spam, type I'))
            for t in self.count[msg.author.id][0]:
                if (msg.created_at - t).total_seconds() >= 5:
                    self.count[msg.author.id][0].pop(0)
            self.count[msg.author.id][0].append(msg.created_at)

    async def act(self, msg: discord.Message, res: discord.Message, reason: str):
        if self.count[msg.author.id][1] == 3:
            role = None
            if msg.guild.id == bitbay.guild_id:
                role = msg.guild.get_role(718210713893601301)  # Muted Pirate
            elif msg.guild == self.bot.missile.guild:
                role = msg.guild.get_role(474578007156326412)  # Asteroid Belt
            if role:
                await msg.author.add_roles(role, reason=reason + ', threat level 1')
                await Missile.append_message(res, 'Muted')
                await asyncio.sleep(10)
                await msg.author.remove_roles(role, reason='Aegis: Deactivating level 1')
                await send(msg.channel, "Unmuted " + msg.author.mention)
        elif self.count[msg.author.id][1] == 5:
            ctx: Context = Context(message=res, prefix=self.bot.default_prefix)
            await ikaros.kick(ctx, msg.author, 0, reason + ', threat level 2')
        elif self.count[msg.author.id][1] == 7:
            ctx: Context = Context(message=res, prefix=self.bot.default_prefix)
            await ikaros.ban(ctx, msg.author, 0, reason + ', threat level 3')
        await asyncio.sleep(90)
        self.count[msg.author.id][1] -= 1
