import logging

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
        self.new = True  # For DimBot change activity loop
        self.snipe: discord.Embed = None
        self.ghost_pings = {}

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
    # similar to @commands.is_owner()
    def is_rainbow():
        async def check(ctx):
            rainbow = ctx.author.id == 264756129916125184
            if not rainbow:
                await ctx.send('I guess you are not my little pog champ :3')
            return rainbow
        return commands.check(check)

    @staticmethod
    def is_channel_owner():
        async def check(ctx):
            if ctx.guild:
                owner = ctx.author == ctx.guild.owner
                if not owner:
                    await ctx.send("I guess you are not this server's pogchamp. Bruh.")
                return owner
            return True
        return commands.check(check)

    async def ask_msg(self, ctx, msg: str, timeout: int = 10) -> str:
        await ctx.send(msg)
        reply = await self.bot.wait_for('message', timeout=timeout, check=self.check_same_author_and_channel(ctx))
        return reply.content
