import asyncio

import discord
from discord.ext.commands import Cog

from missile import Missile


class Aegis(Cog):
    """AutoMod system
    Version 0.1"""

    def __init__(self, bot):
        self.bot = bot
        self.count = {}

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        if len(msg.raw_mentions) > 5:
            aegis_msg = await msg.channel.send(f'**Aegis**: Detected mass ping ({len(msg.raw_mentions)})')
            if msg.author.top_role >= msg.guild.me.top_role or Missile.is_rainbow(msg.author.id):
                await Missile.append_message(aegis_msg, 'Cannot lock target.')
                return
            await msg.author.ban(reason='Aegis: Mass ping detected')
            await msg.channel.send('Banned ' + msg.author.mention)
        if msg.author.id not in self.count:
            self.count[msg.author.id] = [[], []]
        self.count[msg.author.id][0].append(self.bot.loop.create_task(self.fast_spam_1(msg)))
        self.count[msg.author.id][1].append(self.bot.loop.create_task(self.fast_spam_5(msg)))

    async def fast_spam_1(self, msg: discord.Message):
        print('Fast spam I', len(self.count[msg.author.id][0]))
        if len(self.count[msg.author.id][0]) == 3:
            await msg.channel.send('**Aegis** Detected fast spam, type I.<@264756129916125184>\nNo actions will be taken for now.')
            self.count[msg.author.id][1] = []
        await asyncio.sleep(1)
        self.count[msg.author.id][0] = []

    async def fast_spam_5(self, msg: discord.Message):
        print('Fast spam V', len(self.count[msg.author.id][1]))
        if len(self.count[msg.author.id][1]) == 5:
            await msg.channel.send('**Aegis** Detected fast spam, type V.<@264756129916125184>\nNo actions will be taken for now.')
        await asyncio.sleep(5)
        self.count[msg.author.id][1] = []
