import asyncio
import logging
import re
from typing import Optional

import discord
from discord.ext import commands

import dimsecret

dim_id = 264756129916125184


class Missile:
    """A class to store variables that are shared between different modules"""

    # noinspection PyTypeChecker
    # TODO: ^ Remove when wait_for_ready() port finishes
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        if dimsecret.debug:
            self.lvl = logging.DEBUG
        else:
            self.lvl = logging.INFO
        self.guild = None  # My own server
        self.announcement: discord.TextChannel = None  # Announcement channel in my server
        self.logs: discord.TextChannel = None  # Log channel in my server
        # Stores the message for snipe command
        self.snipe: discord.Embed = discord.Embed(description='No one has deleted anything yet...',
                                                  color=Missile.random_rgb())
        self.sch = None
        self.eggy: discord.User = None  # Special Discord user for hug

    def get_logger(self, name: str) -> logging.Logger:
        """Returns a logger with the module name"""
        logger = logging.getLogger(name)
        logger.setLevel(self.lvl)
        ch = logging.StreamHandler()
        ch.setLevel(self.lvl)
        preformat = f'[{logger.name}]'
        # [%(threadName)s/%(levelname)s] = [MainThread/INFO]
        ch.setFormatter(logging.Formatter(fmt=preformat + ' %(levelname)s [%(asctime)s] %(message)s',
                                          datefmt='%H:%M:%S'))
        logger.addHandler(ch)
        return logger

    @staticmethod
    async def append_message(msg: discord.Message, append_content: str, delimiter: str = '\n'):
        """Appends content to a message"""
        await msg.edit(content=f'{msg.content}{delimiter}{append_content}')

    @staticmethod
    def check_same_author_and_channel(ctx):
        """Checks whether the message is sent by the same author and in the same channel.
            Used when the bot needs further response from the user"""
        return lambda msg: msg.author.id == ctx.author.id and msg.channel == ctx.channel

    @staticmethod
    def random_rgb():
        """Generates a random color"""
        # TODO: Remove this method
        return discord.Colour.random()

    @staticmethod
    def is_rainbow(uid: int):
        """Is it me?"""
        return uid == dim_id

    @staticmethod
    # similar to @commands.is_owner()
    def is_rainbow_cmd_check(msg: str = 'I guess you are not my little pog champ :3'):
        """When a command has been invoked, checks whether the sender is me, and reply msg if it is not."""

        async def check(ctx):
            rainbow = Missile.is_rainbow(ctx.author.id)
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
        """Uses RegEx to check whether a string is a URL"""
        return re.search(r"[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)", url)

    async def ask_msg(self, ctx, msg: str, timeout: int = 10) -> Optional[str]:
        """Asks a follow-up question"""
        await ctx.send(msg)
        # Waits for the time specified
        try:
            reply = await self.bot.wait_for('message', timeout=timeout, check=self.check_same_author_and_channel(ctx))
            return reply.content
        except asyncio.TimeoutError:
            return None

    @staticmethod
    async def prefix_process(bot: commands.Bot, msg: discord.Message):
        """Function for discord.py to extract applicable prefix based on the message"""
        tag_mention = re.search(f'^((<@.?{bot.user.id}> |DimBot), )', msg.content)
        if tag_mention:
            if Missile.is_rainbow(msg.author.id):
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