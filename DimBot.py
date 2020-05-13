import json
import platform

import boto3
import discord
from discord.ext import commands

import dimsecret
from botglob import BotGlob
from bruckserver import vireg
from missile import Missile
from raceline import Raceline
from tribe import Tribe

bot = commands.Bot(command_prefix='d.')
bot.missile = Missile(bot)

nickname = "DimBot"
version = 'v0.4.1'
activity = discord.Activity(
    name='Lokeon',
    type=discord.ActivityType.listening
)

if dimsecret.debug:
    nickname += f' [{version}]'
    news_ch = 372386868236386307
else:
    nickname += f' {{{version}}}'
    news_ch = 581699408870113310

botglobal = BotGlob()
with open('urls.json', 'r') as file:
    rss_urls = json.load(file)
logger = bot.missile.get_logger('DimBot')


@bot.command()
async def info(ctx):
    await ctx.send(
        f'Guild count: **{len(bot.guilds)}**. Debug mode: **{dimsecret.debug}**\n'
        f'This bot is coded with the programming language Python `{platform.python_version()}`\n'
        f'It interacts with Discord via discord.py `{discord.__version__}`,'
        f'Amazon Web Services via boto3 `{boto3.__version__}`.\n'
        'Bot source code: https://github.com/TCLRainbow/DimBot'
    )


@bot.event
async def on_ready():
    bot.missile.guild = bot.get_guild(285366651312930817)
    bot.missile.bottyland = bot.get_channel(372386868236386307)
    bot.missile.bruck_ch = bot.get_channel(688948118712090644)
    bot.missile.newsfeed = bot.get_channel(news_ch)
    logger.info(f'Guild count: {len(bot.guilds)}')
    for guild in bot.guilds:
        if guild.me.nick != nickname:
            await guild.me.edit(nick=nickname)
    await bot.change_presence(activity=activity)


bot.add_cog(Raceline(bot))
bot.add_cog(Tribe(bot))
bot.add_cog(vireg.Vireg(bot))
bot.run(dimsecret.discord)
