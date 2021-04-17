import discord
from discord.ext import commands

import dimsecret
from echo import Bottas
from missile import Missile


class Bot(commands.Bot):

    def __init__(self, command_prefix, **options):
        super().__init__(command_prefix, **options)
        self.default_prefix = 't.' if dimsecret.debug else 'd.'
        self.missile = Missile(self)  # Actually, just migrate Missile to this Bot class
        self.echo = Bottas(self)


class MsgExt:

    def __init__(self, msg: discord.Message, prefix: str = ''):
        self.msg = msg
        self.prefix = prefix + ' '

    async def append(self, content: str, delimiter: str = '\n'):
        await self.msg.edit(content=f'{self.msg.content}{delimiter}{content}')

    async def send(self, content: str):
        await self.msg.channel.send(self.prefix + content)

