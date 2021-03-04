import asyncio
from random import choice

import discord
from discord.ext import commands

import bitbay
import bottas
import dimsecret
import ricciardo
from bruckserver import verstapen, albon
from missile import Missile
# Variables needed for preparing the bot
intent = discord.Intents.none()
intent.guilds = intent.members = intent.messages = intent.reactions = True
bot = commands.Bot(command_prefix='t.' if dimsecret.debug else 'd.', intents=intent)
bot.help_command = commands.DefaultHelpCommand(verify_checks=False)
bot.missile = Missile(bot)
bot.echo = bottas.Bottas(bot)
nickname = f"DimBot NEA {'S ' if dimsecret.debug else ''}| 0.7.7.99"
# List of activities that will be randomly displayed every 5 minutes
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
    branch = f.readline().split('/')[-1]  # Read Git branch

sponsor_txt = 'You guys see my brother Tanjiro? I need to save him! Donate me! ' \
              '<https://streamlabs.com/pythonic_rainbow/tip> '


@bot.command(aliases=['ver', 'verinfo'])
async def info(ctx):
    """A command that displays the bot information"""
    from platform import python_version
    from boto3 import __version__ as boto3ver
    await ctx.send(
        # Number of servers the bot is serving and the Git branch
        f'Guild count: **{len(bot.guilds)}** | Branch: **{branch}**\n'
        f'This bot is running on Python `{python_version()}`\n'
        f'It interacts with Discord via discord.py `{discord.__version__}`, '
        f'Amazon Web Services via boto3 `{boto3ver}`.\n'
        'Bot source code: https://github.com/TCLRainbow/DimBot\n\n'
        'This bot has the following modules:\n'  # Module description and version
        f'**Project Ricciardo** `{ricciardo.__version__}`: Relaying RSS, BBM and YouTube feeds to discord channels.\n'
        f'**Project Bottas** `{bottas.__version__}`: Add or search quotes through a SQLite database.\n'
        f'**Project Verstapen** `{verstapen.__version__}`: Connects to AWS and manage a minecraft server instance.\n'
        f'**Project Albon** `{albon.__version__}`: HTTP server sub-project used by `Verstapen`.\n'
        f'**Project BitBay** `{bitbay.__version__}`: Utilities for 128BB\n\n'
        f'Devblog: Instagram @techdim\nDiscord server: `6PjhjCD`\n{sponsor_txt}'  # Contact
    )


@bot.command()
async def sponsor(ctx):
    """Shows the sponsor message"""
    await ctx.send(sponsor_txt)


@bot.event
async def on_ready():
    """Event handler when the bot has connected to the Discord endpoint"""
    # First, fetch all the special objects
    bot.missile.guild = bot.get_guild(285366651312930817)
    bot.missile.bottyland = bot.get_channel(372386868236386307)
    bot.missile.bruck_ch = bot.get_channel(688948118712090644)
    if dimsecret.debug:
        bot.missile.announcement = bot.missile.bottyland  # In debug mode, rss.yt should send in bottyland
    else:
        bot.missile.announcement = bot.get_channel(425703064733876225)
    bot.missile.logs = bot.get_channel(384636771805298689)
    logger.info(f'Guild count: {len(bot.guilds)}')
    # Then updates the nickname for each server that DimBot is listening to
    for guild in bot.guilds:
        if guild.me.nick != nickname:
            await guild.me.edit(nick=nickname)
    if bot.missile.new:
        # Due to endpoint reasons, connection to the endpoint may reset.
        # The bot will reconnect by itself, but on_ready() will be called again, which can trigger
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
    """Event handler when a message has been deleted
    First block of code is Ghost ping detector"""
    # Check whether the message is related to the bot
    if msg.author == msg.guild.me or msg.content.startswith(bot.command_prefix):
        return
    if msg.guild and msg.id in bot.missile.ghost_pings.keys():  # The message has/used to have pings
        for m in bot.missile.ghost_pings[msg.id]:
            # Tells the victim that he has been ghost pinged
            await m.send(f'{msg.author.mention} ({msg.author}) pinged you in **{msg.guild.name}** and deleted it.')
        # Reports in the incident channel that the culprit deleted a ping
        await msg.channel.send(msg.author.mention + ' has deleted a ping')
        # Removes the message from the cache as it has been deleted on Discord
        bot.missile.ghost_pings.pop(msg.id)
    elif msg.guild and msg.mentions and not msg.edited_at:  # The message has pings and has not been edited
        for m in msg.mentions:
            if not m.bot:
                # Tells the victim that he has been ghost pinged
                await m.send(f'{msg.author.mention} ({msg.author}) pinged you in **{msg.guild.name}** and deleted it.')
        # Reports in the incident channel that the culprit deleted a ping
        await msg.channel.send(msg.author.mention + ' has deleted a ping')

    # Stores the deleted message for snipe command
    content = msg.content if msg.content else msg.embeds[0].title
    bot.missile.snipe = discord.Embed(title=msg.author.display_name, description=content)
    bot.missile.snipe.set_author(name=msg.guild.name, icon_url=msg.author.avatar_url)
    bot.missile.snipe.set_thumbnail(url=msg.guild.icon_url)
    bot.missile.snipe.colour = msg.embeds[0].colour if msg.embeds else Missile.random_rgb()


@bot.event
async def on_message_edit(before: discord.Message, after: discord.Message):
    """Event handler when a message has been edited. Detect ghost pings due to edited message"""
    if before.guild and not before.edited_at and before.mentions:  # A message that contains pings has been edited
        #  Add the message to ghost pings cache
        bot.missile.ghost_pings[before.id] = [m for m in before.mentions if not m.bot]
    if before.guild and before.id in bot.missile.ghost_pings.keys():  # Message requires ghost ping checking
        has_removed = False
        for m in bot.missile.ghost_pings[before.id]:
            if m not in after.mentions:  # A ping has been removed
                has_removed = True
                # Tells the victim that he has been ghost pinged
                await m.send(f'{before.author.mention} pinged you in **{before.guild.name}** and deleted it.')
                bot.missile.ghost_pings[before.id].remove(m)
        if has_removed:
            # Reports in the incident channel that the culprit deleted a ping
            await before.channel.send(before.author.mention + ' has removed a ping from a message')
        if not bot.missile.ghost_pings[before.id]:  # All original pings have bene removed.
            bot.missile.ghost_pings.pop(before.id)  # No longer have to track as there are no pings anymore.


@bot.command()
async def snipe(ctx):
    """Displays the last deleted message"""
    await ctx.send(embed=bot.missile.snipe)


@bot.event
async def on_command_error(ctx, error):
    """Event handler when a command raises an error"""
    if isinstance(error, commands.errors.CommandNotFound):  # Human error
        await ctx.send('Stoopid. That is not a command.')
        return
    # Human error
    if isinstance(error, commands.errors.MissingRequiredArgument) or isinstance(error, commands.errors.MissingAnyRole):
        await ctx.send(str(error))
        return
    if isinstance(error, commands.errors.ChannelNotFound):  # Human error
        await ctx.send("Invalid channel. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.RoleNotFound):  # Human error
        await ctx.send("Invalid role. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.BadArgument):  # Could be a human/program error
        await ctx.send('Bad arguments.')
    elif isinstance(error, commands.errors.CheckFailure) or isinstance(error, asyncio.TimeoutError):  # Human error
        return
    raise error  # This is basically "unknown error", raise it for debug purposes


@bot.command()
@Missile.is_rainbow_cmd_check()
async def exit(ctx):
    """Forcefully exits the program"""
    bot.echo.db.commit()
    await ctx.send(':dizzy_face:')
    await bot.logout()

# Enable modules
bot.add_cog(ricciardo.Ricciardo(bot))
bot.add_cog(verstapen.Verstapen(bot))
bot.add_cog(bot.echo)
bot.add_cog(bitbay.BitBay(bot))
bot.run(dimsecret.discord)
