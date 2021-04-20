import asyncio
import re

import discord
from discord.ext import commands


class Missile:
    """A class to store variables that are shared between different modules"""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @staticmethod
    async def prefix_process(bot, msg: discord.Message):
        """Function for discord.py to extract applicable prefix based on the message"""
        tag_mention = re.search(f'^((<@.?{bot.user.id}> |DimBot), )', msg.content)
        if tag_mention:
            if msg.author.id == bot.owner_id:
                return tag_mention.group(0)  # Only I can use 'DimBot, xxx' or '@DimBot , xxx'
            else:
                await msg.reply('Only my little pog champ can use authoritative orders!')
        return bot.default_prefix

    async def ask_reaction(self, ctx: commands.Context, ask: str, emoji: str = '✅') -> bool:
        q = await ctx.send(ask)
        await q.add_reaction(emoji)

        def check(reaction, user):
            return user == ctx.author and str(reaction.emoji) == emoji

        try:
            await self.bot.wait_for('reaction_add', timeout=10, check=check)
            return True
        except asyncio.TimeoutError:
            return False

    @staticmethod
    def ensure_index_value(collection, index, default=None):
        try:
            return collection[index]
        except IndexError or KeyError:
            return default

    @staticmethod
    def is_guild_cmd_check(*guilds):
        """When a command has been invoked, checks whether the invoked channel is in one of the guilds"""

        async def check(ctx):
            async def no_guild():
                msg = 'The command can only be executed in these servers:'
                for guild in guilds:
                    msg += f"\n**{ctx.bot.get_guild(guild).name if ctx.bot.get_guild(guild) else '⚠ Unknown server'}**"
                await ctx.send(msg)

            if ctx.guild:
                is_guild = ctx.guild.id in guilds
                if not is_guild:
                    await no_guild()
                return is_guild
            await no_guild()
            return False

        return commands.check(check)
