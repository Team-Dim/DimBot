import asyncio
import logging
import re
from datetime import datetime
from typing import Union

import aiosql
import aiosqlite
import discord
from aiohttp import ClientSession
from discord.ext import commands

import dimsecret

__lvl__ = logging.DEBUG if dimsecret.debug else logging.INFO


def get_logger(name: str) -> logging.Logger:
    """Returns a logger with the module name"""
    logger = logging.getLogger(name)
    logger.setLevel(__lvl__)
    ch = logging.StreamHandler()
    ch.setLevel(__lvl__)
    preformat = f'[{logger.name}]'
    # [%(threadName)s/%(levelname)s] = [MainThread/INFO]
    ch.setFormatter(logging.Formatter(fmt=preformat + ' %(levelname)s [%(asctime)s] %(message)s',
                                      datefmt='%H:%M:%S'))
    logger.addHandler(ch)
    return logger


async def append_msg(msg: discord.Message, content: str, delimiter: str = '\n'):
    await msg.edit(content=f'{msg.content}{delimiter}{content}')


# similar to @commands.is_owner()
def is_rainbow(msg: str = 'I guess you are not my little pog champ :3'):
    """When a command has been invoked, checks whether the sender is me, and reply msg if it is not."""

    async def check(ctx):
        rainbow = ctx.author.id == ctx.bot.owner_id
        if not rainbow:
            await ctx.send(msg)
        return rainbow

    return commands.check(check)


def is_channel_owner():
    """When a command has been invoked, checks whether the sender is the owner of that text channel."""

    async def check(ctx):
        if ctx.guild:
            owner = ctx.author == ctx.guild.owner
            if not owner:
                await ctx.send("I guess you are not this server's pogchamp. Bruh.")
            return owner
        return True

    return commands.check(check)


def guild_only():
    """When a command has been invoked, checks whether it is sent in a server"""

    async def check(ctx):
        if ctx.guild:  # In a server
            return True
        await ctx.send('This command is only available in servers!')
        return False

    return commands.check(check)


def is_url(url: str):
    """Uses RegEx to check whether a string is a HTTP(s) link"""
    # https://stackoverflow.com/a/17773849/8314159
    return re.search(r"(https?://(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9]"
                     r"[a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?://(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}"
                     r"|www\.[a-zA-Z0-9]+\.[^\s]{2,})", url)


async def prefix_process(bot, msg: discord.Message):
    """Function for discord.py to extract applicable prefix based on the message"""
    tag_mention = re.search(f'^(<@!{bot.user.id}>,? |DimBot, )', msg.content)
    if tag_mention:
        if msg.author.id == bot.owner_id:  # Only I can use 'DimBot, xxx' or '@DimBot xxx'
            return tag_mention.group(0)
        else:
            await msg.reply('Only my little pog champ can use authoritative orders!')
            return ''
    if msg.guild:
        g_prefix = await bot.sql.get_guild_prefix(bot.db, guildID=msg.guild.id)
        if g_prefix:
            return g_prefix, bot.default_prefix
    return bot.default_prefix


def in_guilds(*guilds):
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


async def check_arg(ctx, arg: str, user_mention=True, newline=True):
    if user_mention and '<@' in arg:
        await ctx.reply("You can't mention others!")
        raise commands.errors.CheckFailure
    if newline and '\n' in arg:
        await ctx.reply('It should only be a single line!')
        raise commands.errors.CheckFailure


class Bot(commands.Bot):

    def __init__(self, **options):
        super().__init__(command_prefix=prefix_process, **options)
        self.default_prefix = 't.' if dimsecret.debug else 'd.'
        # Stores the message for the snipe command
        self.snipe = Embed(description='No one has deleted anything yet...')
        self.sch = None
        self.eggy = None  # Special Discord user for d.hug
        self.invoke_time = None  # Time needed to process a command
        self.boot_time = datetime.now()  # Time when bot started
        self.session = ClientSession()  # Central session for all aiohttp client requests
        # Initialise database connection
        self.db = None
        self.sql = aiosql.from_path('sql', 'aiosqlite')
        self._user_store = {}
        self.arccore_typing = None
        self.ip = ''
        self.maintenance: bool = False
        self.status: discord.Status = discord.Status.online
        # self.help_command = _Help()
        self.help_command = commands.DefaultHelpCommand(verify_checks=False)

    async def async_init(self):
        self.db = await aiosqlite.connect('DimBot.db')
        if dimsecret.debug:
            self.ip = 'http://localhost/'
        else:
            async with self.session.get('http://169.254.169.254/latest/meta-data/public-ipv4') as r:
                self.ip = f"http://{await r.text()}/"

    async def ask_msg(self, ctx, msg: str, timeout: int = 10):
        """Asks a follow-up question"""
        await ctx.send(msg)
        # Waits for the time specified
        try:
            reply = await self.wait_for(
                'message', timeout=timeout,
                # Checks whether the message is sent by the same author and in the same channel.
                check=lambda mess: mess.author.id == ctx.author.id and mess.channel == ctx.channel)
            return reply.content
        except asyncio.TimeoutError:
            return None

    async def ask_reaction(self, ctx: commands.Context, ask: str, emoji: str = '✅', timeout: int = 10) -> bool:
        q = await ctx.send(ask)
        await q.add_reaction(emoji)

        try:
            await self.wait_for('reaction_add', timeout=timeout,
                                check=lambda reaction, user:
                                user == ctx.author and str(reaction.emoji) == emoji and reaction.message == q)

            return True
        except asyncio.TimeoutError:
            await append_msg(q, f'Timed out ({timeout})s')
            return False

    def user_store(self, uid: int):
        """Asserts a UserStore instance for the user"""
        if uid not in self._user_store.keys():
            self._user_store[uid] = UserStore()
        return self._user_store[uid]

    async def ensure_user(self, uid: int):
        """Ensures that a discord.User will be returned"""
        user = self.get_user(uid)
        if user:
            return user
        return await self.fetch_user(uid)


class MsgExt:

    def __init__(self, prefix: str = ''):
        self.prefix = f'**{prefix}:** '

    async def send(self, msg: Union[discord.Message, commands.Context], content: str):
        return await msg.channel.send(self.prefix + content)

    async def reply(self, msg: Union[discord.Message, commands.Context], content: str):
        return await msg.reply(self.prefix + content)


class Embed(discord.Embed):

    def __init__(self, title='', description='', color=None, thumbnail: str = None, **kwargs):
        if not color:
            color = discord.Color.random()
        super().__init__(title=title, description=description, color=color, **kwargs)
        if thumbnail:
            super().set_thumbnail(url=thumbnail)

    def add_field(self, name, value, inline=True):
        super().add_field(name=name, value=value, inline=inline)


class Cog(commands.Cog):

    def __init__(self, bot, name):
        self.bot: Bot = bot
        self.logger = get_logger(name)


class UserStore:
    """Stores user specific objects used by DimBot"""

    def __init__(self):
        self.last_xp_time: dict = {None: datetime.now()}

    def get_last_xp_time(self, guild_id: int):
        if guild_id not in self.last_xp_time:
            self.last_xp_time[guild_id] = datetime.now()
        return self.last_xp_time[guild_id]


class _Help(commands.HelpCommand):

    def __init__(self):
        super().__init__(verify_checks=False)
