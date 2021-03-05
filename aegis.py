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
    Version 0.2"""

    def __init__(self, bot):
        self.bot = bot
        self.count = {}

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.author.bot or msg.channel.id == 723153902454964224:
            return
        if len(msg.raw_mentions) > 5:
            aegis_msg = await send(msg.channel, f'Detected mass ping ({len(msg.raw_mentions)})')
            if msg.author.top_role >= msg.guild.me.top_role or Missile.is_rainbow(msg.author.id):
                await Missile.append_message(aegis_msg, 'Cannot lock target.')
                return
            await msg.author.ban(reason='Aegis: Mass ping detected')
            await send(msg.channel, 'Banned ' + msg.author.mention)
        if msg.author.id not in self.count:
            self.count[msg.author.id] = [[], [], 0]
        self.count[msg.author.id][0].append(self.bot.loop.create_task(self.fast_spam_1(msg)))
        self.count[msg.author.id][1].append(self.bot.loop.create_task(self.fast_spam_5(msg)))

    async def fast_spam_1(self, msg: discord.Message):
        # print('Fast spam I', len(self.count[msg.author.id][0]))
        if len(self.count[msg.author.id][0]) == 3:
            self.count[msg.author.id][2] += 1
            res = await send(msg.channel, 'Detected fast spam, type I. Warn: ' + str(self.count[msg.author.id][2]))
            for task in self.count[msg.author.id][1]:
                task.cancel()
            self.count[msg.author.id][1] = []
            self.bot.loop.create_task(self.act(msg, res))
            for task in self.count[msg.author.id][0]:
                task.cancel()
            self.count[msg.author.id][0] = []
        else:
            await asyncio.sleep(1)
            self.count[msg.author.id][0].pop(0)

    async def fast_spam_5(self, msg: discord.Message):
        # print('Fast spam V', len(self.count[msg.author.id][1]))
        if len(self.count[msg.author.id][1]) == 5:
            self.count[msg.author.id][2] += 1
            res = await send(msg.channel, 'Detected fast spam, type V. Warn: ' + str(self.count[msg.author.id][2]))
            for task in self.count[msg.author.id][0]:
                task.cancel()
            self.count[msg.author.id][0] = []
            self.bot.loop.create_task(self.act(msg, res))
            for task in self.count[msg.author.id][1]:
                task.cancel()
            self.count[msg.author.id][1] = []
        else:
            await asyncio.sleep(5)
            self.count[msg.author.id][1].pop(0)

    async def act(self, msg: discord.Message, res: discord.Message):
        # print(self.count[msg.author.id][2])
        if self.count[msg.author.id][2] == 3:
            role = None
            if msg.guild.id == bitbay.__guild_id__:
                role = msg.guild.get_role(718210713893601301)  # Muted Pirate
            elif msg.guild == self.bot.missile.guild:
                role = msg.guild.get_role(474578007156326412)  # Asteroid Belt
            if role:
                await msg.author.add_roles(role, reason='Aegis: Detected fast ping, threat level 1')
                await Missile.append_message(res, 'Muted')
                await asyncio.sleep(10)
                await msg.author.remove_roles(role, reason='Aegis: Deactivating level 1')
                await send(msg.channel, "Unmuted " + msg.author.mention)
        elif self.count[msg.author.id][2] == 5:
            ctx: Context = Context(message=res, prefix=self.bot.default_prefix)
            await ikaros.kick(ctx, msg.author, 0, 'Aegis: Detected fast ping, threat level 2')
        elif self.count[msg.author.id][2] == 7:
            ctx: Context = Context(message=res, prefix=self.bot.default_prefix)
            await ikaros.ban(ctx, msg.author, 0, 'Aegis: Detected fast ping, threat level 3')
        await asyncio.sleep(90)
        self.count[msg.author.id][2] -= 1
