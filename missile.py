import asyncio
import base64
import logging
import re
from datetime import datetime
from typing import Union

import aiosql
import aiosqlite
import discord
from aiohttp import ClientSession
from discord.ext import commands
from diminator.obj import PP

import dimsecret

__lvl__ = logging.DEBUG if dimsecret.debug else logging.INFO
ver = '0.10.24.3'


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


def encode(text: str) -> str:
    """Converts the given string to base64"""
    b: bytes = text.encode()
    encoded: bytes = base64.b64encode(b)
    return encoded.decode()


def decode(text: str) -> str:
    b: bytes = text.encode()
    decoded: bytes = base64.b64decode(b)
    return decoded.decode()

def underline(text: str, mag: int = 1) -> str:
    u_line = '_'*mag
    text = text.replace(u_line, '\\_'*mag)
    return u_line + text + u_line

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


def vc_only():
    """When a command has been invoked, check whether the author is in a voice channel"""

    async def check(ctx):
        if ctx.guild and ctx.author.voice:
            if not ctx.guild.me.voice or ctx.author.voice.channel == ctx.guild.me.voice.channel:
                return True
            await ctx.reply("I'm already in another voice channel!")
            return False
        await ctx.reply('You must join a server voice channel first!')
        return False

    return commands.check(check)


def bot_has_perm(**kwargs):
    async def check(ctx):
        remote = ctx.guild.me.permissions_in(ctx.channel)
        has = remote.is_superset(discord.Permissions(**kwargs))
        if not has and remote.send_messages:
            await ctx.reply(f"I'm missing permissions: {', '.join(kwargs.keys())}")
        return has

    return commands.check(check)


def is_mod():
    async def check(ctx):
        role = ctx.guild.get_role(await ctx.bot.sql.get_mod_role(ctx.bot.db, guild=ctx.guild.id))
        mod = role in ctx.author.roles or ctx.author.guild_permissions.manage_guild
        if not mod:
            await ctx.reply('You must be a moderator to execute this command!')
        return mod

    return commands.check(check)


def is_url(url: str):
    """Uses RegEx to check whether a string is a HTTP(s) link"""
    # https://stackoverflow.com/a/17773849/8314159
    return re.search(r"(https?://(?:www\.|(?!www))[a-zA-Z0-9][a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|www\.[a-zA-Z0-9]"
                     r"[a-zA-Z0-9-]+[a-zA-Z0-9]\.[^\s]{2,}|https?://(?:www\.|(?!www))[a-zA-Z0-9]+\.[^\s]{2,}"
                     r"|www\.[a-zA-Z0-9]+\.[^\s]{2,})", url)


async def prefix_process(bot, msg: discord.Message):
    """Function for discord.py to extract applicable prefix based on the message"""
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


class UserStore:
    """Stores user specific objects used by DimBot"""

    def __init__(self):
        self.last_xp_time: dict = {None: datetime.now()}
        self.pp: PP = None

    def get_last_xp_time(self, guild_id: int):
        if guild_id not in self.last_xp_time:
            self.last_xp_time[guild_id] = datetime.now()
        return self.last_xp_time[guild_id]


class Bot(commands.Bot):

    def __init__(self, **options):
        super().__init__(command_prefix=prefix_process, **options)
        self.default_prefix = 't.' if dimsecret.debug else 'd.'
        self.guild_store = {}
        self.sch = None
        self.boot_time = datetime.now()  # Time when bot started
        self.session = ClientSession()  # Central session for all aiohttp client requests
        # Initialise database connection
        self.db = None
        self.sql = aiosql.from_path('sql', 'aiosqlite')
        self.user_store: dict[int: UserStore] = {}
        self.arccore_typing = None
        self.ip = ''
        self.maintenance: bool = False
        self.status: discord.Status = discord.Status.online
        self.help_command = _Help()
        self.nickname = f"DimBot {'S ' if dimsecret.debug else ''}| {ver}"

    async def async_init(self):
        self.db = await aiosqlite.connect('DimBot.db')
        await self.db.execute('PRAGMA foreign_keys = ON')
        if dimsecret.debug:
            self.ip = 'http://localhost:4010/'
        else:
            async with self.session.get('http://169.254.169.254/latest/meta-data/public-ipv4') as r:
                self.ip = f"http://{await r.text()}:4010/"

    async def ask_msg(self, ctx, msg: str, timeout: int = 10):
        """Asks a follow-up question"""
        nene = self.get_cog('Nene')
        p = await ctx.reply(msg)
        nene.no_ai.append(p.id)
        r = None
        # Waits for the time specified
        try:
            reply = await self.wait_for(
                'message', timeout=timeout,
                # Checks whether mess is replying to p
                check=lambda mess: mess.reference and mess.reference.cached_message == p)
            r = reply.content
        except asyncio.TimeoutError:
            pass
        nene.no_ai.remove(p.id)
        return r

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

    def get_user_store(self, uid: int) -> UserStore:
        """Asserts a UserStore instance for the user"""
        if uid not in self.user_store.keys():
            self.user_store[uid] = UserStore()
        return self.user_store[uid]

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


class _Help(commands.HelpCommand):

    def __init__(self):
        super().__init__(verify_checks=False)

    async def send_bot_help(self, mapping: dict):
        embed = Embed('Modules')
        for cog in tuple(mapping.keys())[:-1]:
            embed.description += f'**{cog.qualified_name}**: {cog.description.split("Version")[0]}'
        embed.description += "\n__Commands that don't belong to any modules:__"
        for cmd in filter(lambda c: not c.cog, self.context.bot.commands):
            embed.description += f'\n`{cmd.name}`: {cmd.brief}'
        embed.set_author(name='Click me for Wiki',
                         url='https://github.com/TCLRainbow/DimBot-Wiki/blob/master/README.md')
        await self.context.reply(
            f"Send `{await self.context.bot.get_prefix(self.context.message)}help <module/command>`!",
            embed=embed
        )

    async def send_cog_help(self, cog: commands.Cog):
        embed = Embed('Commands in ' + cog.qualified_name)
        for cmd in cog.walk_commands():
            embed.description += f'**{cmd.name}**: {cmd.brief}\n'
        embed.set_footer(text='Version ' + cog.description.split('Version')[1])
        await self.context.reply(
            f"Send `{await self.context.bot.get_prefix(self.context.message)}help <command>`!",
            embed=embed
        )

    async def send_group_help(self, group: commands.Group):
        embed = Embed(group.short_doc, group.help if group.help != group.short_doc else '')
        embed.description += '\n\nSubcommands:\n'
        for cmd in group.walk_commands():
            embed.description += f'**{cmd.name}**: {cmd.short_doc}\n'
        if group.aliases:
            embed.add_field('Aliases', ', '.join(group.aliases))
        await self.context.reply(embed=embed)

    async def send_command_help(self, cmd: commands.Command):
        embed = Embed(cmd.short_doc, cmd.help if cmd.help != cmd.short_doc else '')
        if cmd.aliases:
            embed.add_field('Aliases', ', '.join(cmd.aliases))
        await self.context.reply(embed=embed)
