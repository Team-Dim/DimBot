import asyncio
import glob
import platform
from os import listdir
from random import choice

import boto3
import discord
from discord.ext import commands

import beural
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
version = 'v0.6.3.4'
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
        f'**Project Echo** `{echo.__version__}`: Add or search quotes through a SQL database.\n'
        f'**Project Tribe** `{tribe.__version__}`: Adds additional feature per role\n'
        '**Project Brighten**: *Confidential*\n'
        '**Project Blin**: *Confidential*\n'
        f'**Project Vireg** `{vireg.__version__}`: Connects to AWS and manage a minecraft server instance.\n'
        f'**Project Pythania** `{pythania.__version__}`: HTTP server sub-project used by `Vireg`.\n'
        f'**Project Beural** `{beural.__version__}` : Chat bot for answering BBM questions\n'
        '**Project Skybow**: *Confidential*'
    )


@bot.group()
async def link(ctx):
    pass


@link.command()
async def forge(ctx):
    msg = await bot.missile.ask_msg(ctx, 'Reply `Minecraft version-Forge version`')
    await ctx.send(f'https://files.minecraftforge.net/maven/net/minecraftforge/forge/{msg}/forge-{msg}-installer.jar')


@link.command()
async def galacticraft(ctx):
    mc = await bot.missile.ask_msg(ctx, 'Minecraft version?')
    ga = await bot.missile.ask_msg(ctx, 'Galacticraft version?')
    mc_ver = mc.rsplit(',', 1)[0]
    ga_build = ga.rsplit('.', 1)[1]
    await ctx.send(f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/GalacticraftCore-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/Galacticraft-Planet-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/MicdoodleCore-{mc}-{ga}.jar')


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


@bot.command()
@commands.check(is_debug)
async def play(ctx, name: str):
    if name == 'list':
        content = ''
        for fname in listdir('D:\\Music'):
            content += f'{fname}\n'
        await ctx.send(content)
    else:
        try:
            file = next(glob.iglob(f'D:\\Music\\*{glob.escape(name)}*'))
            client = await ctx.author.voice.channel.connect()
            name = file.split('\\')[2]
            await ctx.send(f'Now playing `{name}`')
            client.play(discord.FFmpegPCMAudio(source=file,
                                               executable='D:\\GitHub.Tyrrrz\\ffmpeg.exe'))
            await asyncio.sleep(skybow.get_audio_length(file))
            while bot.missile.loop:
                client.play(discord.FFmpegPCMAudio(source=file,
                                                   executable='D:\\GitHub.Tyrrrz\\ffmpeg.exe'))
                await asyncio.sleep(skybow.get_audio_length(file))
            await client.disconnect()
        except StopIteration:
            await ctx.send('No song found!')


@bot.command()
async def loop(ctx):
    bot.missile.loop = not bot.missile.loop
    await ctx.send(f'Bot loop: **{bot.missile.loop}**')


# Eggy requested this command
@bot.command()
async def hug(ctx):
    gif = choice(['https://tenor.com/view/milk-and-mocha-bear-couple-line-hug-cant-breathe-gif-12687187',
                  'https://tenor.com/view/hugs-hug-ghost-hug-gif-4451998',
                  'https://tenor.com/view/true-love-hug-miss-you-everyday-always-love-you-running-hug-gif-5534958'])
    await ctx.send(f'{gif}\nHug {ctx.author.mention}')


bot.add_cog(raceline.Raceline(bot))
bot.add_cog(tribe.Tribe(bot))
bot.add_cog(vireg.Vireg(bot))
bot.add_cog(echo.Echo(bot))
bot.add_cog(beural.Beural(bot))
bot.run(dimsecret.discord)
