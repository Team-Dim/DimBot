import asyncio
import re
from typing import Optional

import discord
from discord.ext import commands

import obj

dim_id = 264756129916125184


class Missile:
    """A class to store variables that are shared between different modules"""

    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot

    @staticmethod
    # similar to @commands.is_owner()
    def is_rainbow_cmd_check(msg: str = 'I guess you are not my little pog champ :3'):
        """When a command has been invoked, checks whether the sender is me, and reply msg if it is not."""

        async def check(ctx):
            rainbow = ctx.author.id == ctx.bot.owner_id
            if not rainbow:
                await ctx.send(msg)
            return rainbow

        return commands.check(check)

    @staticmethod
    def is_channel_owner_cmd_check():
        """When a command has been invoked, checks whether the sender is the owner of that text channel."""

        async def check(ctx):
            if ctx.guild:
                owner = ctx.author == ctx.guild.owner
                if not owner:
                    await ctx.send("I guess you are not this server's pogchamp. Bruh.")
                return owner
            return True

        return commands.check(check)

    @staticmethod
    def guild_only():
        """When a command has been invoked, checks whether it is sent in a server"""

        async def check(ctx):
            if ctx.guild:  # In a server
                return True
            await ctx.send('This command is only available in servers!')
            return False

        return commands.check(check)

    @staticmethod
    def regex_is_url(url: str):
        """Uses RegEx to check whether a string is a HTTP(s) link"""
        # https://stackoverflow.com/a/17773849/8314159
        return re.search(r"(https?://(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9]"
                         r"[a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?://(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}"
                         r"|www\.[a-zA-Z0-9]+\.[^\s]{2,})", url)

    async def ask_msg(self, ctx, msg: str, timeout: int = 10) -> Optional[str]:
        """Asks a follow-up question"""
        await ctx.send(msg)
        # Waits for the time specified
        try:
            reply = await self.bot.wait_for(
                'message', timeout=timeout,
                # Checks whether the message is sent by the same author and in the same channel.
                check=lambda mess: mess.author.id == ctx.author.id and mess.channel == ctx.channel)
            return reply.content
        except asyncio.TimeoutError:
            return None

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
