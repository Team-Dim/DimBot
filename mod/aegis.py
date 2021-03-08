import asyncio

import discord
from discord.ext.commands import Cog

import bitbay
import ikaros


async def send(ch: discord.TextChannel, content: str):
    """Appends Aegis to the message and sends it"""
    return await ch.send('**Aegis:** ' + content)


class Aegis(Cog):
    """AutoMod system
    Version 0.3"""

    def __init__(self, bot):
        self.bot = bot
        self.count = {}

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        # Check whether message needs to be scanned by Aegis
        if not msg.guild or msg.author.bot or msg.channel.id == bitbay.spam_ch_id:
            return
        if msg.author.id not in self.count:  # Creates record for the message author
            self.count[msg.author.id] = [[], 0]  # [Tracked messages, warn count]
        raw_mention_count = len(msg.raw_mentions)
        if raw_mention_count >= 5:  # Mass ping
            self.count[msg.author.id][1] += 1
            await send(msg.channel, f'Detected mass ping ({raw_mention_count}). Warn: {self.count[msg.author.id][1]}')
            self.bot.loop.create_task(self.act(msg, 'Aegis: Mass ping'))
        else:
            ml = len(self.count[msg.author.id][0])
            if ml == 4:  # There are 4 previous messages
                if (msg.created_at - self.count[msg.author.id][0][0]).total_seconds() < 5:  # 5 msg in 5s
                    self.count[msg.author.id][1] += 1
                    await send(msg.channel, 'Detected spam, type V. Warn: ' + str(self.count[msg.author.id][1]))
                    self.count[msg.author.id][0] = []
                    self.bot.loop.create_task(self.act(msg, 'Aegis: Spam, type V'))
                else:
                    self.count[msg.author.id][0].pop(0)  # We only track up to 5 previous messages
            ml = len(self.count[msg.author.id][0])
            if ml > 1 > (msg.created_at - self.count[msg.author.id][0][ml - 2]).total_seconds():  # 3 msg in 1s
                self.count[msg.author.id][1] += 1
                await send(msg.channel, 'Detected spam, type I. Warn: ' + str(self.count[msg.author.id][1]))
                self.count[msg.author.id][0] = []
                self.bot.loop.create_task(self.act(msg, 'Aegis: Spam, type I'))
            for t in self.count[msg.author.id][0]:  # If previous messages are >5s older than current, purge cache
                if (msg.created_at - t).total_seconds() >= 5:
                    self.count[msg.author.id][0].pop(0)
            self.count[msg.author.id][0].append(msg.created_at)  # Add current message for tracking

    async def act(self, msg: discord.Message, reason: str):
        """Takes action"""
        if self.count[msg.author.id][1] == 3:  # 3 warns in the past 90s
            await ikaros.mute(msg, msg.author, 10, 0, reason + ', threat level 1')  # 10s mute
        elif self.count[msg.author.id][1] == 4:  # 4 warns in the past 90s
            await ikaros.kick(msg, msg.author, 0, reason + ', threat level 2')  # Immediate kick
        elif self.count[msg.author.id][1] == 5:  # 5 warns in the past 90s
            await ikaros.ban(msg, msg.author, 0, reason + ', threat level 3')  # Immediate ban
        await asyncio.sleep(90)  # Reduces total warn count by 1 after 90s
        self.count[msg.author.id][1] -= 1
