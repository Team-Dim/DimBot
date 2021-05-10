import asyncio
from datetime import datetime, timedelta
from random import choice, randint
from typing import Union

import aiosql
import discord
from discord.ext import commands
from discord.ext.commands import errors

import bitbay
import dimond
import dimsecret
import missile
import tribe
from bruckserver.vireg import Verstapen
from echo import Bottas
from mod.aegis import Aegis
from mod.ikaros import Ikaros
from raceline import Ricciardo
from xp import XP

# Variables needed for initialising the bot
intent = discord.Intents.none()
intent.guilds = intent.members = intent.messages = intent.reactions = intent.voice_states = intent.typing = True
intent.presences = True
bot = missile.Bot(intents=intent)
bot.help_command = commands.DefaultHelpCommand(verify_checks=False)
nickname = f"DimBot {'S ' if dimsecret.debug else ''}| 0.9.14"
logger = missile.get_logger('DimBot')
sponsor_txt = '世界の未来はあなたの手の中にあります <https://streamlabs.com/pythonic_rainbow/tip> <https://www.patreon.com/ChingDim>'
reborn_channel = None


async def binvk(ctx: commands.Context):
    if randint(1, 100) <= 5:
        await ctx.send(sponsor_txt)
    bot.invoke_time = datetime.now()


bot.before_invoke(binvk)


async def ainvk(ctx: commands.Context):
    timedelta = (datetime.now() - bot.invoke_time).total_seconds() * 1000
    await bot.wait_until_ready()
    await bot.get_cog('Hamilton').bot_test.send(f'**{ctx.command}**: {timedelta}ms')


bot.after_invoke(ainvk)

try:
    # If the bot is restarting, read the channel ID that invoked the restart command
    with open('final', 'r') as fi:
        logger.info('Found final file')
        reborn_channel = int(fi.readline())
    import os

    os.remove('final')
except FileNotFoundError:
    logger.info('No previous final file found')


@bot.event
async def on_message(msg: discord.Message):
    if msg.author.id != bot.user.id:
        logger.info(f"{msg.author} @{msg.guild} #{msg.channel}")
        logger.info(msg.content + '\n')
    if msg.guild and msg.content == msg.guild.me.mention:
        await msg.channel.send(f'My prefix is **{bot.default_prefix}**')
        return
    await bot.process_commands(msg)


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Updates DimBot's nickname in new servers"""
    await guild.me.edit(nick=nickname)


@bot.event
async def on_message_delete(msg: discord.Message):
    """Event handler when a message has been deleted"""
    if msg.author == msg.guild.me or msg.content.startswith(await missile.prefix_process(bot, msg)):
        return
    # Stores the deleted message for snipe command
    content = msg.content if msg.content else msg.embeds[0].title
    bot.snipe = missile.Embed(msg.author.display_name, content,
                              msg.embeds[0].colour if msg.embeds else discord.Colour.random(),
                              msg.guild.icon_url)
    bot.snipe.set_author(name=msg.guild.name, icon_url=msg.author.avatar_url)


@bot.event
async def on_command_error(ctx: commands.Context, error: commands.errors.CommandInvokeError):
    """Event handler when a command raises an error"""
    if isinstance(error, errors.CommandNotFound):  # Human error
        await ctx.reply('Stoopid. That is not a command.')
    # Human error
    elif isinstance(error, (errors.MissingRequiredArgument, errors.MissingAnyRole, errors.CommandOnCooldown,
                            errors.UserNotFound, errors.MemberNotFound, errors.MissingPermissions,
                            errors.BadInviteArgument, errors.BadColourArgument)) \
            or isinstance(error, errors.BadUnionArgument) and not ctx.command.has_error_handler():
        await ctx.reply(str(error))
    elif isinstance(error, bitbay.BasePPException):  # Human error
        await ctx.reply(str(error).format(ctx.bot.default_prefix))
    elif isinstance(error, errors.ChannelNotFound):  # Human error
        await ctx.reply("Invalid channel. Maybe you've tagged the wrong one?")
    elif isinstance(error, errors.RoleNotFound):  # Human error
        await ctx.reply("Invalid role. Maybe you've tagged the wrong one?")
    elif isinstance(error, errors.GuildNotFound):
        await ctx.reply('I am not in that server.')
    elif isinstance(error, errors.BadArgument):
        # Could be a human/program error
        await ctx.reply('Bad arguments.')
    elif isinstance(error, errors.CheckFailure):
        return
    else:
        # This is basically "unknown error"
        import traceback
        content = f'```python\n{ctx.message.content}\n'
        for tb in traceback.format_tb(error.original.__traceback__):
            content += tb
        content += str(error.original) + '```'
        msg = await bot.get_cog('Hamilton').bot_test.send(content)
        await ctx.reply(f'Hmm... Report ID: **{msg.id}**')


@bot.command(aliases=('bot',))
async def botinfo(ctx):
    """Displays bot information"""
    from platform import python_version
    embed = missile.Embed(sponsor_txt)
    embed.add_field('Guild count', len(bot.guilds))
    embed.add_field('Uptime', datetime.now() - bot.boot_time)
    embed.add_field('Python', python_version())
    embed.add_field('Discord.py', discord.__version__)
    embed.add_field('Codename', '뾆')
    embed.add_field('Devblog', '[Instagram](https://www.instagram.com/techdim)')
    embed.add_field('Source code', '[GitHub](https://github.com/TCLRainbow/DimBot)')
    embed.add_field('Discord server', '[6PjhjCD](https://discord.gg/6PjhjCD)')
    await ctx.send(embed=embed)


@bot.command()
async def sponsor(ctx):
    """$.$"""
    await ctx.send(sponsor_txt)


@bot.command()
async def noel(ctx):
    """Listens to my heartbeat"""
    msg = await ctx.reply(f':heartbeat: {bot.latency * 1000:.3f}ms')
    tic = datetime.now()
    await msg.add_reaction('📡')
    toc = datetime.now()
    await msg.edit(content=msg.content + f' :satellite_orbital: {(toc - tic).total_seconds() * 1000:.3f}ms')


@bot.group(invoke_without_command=True)
async def link(ctx):
    """Commands for generating links"""
    raise commands.errors.CommandNotFound


@link.command()
async def forge(ctx):
    """Generating MinecraftForge installer links"""
    msg = await bot.ask_msg(ctx, 'Reply `Minecraft version`-`Forge version`')
    await ctx.send(f'https://files.minecraftforge.net/maven/net/minecraftforge/forge/{msg}/forge-{msg}-installer.jar')


@link.command()
async def galacticraft(ctx):
    """Generating Galaticraft mod download links"""
    mc = await bot.ask_msg(ctx, 'Minecraft version?')
    ga = await bot.ask_msg(ctx, 'Galacticraft version?')
    mc_ver = mc.rsplit(',', 1)[0]
    ga_build = ga.rsplit('.', 1)[1]
    await ctx.send(f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/GalacticraftCore-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/Galacticraft-Planet-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/MicdoodleCore-{mc}-{ga}.jar')


@link.command(aliases=('m',))
async def message(ctx, msg: discord.Message):
    await ctx.reply(msg.jump_url)


@bot.command()
async def snipe(ctx):
    """Displays the last deleted message"""
    await ctx.send(embed=bot.snipe)


@bot.group()
@missile.is_rainbow()
async def arccore(ctx: commands.Context):
    """Confidential"""
    if not ctx.invoked_subcommand:
        raise commands.errors.CommandNotFound


@arccore.command()
async def stealth(ctx):
    await bot.db.commit()
    await bot.db.close()
    await ctx.send('Arc-Cor𐑞: **Stealth**')
    await bot.close()


@arccore.command()
async def pandora(ctx):
    await bot.db.commit()
    await bot.db.close()
    await ctx.send('Arc-Cor𐑞: **PANDORA**, self-evolving!')
    with open('final', 'w') as death_note:
        death_note.write(str(ctx.channel.id))
    logger.critical('RESTARTING')
    import subprocess
    subprocess.Popen(['sudo systemctl restart dimbot'], shell=True)


@arccore.command()
async def sch(ctx, ch: Union[discord.TextChannel, discord.User]):
    bot.sch = ch


@arccore.command()
async def say(ctx, *, msg: str):
    await bot.sch.send(msg)


@arccore.command()
async def shadow(c, *, cmd: str):
    msg = await bot.sch.send('⠀')
    msg.content = bot.default_prefix + cmd
    msg.author = msg.guild.get_member(bot.owner_id)
    await bot.invoke(await bot.get_context(msg))


@arccore.command()
async def leave(ctx: commands.Context, s: discord.Guild):
    await s.leave()
    await ctx.reply('Done.')


@arccore.command()
async def exe(ctx, *, msg: str):
    # Directly executes SQL statements
    import sqlite3
    try:
        tic = datetime.now()  # Measure execution time
        msg = f"--name: sqlexe\n{msg}"""
        query = aiosql.from_str(msg, 'aiosqlite')
        async with query.sqlexe_cursor(bot.db) as cursor:
            result = await cursor.fetchall()
            toc = datetime.now()
            await ctx.reply(f"{result}\n{cursor.rowcount} row affected in {(toc - tic).total_seconds() * 1000}ms")
    except sqlite3.Error as e:
        await ctx.send(f"**{e.__class__.__name__}**: {e}")


@arccore.command()
async def save(ctx):
    # Forcefully saves the db
    await bot.db.commit()
    await ctx.send('Saved')


@arccore.command()
async def typing(ctx):
    if bot.arccore_typing:
        await bot.arccore_typing.__aexit__(None, None, None)
        bot.arccore_typing = None
    else:
        bot.arccore_typing = await bot.sch.typing().__aenter__()


async def __maintenance__(context):
    owner = context.author.id == bot.owner_id
    if not owner:
        await context.reply("My pog champ is taking care of me <:ikaros:823581166715928588>")
    return owner


@arccore.command()
async def mt(ctx: commands.Context, minutes: int = 5):

    if bot.maintenance:
        bot.remove_check(__maintenance__)
        bot.status = discord.Status.online
        await bot.change_presence()
        await ctx.reply('Removed maintenance')
    elif await bot.ask_reaction(ctx, f'Enable maintenance mode after {minutes}min?'):
        now = datetime.now() + timedelta(minutes=minutes)

        async def prep(context: commands.Context):
            stamp = (now - datetime.now()).total_seconds()
            if stamp >= 60:
                stamp = f"{(stamp // 60):.0f}m {(stamp % 60):.0f}s"
            else:
                stamp = f"{stamp:.0f}s"
            await context.send(f"⚠Maintenance mode in **{stamp}**!")
            return True

        bot.add_check(prep)
        bot.status = discord.Status.idle
        await bot.change_presence(status=bot.status)
        m = await ctx.send('Preparing maintenance')
        await asyncio.sleep(minutes * 60)
        bot.remove_check(prep)
        bot.add_check(__maintenance__)
        bot.maintenance = True
        bot.status = discord.Status.dnd
        await bot.change_presence(status=bot.status)
        await missile.append_msg(m, 'Started')


# Eggy requested this command
@bot.command()
async def hug(ctx):
    """Need some love?"""
    gif = choice(('https://tenor.com/view/milk-and-mocha-bear-couple-line-hug-cant-breathe-gif-12687187',
                  'https://tenor.com/view/hugs-hug-ghost-hug-gif-4451998',
                  'https://tenor.com/view/true-love-hug-miss-you-everyday-always-love-you-running-hug-gif-5534958'))
    await ctx.send(f'{gif}\nWe are friends again, {bot.eggy}\nHug {ctx.author.mention}')


@bot.group(aliases=('color',), invoke_without_command=True)
async def colour(ctx: commands.Context, c: discord.Colour = None):
    if not c:
        c = discord.Colour.random()
    value = f'{c.value:X}'
    emb = missile.Embed(f'#{value.zfill(6)}', color=c)
    emb.add_field('R', c.r)
    emb.add_field('G', c.g)
    emb.add_field('B', c.b)
    await ctx.reply(embed=emb)


@colour.command()
async def hsv(ctx: commands.Context, h: int = 0, s: int = 0, v: int = 0):
    color = discord.Colour.from_hsv(h, s, v)
    if 0 <= color.value <= 0xFFFFFF:
        await bot.get_command('color')(ctx, discord.Colour.from_hsv(h, s, v))
    else:
        raise errors.BadColorArgument(color)


async def ready_tasks():
    bot.add_cog(Ricciardo(bot))
    bot.add_cog(Verstapen(bot))
    bot.add_cog(Bottas(bot))
    bot.add_cog(bitbay.BitBay(bot))
    bot.add_cog(dimond.Dimond(bot))
    bot.add_cog(Ikaros(bot))
    bot.add_cog(Aegis(bot))
    bot.add_cog(XP(bot))
    await bot.wait_until_ready()
    bot.add_cog(tribe.Hamilton(bot))
    bot.eggy = await bot.fetch_user(226664644041768960)  # Special Discord user
    await bot.is_owner(bot.eggy)  # Trick to set bot.owner_id
    logger.info('Ready')
    # Then updates the nickname for each server that DimBot is listening to
    for guild in bot.guilds:
        if guild.me.nick != nickname:
            bot.loop.create_task(guild.me.edit(nick=nickname))
    if reborn_channel:  # Post-process Pandora if needed
        await bot.get_channel(reborn_channel).send("Arc-Cor𐑞: Pandora complete.")
    while True:
        activity = await bot.sql.get_activity(bot.db)
        await bot.change_presence(activity=discord.Activity(name=activity[0], type=discord.ActivityType(activity[1])),
                                  status=bot.status)
        await asyncio.sleep(300)
        await bot.db.commit()
        logger.debug('DB auto saved')

bot.loop.create_task(bot.async_init())
bot.loop.create_task(ready_tasks())
bot.run(dimsecret.discord)
