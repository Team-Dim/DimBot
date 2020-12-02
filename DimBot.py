import asyncio
import platform
from random import choice

import boto3
import discord
from discord.ext import commands

import norris
import dimsecret
import bottas
import ricciardo
import hamilton
from bruckserver import verstapen, albon
from missile import Missile

# NEA: Create more tables for db, create custom polymorphism

bot = commands.Bot(command_prefix='d.')
bot.missile = Missile(bot)

nickname = "DimBot"
version = 'v0.6.5'
activities = [
    discord.Activity(name='Echo', type=discord.ActivityType.listening),
    discord.Activity(name='Lokeon', type=discord.ActivityType.listening),
    discord.Activity(name='Ricizus screaming', type=discord.ActivityType.listening),
    discord.Activity(name='Rainbow codes', type=discord.ActivityType.watching),
    discord.Activity(name='Rainbow laughs', type=discord.ActivityType.watching),
    discord.Activity(name='comics', type=discord.ActivityType.watching),
    discord.Activity(name='Terry coughing', type=discord.ActivityType.listening),
    discord.Activity(name='Bruck sleeps', type=discord.ActivityType.watching)
]

if dimsecret.debug:
    nickname += f' [{version}]'
    news_ch = announcement_ch = 372386868236386307
else:
    nickname += f' {{{version}}}'
    news_ch = 581699408870113310
    announcement_ch = 425703064733876225

logger = bot.missile.get_logger('DimBot')
with open('.git/HEAD', 'r') as f:
    branch = f.readline().split('/')[-1]


@bot.command(aliases=['ver', 'verinfo'])
async def info(ctx):
    await ctx.send(
        f'Guild count: **{len(bot.guilds)}** | Debug mode: **{dimsecret.debug}** | Branch: **{branch}**\n'
        f'This bot is coded with the programming language Python `{platform.python_version()}`\n'
        f'It interacts with Discord via discord.py `{discord.__version__}`, '
        f'Amazon Web Services via boto3 `{boto3.__version__}`.\n'
        'Bot source code: https://github.com/TCLRainbow/DimBot\n\n'
        'This bot has the following modules:\n'
        f'**Project Ricciardo** `{ricciardo.__version__}`: Subscribe to multiple RSS feed and send them to discord channels.\n'
        f'**Project Bottas** `{bottas.__version__}`: Add or search quotes through a SQL database.\n'
        f'**Project Hamilton** `{hamilton.__version__}`: Adds additional feature per role\n'
        f'**Project Verstapen** `{verstapen.__version__}`: Connects to AWS and manage a minecraft server instance.\n'
        f'**Project Albon** `{albon.__version__}`: HTTP server sub-project used by `Vireg`.\n'
        f'**Project Norris** `{norris.__version__}` : Chat bot for answering BBM questions\n'
    )


def is_debug(ctx):
    return dimsecret.debug


@bot.event
async def on_ready():
    bot.missile.guild = bot.get_guild(285366651312930817)
    bot.missile.bottyland = bot.get_channel(372386868236386307)
    bot.missile.bruck_ch = bot.get_channel(688948118712090644)
    bot.missile.newsfeed = bot.get_channel(news_ch)
    bot.missile.announcement = bot.get_channel(announcement_ch)
    bot.missile.logs = bot.get_channel(384636771805298689)
    logger.info(f'Guild count: {len(bot.guilds)}')
    for guild in bot.guilds:
        if guild.me.nick != nickname:
            await guild.me.edit(nick=nickname)
    if bot.missile.new:
        bot.missile.new = False
        while True:
            logger.debug('Changed activity')
            await bot.change_presence(activity=choice(activities))
            await asyncio.sleep(300)


@bot.event
async def on_disconnect():
    bot.missile.new = True


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.BadArgument):
        await ctx.send('Bad argument.')


bot.add_cog(ricciardo.Ricciardo(bot))
bot.add_cog(hamilton.Hamilton(bot))
bot.add_cog(verstapen.Verstapen(bot))
bot.add_cog(bottas.Bottas(bot))
bot.add_cog(norris.Norris(bot))
bot.run(dimsecret.discord)
