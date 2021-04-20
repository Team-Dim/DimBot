import logging
from datetime import datetime

import discord
from aiohttp import ClientSession
from discord.ext import commands

import dimsecret
from echo import Bottas
from missile import Missile

lvl = logging.DEBUG if dimsecret.debug else logging.INFO


def get_logger(name: str) -> logging.Logger:
    """Returns a logger with the module name"""
    logger = logging.getLogger(name)
    logger.setLevel(lvl)
    ch = logging.StreamHandler()
    ch.setLevel(lvl)
    preformat = f'[{logger.name}]'
    # [%(threadName)s/%(levelname)s] = [MainThread/INFO]
    ch.setFormatter(logging.Formatter(fmt=preformat + ' %(levelname)s [%(asctime)s] %(message)s',
                                      datefmt='%H:%M:%S'))
    logger.addHandler(ch)
    return logger


async def append_msg(msg: discord.Message, content: str, delimiter: str = '\n'):
    await msg.edit(content=f'{msg.content}{delimiter}{content}')


class Bot(commands.Bot):

    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)
        self.default_prefix = 't.' if dimsecret.debug else 'd.'
        self.missile = Missile(self)  # Actually, just migrate Missile to this Bot class
        self.echo = Bottas(self)
        # Stores the message for the snipe command
        self.snipe = Embed(description='No one has deleted anything yet...')
        self.sch = None
        self.eggy = None  # Special Discordr user for d.hug
        self.invoke_time = None  # Time needed to process a command
        self.boot_time = datetime.now()  # Time when bot started
        self.session = ClientSession()  # Central session for all aiohttp client requests


class MsgExt:

    def __init__(self, msg: discord.Message, prefix: str = ''):
        self.msg = msg
        self.prefix = prefix + ' '

    async def send(self, content: str):
        await self.msg.channel.send(self.prefix + content)


class Embed(discord.Embed):

    def __init__(self, title=None, description=None, color=discord.Colour.random(), thumbnail: str = None, **kwargs):
        super().__init__(title=title, description=description, color=color, **kwargs)
        if thumbnail:
            super().set_thumbnail(url=thumbnail)


class Cog(commands.Cog):

    def __init__(self, bot, name):
        self.bot: Bot = bot
        self.logger = get_logger(name)
