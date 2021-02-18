import asyncio
import re
from random import choice, randint

import discord
from discord.ext import commands

import bitbay
import bottas
import dimsecret
import hamilton
import ricciardo
from bruckserver import verstapen, albon
from missile import Missile

intent = discord.Intents.none()
intent.guilds = intent.members = intent.messages = True
bot = commands.Bot(command_prefix='t.' if dimsecret.debug else 'd.', intents=intent)
bot.help_command = commands.DefaultHelpCommand(verify_checks=False)
bot.missile = Missile(bot)
bot.echo = bottas.Bottas(bot)
nickname = f"DimBot {'S ' if dimsecret.debug else ''}| 0.6.20.1"
activities = [
    discord.Activity(name='Echo', type=discord.ActivityType.listening),
    discord.Activity(name='YOASOBI ❤', type=discord.ActivityType.listening),
    discord.Activity(name='Sam yawning', type=discord.ActivityType.listening),
    discord.Activity(name='Lokeon', type=discord.ActivityType.listening),
    discord.Activity(name='Ricizus screaming', type=discord.ActivityType.listening),
    discord.Activity(name='Rainbow codes', type=discord.ActivityType.watching),
    discord.Activity(name='Matt plays R6', type=discord.ActivityType.watching),
    discord.Activity(name='Rainbow laughs', type=discord.ActivityType.watching),
    discord.Activity(name='comics', type=discord.ActivityType.watching),
    discord.Activity(name='Terry coughing', type=discord.ActivityType.listening),
    discord.Activity(name='Bruck sleeps', type=discord.ActivityType.watching),
    discord.Activity(name='Try not to crash', type=discord.ActivityType.competing),
    discord.Activity(name='Muzen train', type=discord.ActivityType.watching)
]
logger = bot.missile.get_logger('DimBot')
with open('.git/HEAD', 'r') as f:
    branch = f.readline().split('/')[-1]

sponsor_txt = 'You guys see my brother Tanjiro? I need to save him! Donate me! ' \
              '<https://streamlabs.com/pythonic_rainbow/tip> '


@bot.command(aliases=['ver', 'verinfo'])
async def info(ctx):
    from platform import python_version
    from boto3 import __version__ as boto3ver
    await ctx.send(
        f'Guild count: **{len(bot.guilds)}** | Branch: **{branch}**\n'
        f'This bot is running on Python `{python_version()}`\n'
        f'It interacts with Discord via discord.py `{discord.__version__}`, '
        f'Amazon Web Services via boto3 `{boto3ver}`.\n'
        'Bot source code: https://github.com/TCLRainbow/DimBot\n\n'
        'This bot has the following modules:\n'
        f'**Project Ricciardo** `{ricciardo.__version__}`: Relaying RSS, BBM and YouTube feeds to discord channels.\n'
        f'**Project Bottas** `{bottas.__version__}`: Add or search quotes through a SQLite database.\n'
        f'**Project Hamilton** `{hamilton.__version__}`: Adds additional feature per role\n'
        f'**Project Verstapen** `{verstapen.__version__}`: Connects to AWS and manage a minecraft server instance.\n'
        f'**Project Albon** `{albon.__version__}`: HTTP server sub-project used by `Verstapen`.\n'
        '**Project Norris** `0`: Chat bot for answering BBM questions.\n'
        f'**Project BitBay** `{bitbay.__version__}`: Utilities for 128BB\n\n'
        f'Devblog: Instagram @techdim\nDiscord server: `6PjhjCD`\n{sponsor_txt}'
    )


@bot.command()
async def sponsor(ctx):
    await ctx.send(sponsor_txt)


def is_debug(ctx):
    return dimsecret.debug


@bot.event
async def on_ready():
    bot.missile.guild = bot.get_guild(285366651312930817)
    bot.missile.bottyland = bot.get_channel(372386868236386307)
    bot.missile.bruck_ch = bot.get_channel(688948118712090644)
    if dimsecret.debug:
        bot.missile.announcement = bot.missile.bottyland  # In debug mode, rss.yt should send in bottyland
    else:
        bot.missile.announcement = bot.get_channel(425703064733876225)
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
async def on_message_delete(msg: discord.Message):
    if msg.author == msg.guild.me and re.search('has (delet|edit)ed a ping', msg.content):
        base = msg.clean_content.split('\n')[0]
        if msg.guild.me.permissions_in(msg.channel).view_audit_log:
            async for audit in msg.guild.audit_logs(limit=1, action=discord.AuditLogAction.message_delete):
                base += f"\n*{audit.user.mention} You tried to mute me but you can't hide*"
        await msg.channel.send(base)
        return
    if msg.guild and msg.id in bot.missile.ghost_pings.keys():
        for m in bot.missile.ghost_pings[msg.id]:
            await m.send(f'{msg.author.mention} pinged you in **{msg.guild.name}** and deleted it.')
        await msg.channel.send(msg.author.mention + ' has deleted a ping')
        bot.missile.ghost_pings.pop(msg.id)
    elif msg.guild and msg.mentions and not msg.edited_at:
        for m in msg.mentions:
            if not m.bot:
                await m.send(f'{msg.author.mention} pinged you in **{msg.guild.name}** and deleted it.')
        await msg.channel.send(msg.author.mention + ' has deleted a ping')
    content = msg.content if msg.content else msg.embeds[0].title
    bot.missile.snipe = discord.Embed(title=msg.author.display_name, description=content)
    bot.missile.snipe.set_author(name=msg.guild.name, icon_url=msg.author.avatar_url)
    bot.missile.snipe.set_thumbnail(url=msg.guild.icon_url)
    colour = msg.embeds[0].colour if msg.embeds else discord.Colour.from_rgb(
        randint(0, 255), randint(0, 255), randint(0, 255))
    bot.missile.snipe.colour = colour


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    if before.guild and not before.edited_at and before.mentions:
        bot.missile.ghost_pings[before.id] = [m for m in before.mentions if not m.bot]
    if before.guild and before.id in bot.missile.ghost_pings.keys():
        has_removed = False
        for m in bot.missile.ghost_pings[before.id]:
            if m not in after.mentions:
                has_removed = True
                await m.send(f'{before.author.mention} pinged you in **{before.guild.name}** and deleted it.')
                bot.missile.ghost_pings[before.id].remove(m)
        if has_removed:
            await before.channel.send(before.author.mention + ' has removed a ping from a message')
        if not bot.missile.ghost_pings[before.id]:
            bot.missile.ghost_pings.pop(before.id)


@bot.command()
async def snipe(ctx):
    if bot.missile.snipe:
        await ctx.send(embed=bot.missile.snipe)


@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.errors.CommandNotFound):
        await ctx.send('Stoopid. That is not a command.')
        return
    if isinstance(error, commands.errors.MissingRequiredArgument) or isinstance(error, commands.errors.MissingAnyRole):
        await ctx.send(str(error))
        return
    if isinstance(error, commands.errors.ChannelNotFound):
        await ctx.send("Invalid channel. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.RoleNotFound):
        await ctx.send("Invalid role. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.BadArgument):
        await ctx.send('Bad arguments.')
    elif isinstance(error, commands.errors.CheckFailure) or isinstance(error, asyncio.TimeoutError):
        return
    raise error


@bot.command()
@Missile.is_rainbow()
async def exit(ctx):
    bot.echo.db.commit()
    await ctx.send(':dizzy_face:')
    await bot.logout()


bot.add_cog(ricciardo.Ricciardo(bot))
# bot.add_cog(hamilton.Hamilton(bot))
bot.add_cog(verstapen.Verstapen(bot))
bot.add_cog(bot.echo)
bot.add_cog(bitbay.BitBay(bot))
bot.run(dimsecret.discord)
