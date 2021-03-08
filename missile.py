import logging
import re
from random import randint

import discord
from discord.ext import commands

import dimsecret


class Missile:

    # noinspection PyTypeChecker
    # TODO: ^ Remove when wait_for_ready() port finishes
    def __init__(self, bot: commands.Bot):
        self.bot: commands.Bot = bot
        if dimsecret.debug:
            self.lvl = logging.DEBUG
        else:
            self.lvl = logging.INFO
        self.guild = None
        self.bottyland: discord.TextChannel = None
        self.announcement: discord.TextChannel = None
        self.logs: discord.TextChannel = None
        self.loop = False
        self.snipe: discord.Embed = discord.Embed(description='No one has deleted anything yet...',
                                                  color=Missile.random_rgb())
        self.ghost_pings = {}
        self.sch = None
        self.eggy: discord.User = None

    def get_logger(self, name: str) -> logging.Logger:
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
        await msg.edit(content=f'{msg.content}{delimiter}{append_content}')

    @staticmethod
    def check_same_author_and_channel(ctx):
        return lambda msg: msg.author.id == ctx.author.id and msg.channel == ctx.channel

    @staticmethod
    def random_rgb():
        return discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))

    @staticmethod
    def is_rainbow(uid: int):
        return uid == 264756129916125184

    @staticmethod
    # similar to @commands.is_owner()
    def is_rainbow_cmd_check(msg: str = 'I guess you are not my little pog champ :3'):
        async def check(ctx):
            rainbow = Missile.is_rainbow(ctx.author.id)
            if not rainbow:
                await ctx.send(msg)
            return rainbow
        return commands.check(check)

    @staticmethod
    def is_channel_owner_cmd_check():
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
        async def check(ctx):
            if ctx.guild:
                return True
            await ctx.send('This command is only available in servers!')
            return False
        return commands.check(check)

    @staticmethod
    def regex_is_url(url: str):
        return re.search(r"[-a-zA-Z0-9@:%._+~#=]{1,256}\.[a-zA-Z0-9()]{1,6}\b([-a-zA-Z0-9()@:%_+.~#?&/=]*)", url)

    async def ask_msg(self, ctx, msg: str, timeout: int = 10) -> str:
        await ctx.send(msg)
        reply = await self.bot.wait_for('message', timeout=timeout, check=self.check_same_author_and_channel(ctx))
        return reply.content
