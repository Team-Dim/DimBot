import asyncio
from datetime import datetime
from random import choice
from typing import Optional

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
intent.guilds = intent.members = intent.messages = intent.reactions = intent.voice_states = intent.typing = True
intent.presences = True
bot = commands.Bot(command_prefix='t.' if dimsecret.debug else 'd.', intents=intent)
bot.help_command = commands.DefaultHelpCommand(verify_checks=False)
bot.missile = Missile(bot)
bot.echo = bottas.Bottas(bot)
nickname = f"DimBot {'S ' if dimsecret.debug else ''}| 0.7.13"
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


@bot.group(invoke_without_command=True)
async def user(ctx, u: discord.User = None):
    u = u if u else ctx.author
    emb = discord.Embed(title=str(u), description=f"Send `{bot.command_prefix}user f <user>` for flag details")
    emb.set_thumbnail(url=u.avatar_url)
    emb.set_footer(text='Avatar hash: ' + str(u.avatar))
    emb.add_field(name='❄ ID', value=u.id)
    emb.add_field(name='Is bot?', value=u.bot)
    emb.add_field(name='Public flags', value=u.public_flags.value)
    emb.add_field(name='Created at', value=u.created_at)
    member: Optional[discord.Member] = None
    for g in bot.guilds:
        m = g.get_member(u.id)
        if m:
            member = m
            if m.voice:
                break
    # TODO: Use user.mutual_guilds to check status&activities instead when d.py 1.7 is released
    if member:
        emb.add_field(name='Number of activities', value=str(len(member.activities)) if member.activities else '0')
        stat = str(member.status)
        if member.desktop_status != discord.Status.offline:
            stat += ' 💻'
        if member.mobile_status != discord.Status.offline:
            stat += ' 📱'
        if member.web_status != discord.Status.offline:
            stat += ' 🌐'
        emb.add_field(name='Status', value=stat)
        if member.voice:
            v_state = str(member.voice.channel.id)
            if member.voice.self_mute:
                v_state += ' **Muted**'
            if member.voice.self_deaf:
                v_state += ' **Deaf**'
            if member.voice.self_stream:
                v_state += ' **Streaming**'
            emb.add_field(name='Voice channel ❄ ID', value=v_state)
    # Guild specific data
    if ctx.guild:
        member = ctx.guild.get_member(u.id)
        if member:
            emb.add_field(name='Joined at', value=member.joined_at)
            emb.add_field(name='Pending member?', value=member.pending)
            emb.add_field(name='Nitro boosting server since', value=member.premium_since)
            emb.add_field(name='Roles', value=' '.join([role.mention for role in member.roles[1:]][::-1]))
            emb.add_field(name='Permissions in this server', value=member.guild_permissions.value)
            emb.add_field(name='Permissions in this channel', value=member.permissions_in(ctx.channel).value)
            emb.colour = member.color
    emb.set_author(name=member.display_name if member else u.name, icon_url=u.default_avatar_url)
    await ctx.reply(embed=emb)


@user.command(aliases=['f'])
async def flags(ctx, u: discord.User = None):
    u = u if u else ctx.author
    bin_value = f'{u.public_flags.value:b}'
    hex_value = f'{u.public_flags.value:X}'
    emb = discord.Embed(title=u.name + "'s public flags",
                        description=f"{u.public_flags.value}, 0b{bin_value.zfill(17)}, "
                                    f"0x{hex_value.zfill(5)}",
                        color=Missile.random_rgb())
    emb.add_field(name='Verified bot developer', value=u.public_flags.verified_bot_developer)
    emb.add_field(name='Verified bot', value=u.public_flags.verified_bot)
    if u.public_flags.bug_hunter_level_2:
        emb.add_field(name='Bug hunter', value='**Level 2**')
    else:
        emb.add_field(name='Bug hunter', value=u.public_flags.bug_hunter)
    emb.add_field(name='Discord system', value=u.public_flags.system)
    emb.add_field(name='Team User', value=u.public_flags.team_user)
    emb.add_field(name='Early supporter', value=u.public_flags.early_supporter)
    if u.public_flags.hypesquad_balance:
        emb.add_field(name='HypeSquad', value='Balance')
    elif u.public_flags.hypesquad_bravery:
        emb.add_field(name='HypeSquad', value='Bravery')
    elif u.public_flags.hypesquad_brilliance:
        emb.add_field(name='HypeSquad', value='Brilliance')
    else:
        emb.add_field(name='HypeSquad', value=u.public_flags.hypesquad)
    emb.add_field(name='Discord partner', value=u.public_flags.partner)
    emb.add_field(name='Discord employee', value=u.public_flags.staff)
    await ctx.reply(embed=emb)


@bot.command()
async def sponsor(ctx):
    await ctx.send(sponsor_txt)


@bot.command()
async def noel(ctx):
    """Shows the ping of the bot"""
    msg = await ctx.send(f':heartbeat: {bot.latency*1000:.3f}ms')
    tic = datetime.now()
    await msg.add_reaction('📡')
    toc = datetime.now()
    await msg.edit(content=msg.content + f' :satellite_orbital: {(toc - tic).total_seconds()*1000}ms')


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
    if msg.author == msg.guild.me or msg.content.startswith(bot.command_prefix):
        return
    if msg.guild and msg.id in bot.missile.ghost_pings.keys():
        for m in bot.missile.ghost_pings[msg.id]:
            await m.send(f'{msg.author.mention} ({msg.author}) pinged you in **{msg.guild.name}** and deleted it.')
        await msg.channel.send(msg.author.mention + ' has deleted a ping')
        bot.missile.ghost_pings.pop(msg.id)
    elif msg.guild and msg.mentions and not msg.edited_at:
        for m in msg.mentions:
            if not m.bot:
                await m.send(f'{msg.author.mention} ({msg.author}) pinged you in **{msg.guild.name}** and deleted it.')
        await msg.channel.send(msg.author.mention + ' has deleted a ping')
    content = msg.content if msg.content else msg.embeds[0].title
    bot.missile.snipe = discord.Embed(title=msg.author.display_name, description=content)
    bot.missile.snipe.set_author(name=msg.guild.name, icon_url=msg.author.avatar_url)
    bot.missile.snipe.set_thumbnail(url=msg.guild.icon_url)
    bot.missile.snipe.colour = msg.embeds[0].colour if msg.embeds else Missile.random_rgb()


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
        await ctx.reply('Stoopid. That is not a command.')
        return
    if isinstance(error, commands.errors.MissingRequiredArgument) or isinstance(error, commands.errors.MissingAnyRole) \
            or isinstance(error, commands.errors.CommandOnCooldown) or isinstance(error, commands.errors.UserNotFound) \
            or isinstance(error, commands.errors.MemberNotFound):
        await ctx.reply(str(error))
        return
    if isinstance(error, commands.errors.ChannelNotFound):
        await ctx.reply("Invalid channel. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.RoleNotFound):
        await ctx.reply("Invalid role. Maybe you've tagged the wrong one?")
        return
    if isinstance(error, commands.errors.BadArgument):
        await ctx.reply('Bad arguments.')
    elif isinstance(error, commands.errors.CheckFailure) or isinstance(error, asyncio.TimeoutError):
        return
    raise error


@bot.command()
@Missile.is_rainbow_cmd_check()
async def exit(ctx):
    bot.echo.db.commit()
    await ctx.send(':dizzy_face:')
    await bot.logout()


bot.add_cog(ricciardo.Ricciardo(bot))
bot.add_cog(hamilton.Hamilton(bot))
bot.add_cog(verstapen.Verstapen(bot))
bot.add_cog(bot.echo)
bot.add_cog(bitbay.BitBay(bot))
bot.run(dimsecret.discord)
