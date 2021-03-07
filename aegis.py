import asyncio

import discord
from discord.ext.commands import Cog

import bitbay
import ikaros


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
            self.count[msg.author.id] = [[], 0]
        raw_mention_count = len(msg.raw_mentions)
        if raw_mention_count >= 5:
            self.count[msg.author.id][1] += 1
            await send(msg.channel, f'Detected mass ping ({raw_mention_count}). Warn: {self.count[msg.author.id][1]}')
            self.bot.loop.create_task(self.act(msg, 'Aegis: Mass ping'))
        else:
            ml = len(self.count[msg.author.id][0])
            if ml == 4:
                if (msg.created_at - self.count[msg.author.id][0][0]).total_seconds() < 5:
                    self.count[msg.author.id][1] += 1
                    await send(msg.channel, 'Detected spam, type V. Warn: ' + str(self.count[msg.author.id][1]))
                    self.count[msg.author.id][0] = []
                    self.bot.loop.create_task(self.act(msg, 'Aegis: Spam, type V'))
                else:
                    self.count[msg.author.id][0].pop(0)
            ml = len(self.count[msg.author.id][0])
            if ml > 1 > (msg.created_at - self.count[msg.author.id][0][ml - 2]).total_seconds():
                self.count[msg.author.id][1] += 1
                await send(msg.channel, 'Detected spam, type I. Warn: ' + str(self.count[msg.author.id][1]))
                self.count[msg.author.id][0] = []
                self.bot.loop.create_task(self.act(msg, 'Aegis: Spam, type I'))
            for t in self.count[msg.author.id][0]:
                if (msg.created_at - t).total_seconds() >= 5:
                    self.count[msg.author.id][0].pop(0)
            self.count[msg.author.id][0].append(msg.created_at)

    async def act(self, msg: discord.Message, reason: str):
        if self.count[msg.author.id][1] == 3:
            await ikaros.mute(msg, msg.author, 10, 0, reason + ', threat level 1')
        elif self.count[msg.author.id][1] == 5:
            await ikaros.kick(msg, msg.author, 0, reason + ', threat level 2')
        elif self.count[msg.author.id][1] == 7:
            await ikaros.ban(msg, msg.author, 0, reason + ', threat level 3')
        await asyncio.sleep(90)
        self.count[msg.author.id][1] -= 1
