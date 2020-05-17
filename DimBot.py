import asyncio
import json
import platform
from glob import glob

import boto3
import discord
from discord.ext import commands

import dimsecret
import echo
import raceline
import skybow
import tribe
from bruckserver import vireg, pythania
from missile import Missile

bot = commands.Bot(command_prefix='d.')
bot.missile = Missile(bot)

nickname = "DimBot"
version = 'v0.4.2'
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

with open('urls.json', 'r') as file:
    rss_urls = json.load(file)
logger = bot.missile.get_logger('DimBot')


@bot.command(aliases=['ver', 'verinfo'])
async def info(ctx):
    await ctx.send(
        f'Guild count: **{len(bot.guilds)}**. Debug mode: **{dimsecret.debug}**\n'
        f'This bot is coded with the programming language Python `{platform.python_version()}`\n'
        f'It interacts with Discord via discord.py `{discord.__version__}`, '
        f'Amazon Web Services via boto3 `{boto3.__version__}`.\n'
        'Bot source code: https://github.com/TCLRainbow/DimBot\n\n'
        'This bot has the following modules:\n'
        f'**Project Raceline** `{raceline.__version__}`: Subscribe to multiple RSS feed and send them to discord channels.\n'
        '**Project Echo** `(Beta)`: Add or search quotes through a SQL database.\n'
        f'**Project Tribe** `{tribe.__version__}`: Adds additional feature per role\n'
        '**Project Brighten**: *Confidential*\n'
        '**Project Blin**: *Confidential*\n'
        f'**Project Vireg** `{vireg.__version__}`: Connects to AWS and manage a minecraft server instance.\n'
        f'**Project Pythania** `{pythania.__version__}`: HTTP server sub-project used by `Vireg`.\n'
        '**Project Beural**: *Confidential*'
        '**Project Skybow**: *Confidential*'
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


@bot.command()
@commands.check(vireg.is_rainbow)
async def music(ctx, name: str):
    results = glob(f'D:\\Music\\{name}?.mp3')
    print(results)
    client = await ctx.author.voice.channel.connect()
    song_name = 'Tantal - Xenoblade Chronicles 2 OST 053.mp3'
    path = f'D:\\Music\\{song_name}'
    await ctx.send(f'Now playing `{song_name}`')
    logger.debug('Play once')
    client.play(discord.FFmpegPCMAudio(source=path,
                                       executable='D:\\GitHub.Tyrrrz\\ffmpeg.exe'))
    await asyncio.sleep(skybow.get_audio_length(path))
    while bot.missile.loop:
        logger.debug('in loop')
        client.play(discord.FFmpegPCMAudio(source=path,
                                           executable='D:\\GitHub.Tyrrrz\\ffmpeg.exe'))
        await asyncio.sleep(skybow.get_audio_length(path))
    await client.disconnect()


@bot.command()
@commands.check(vireg.is_rainbow)
async def loop(ctx):
    bot.missile.loop = not bot.missile.loop
    await ctx.send(f'Bot loop: **{bot.missile.loop}**')


bot.add_cog(raceline.Raceline(bot))
bot.add_cog(tribe.Tribe(bot))
bot.add_cog(vireg.Vireg(bot))
bot.add_cog(echo.Echo(bot))
bot.run(dimsecret.discord)
