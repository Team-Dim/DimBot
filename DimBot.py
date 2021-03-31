import asyncio
from datetime import datetime
from random import choice, randint
from typing import Union

import discord
from discord.ext import commands

import dimond
import dimsecret
import echo
import raceline
import tribe
from bitbay import BitBay
from bruckserver.vireg import Verstapen
from missile import Missile, dim_id
from mod.aegis import Aegis
from mod.ikaros import Ikaros

# Variables needed for initialising the bot
intent = discord.Intents.none()
intent.guilds = intent.members = intent.messages = intent.reactions = intent.voice_states = intent.typing = True
intent.presences = True
bot = commands.Bot(command_prefix=Missile.prefix_process, intents=intent)
bot.default_prefix = 't.' if dimsecret.debug else 'd.'
bot.help_command = commands.DefaultHelpCommand(verify_checks=False)
bot.missile = Missile(bot)
bot.echo = echo.Bottas(bot)
nickname = f"DimBot {'S ' if dimsecret.debug else ''}| 0.8.14"
nickname = 'Cough'
# List of activities that will be randomly displayed every 5 minutes
activities = [
    discord.Activity(name='Echo', type=discord.ActivityType.listening),
    discord.Activity(name='YOASOBI ❤', type=discord.ActivityType.listening),
    discord.Activity(name='Sam yawning', type=discord.ActivityType.listening),
    discord.Activity(name='Lokeon', type=discord.ActivityType.listening),
    discord.Activity(name='Ricizus screaming', type=discord.ActivityType.listening),
    discord.Activity(name='Dim codes', type=discord.ActivityType.watching),
    discord.Activity(name='Matt plays R6', type=discord.ActivityType.watching),
    discord.Activity(name='Dim laughs', type=discord.ActivityType.watching),
    discord.Activity(name='comics', type=discord.ActivityType.watching),
    discord.Activity(name='Terry coughing', type=discord.ActivityType.listening),
    discord.Activity(name='Bruck sleeps', type=discord.ActivityType.watching),
    discord.Activity(name='Try not to crash', type=discord.ActivityType.competing),
    discord.Activity(name='Muzen train', type=discord.ActivityType.watching),
    discord.Activity(name="Heaven's Lost Property", type=discord.ActivityType.watching)
]
activities = [discord.Activity(name='people spread covid', type=discord.ActivityType.watching)]
logger = bot.missile.get_logger('DimBot')
sponsor_txt = '世界の未来はあなたの手の中にあります <https://streamlabs.com/pythonic_rainbow/tip>'
reborn_channel = None
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
    dim = msg.guild.get_member(dim_id)
    if dim and dim.status != discord.Status.online and dim in msg.mentions:
        await msg.reply('My master is away atm.')
    role = discord.utils.get(msg.guild.roles, name='Covid')
    new_hash = bin(hash(f"{msg.content}{msg.author}{msg.created_at}")).ljust(65, '0')
    x = sum(c1 != c2 for c1, c2 in zip(new_hash, bot.missile.hash))
    if role not in msg.author.roles:
        if bot.missile.last_hash_count == x and bot.missile.last_msg and msg.author != bot.missile.last_msg.author and \
                role in bot.missile.last_msg.author.roles:
            await msg.reply(f'OH FUCK! You are infected by {bot.missile.last_msg.author}!\nBuy masks via `d.sponsor`!')
            await msg.author.add_roles(role)
        elif x >= 52:
            await msg.reply(f"Your body just somehow mutated covid by itself. Smh my head.\nBuy masks via `d.sponsor`!")
            await msg.author.add_roles(role)
    elif x <= 13:
        await msg.reply("You have been cured.")
        await msg.author.remove_roles(role)

    bot.missile.hash = new_hash
    bot.missile.last_hash_count = x
    bot.missile.last_msg = msg
    await bot.process_commands(msg)


@bot.event
async def on_ready():
    """Event handler when the bot has connected to the Discord endpoint"""
    # First, fetch all the special objects
    bot.missile.bottyland = bot.get_channel(372386868236386307)
    if dimsecret.debug:
        bot.missile.announcement = bot.missile.bottyland  # In debug mode, rss,yt should send in bottyland
    else:
        bot.missile.announcement = bot.get_channel(425703064733876225)
    bot.missile.logs = bot.get_channel(384636771805298689)
    bot.missile.eggy = await bot.fetch_user(226664644041768960)

    # Then updates the nickname for each server that DimBot is listening to
    for guild in bot.guilds:
        if guild.me.nick != nickname:
            bot.loop.create_task(guild.me.edit(nick=nickname))
    if reborn_channel:
        await bot.get_channel(reborn_channel).send("Arc-Cor𐑞: Pandora complete.")
    while True:
        logger.debug('Changed activity')
        await bot.change_presence(activity=choice(activities))
        await asyncio.sleep(300)


@bot.event
async def on_guild_join(guild: discord.Guild):
    """Updates DimBot's nickname in new servers"""
    await guild.me.edit(nick=nickname)


@bot.event
async def on_message_delete(msg: discord.Message):
    """Event handler when a message has been deleted"""
    if msg.author == msg.guild.me or msg.content.startswith(await Missile.prefix_process(bot, msg)):
        return
    # Stores the deleted message for snipe command
    content = msg.content if msg.content else msg.embeds[0].title
    bot.missile.snipe = discord.Embed(title=msg.author.display_name, description=content)
    bot.missile.snipe.set_author(name=msg.guild.name, icon_url=msg.author.avatar_url)
    bot.missile.snipe.set_thumbnail(url=msg.guild.icon_url)
    bot.missile.snipe.colour = msg.embeds[0].colour if msg.embeds else Missile.random_rgb()


@bot.event
async def on_command_error(ctx, error):
    """Event handler when a command raises an error"""
    if isinstance(error, commands.errors.CommandNotFound):  # Human error
        await ctx.reply('Stoopid. That is not a command.')
        return
    # Human error
    if isinstance(error, commands.errors.MissingRequiredArgument) or isinstance(error, commands.errors.MissingAnyRole) \
            or isinstance(error, commands.errors.CommandOnCooldown) or isinstance(error, commands.errors.UserNotFound) \
            or isinstance(error, commands.errors.MemberNotFound) or isinstance(error, commands.errors.MissingPermissions):
        await ctx.reply(str(error))
        return
    if isinstance(error, commands.errors.ChannelNotFound):  # Human error
        await ctx.reply("Invalid channel. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.RoleNotFound):  # Human error
        await ctx.reply("Invalid role. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.BadArgument):  # Could be a human/program error
        await ctx.reply('Bad arguments.')
    elif isinstance(error, commands.errors.CheckFailure):
        return
    raise error  # This is basically "unknown error", raise it for debug purposes


@bot.command(aliases=['ver', 'verinfo'])
async def info(ctx):
    """Displays bot information"""
    from platform import python_version
    await ctx.send(
        f'Guild count: **{len(bot.guilds)}** | Python: `{python_version()}` | Discord.py: `{discord.__version__}` \n'
        'Bot source code: https://github.com/TCLRainbow/DimBot\n'
        f'Bot module descriptions have been moved to `{bot.default_prefix}help <module name>`\n'
        f'Devblog: Instagram @techdim\nDiscord server: `6PjhjCD`\n\n{sponsor_txt}'
    )


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


@bot.group()
async def link(ctx):
    """Commands for generating links"""
    pass


@link.command()
async def forge(ctx):
    """Generating MinecraftForge installer links"""
    msg = await bot.missile.ask_msg(ctx, 'Reply `Minecraft version`-`Forge version`')
    await ctx.send(f'https://files.minecraftforge.net/maven/net/minecraftforge/forge/{msg}/forge-{msg}-installer.jar')


@link.command()
async def galacticraft(ctx):
    """Generating Galaticraft mod download links"""
    mc = await bot.missile.ask_msg(ctx, 'Minecraft version?')
    ga = await bot.missile.ask_msg(ctx, 'Galacticraft version?')
    mc_ver = mc.rsplit(',', 1)[0]
    ga_build = ga.rsplit('.', 1)[1]
    await ctx.send(f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/GalacticraftCore-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/Galacticraft-Planet-{mc}-{ga}.jar\n'
                   f'https://micdoodle8.com/new-builds/GC-{mc_ver}/{ga_build}/MicdoodleCore-{mc}-{ga}.jar')


@bot.command()
async def snipe(ctx):
    """Displays the last deleted message"""
    await ctx.send(embed=bot.missile.snipe)


@bot.group(invoke_without_command=True)
@Missile.is_rainbow_cmd_check()
async def arccore(ctx):
    pass


@arccore.command()
@Missile.is_rainbow_cmd_check()
async def stealth(ctx):
    bot.echo.db.commit()
    await ctx.send('Arc-Cor𐑞: **Stealth**')
    await bot.logout()


@arccore.command()
@Missile.is_rainbow_cmd_check()
async def pandora(ctx):
    bot.echo.db.commit()
    await ctx.send('Arc-Cor𐑞: **PANDORA**, self-evolving!')
    with open('final', 'w') as death_note:
        death_note.write(str(ctx.channel.id))
    logger.critical('RESTARTING')
    import subprocess
    subprocess.Popen(['sudo systemctl restart dimbot'], shell=True)


@bot.command()
@Missile.is_rainbow_cmd_check()
async def sch(ctx, ch: Union[discord.TextChannel, discord.User]):
    bot.missile.sch = ch


@bot.command()
@Missile.is_rainbow_cmd_check()
async def say(ctx, *, msg: str):
    await bot.missile.sch.send(msg)


@bot.command()
@Missile.is_rainbow_cmd_check()
async def shadow(c, *, cmd: str):
    msg = await bot.missile.sch.send('⠀')
    msg.content = bot.default_prefix + cmd
    msg.author = msg.guild.get_member(dim_id)
    await bot.invoke(await bot.get_context(msg))


# Eggy requested this command
@bot.command()
async def hug(ctx):
    """Hugs you"""
    gif = choice(['https://tenor.com/view/milk-and-mocha-bear-couple-line-hug-cant-breathe-gif-12687187',
                  'https://tenor.com/view/hugs-hug-ghost-hug-gif-4451998',
                  'https://tenor.com/view/true-love-hug-miss-you-everyday-always-love-you-running-hug-gif-5534958'])
    await ctx.send(f'{gif}\nIn memory of our friendship, {bot.missile.eggy}\nHug {ctx.author.mention}')


@bot.command(aliases=['color'])
async def colour(ctx, a: str = None, *args):
    """Shows info about the color"""
    if not a:
        a = str(randint(1, 0xFFFFFF))
    try:
        is_hex = a[0] == '#'
        if is_hex:
            colour = discord.Colour(int(a[1:], 16))
        elif a.lower() == 'rgb':
            colour = discord.Colour.from_rgb(int(Missile.ensure_index_value(args, 0, 0)),
                                             int(Missile.ensure_index_value(args, 1, 0)),
                                             int(Missile.ensure_index_value(args, 2, 0)))
        elif a.lower() == 'hsv':
            colour = discord.Colour.from_hsv(int(Missile.ensure_index_value(args, 0, 0)),
                                             int(Missile.ensure_index_value(args, 1, 0)),
                                             int(Missile.ensure_index_value(args, 2, 0)))
        else:
            colour = discord.Colour(int(a))
        emb = discord.Embed(title=a if is_hex else f'#{colour.value:X}', color=colour)
        emb.add_field(name='R', value=colour.r)
        emb.add_field(name='G', value=colour.g)
        emb.add_field(name='B', value=colour.b)
        await ctx.reply(embed=emb)
    except ValueError:
        await ctx.reply('Invalid color. You can input an integer `2048` , a hex code `#ABCABC`, or a RGB/HSV '
                        'combination `rgb/hsv <> <> <>`')


async def ready_tasks():
    bot.add_cog(raceline.Ricciardo(bot))
    bot.add_cog(Verstapen(bot))
    bot.add_cog(bot.echo)
    bot.add_cog(BitBay(bot))
    bot.add_cog(dimond.Dimond(bot))
    bot.add_cog(Ikaros(bot))
    bot.add_cog(Aegis(bot))
    await bot.wait_until_ready()
    bot.add_cog(tribe.Hamilton(bot))
bot.loop.create_task(ready_tasks())
bot.run(dimsecret.discord)
