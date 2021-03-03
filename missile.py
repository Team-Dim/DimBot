import logging
import re
from random import randint

import discord
from discord.ext import commands

import dimsecret


class Missile:
    """A class to store variables that are shared between different modules."""

    # noinspection PyTypeChecker
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        # Set the logger level based on debug
        if dimsecret.debug:
            self.lvl = logging.DEBUG
        else:
            self.lvl = logging.INFO
        self.guild = None  # My own server
        self.bottyland: discord.TextChannel = None  # A channel in my server that is used for bot debugging
        self.announcement: discord.TextChannel = None  # Announcement channel in my server
        self.logs: discord.TextChannel = None  # Log channel in my server
        self.new = True  # For DimBot change activity loop
        # Stores the message for snipe command
        self.snipe: discord.Embed = discord.Embed(description='No one has deleted anything yet...')
        self.ghost_pings = {}  # Ghost ping cache

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
        return discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))

    @staticmethod
    def is_rainbow(ctx):
        """Is it me?"""
        return ctx.author.id == 264756129916125184

    @staticmethod
    # similar to @commands.is_owner()
    def is_rainbow_cmd_check(msg: str = 'You are not the bot owner.'):
        """When a command has been invoked, checks whether the sender is me, and reply msg if it is not."""
        async def check(ctx):
            rainbow = Missile.is_rainbow(ctx)
            if not rainbow:
                await ctx.send(msg)
            return rainbow
        return commands.check(check)

    @staticmethod
    def is_channel_owner_cmd_check():
        """When a command has been invoked, checks whether the sender is the owner of that text channel."""
        async def check(ctx):
            if ctx.guild:  # Message is in a server
                owner = ctx.author == ctx.guild.owner
                # Checks whether the sender is the server owner (which owns the channel)
                if not owner:
                    await ctx.send("I guess you are not this server's pogchamp. Bruh.")
                return owner
            # If it is not in a server, then it is a private message, which the sender is always the channel owner.
            return True
        return commands.check(check)

    @staticmethod
    def regex_is_url(url: str):
        """Uses RegEx to check whether a string is a URL."""
        return re.search(r"[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)", url)

    async def ask_msg(self, ctx, msg: str, timeout: int = 10) -> str:
        """Asks a follow-up question"""
        await ctx.send(msg)
        # Waits for the time specified
        reply = await self.bot.wait_for('message', timeout=timeout, check=self.check_same_author_and_channel(ctx))
        return reply.content
