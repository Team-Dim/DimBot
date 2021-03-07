import asyncio

import discord
from discord.ext.commands import Cog, command, Context, has_any_role, has_permissions, bot_has_permissions, guild_only, \
    has_guild_permissions, bot_has_guild_permissions

from missile import Missile


async def reply(ctx_msg, content: str):
    await ctx_msg.reply('**Ikaros:** ' + content)


async def send(msg: discord.Message, content: str):
    return await msg.channel.send('**Ikaros:** ' + content)


async def ensure_target(msg: discord.Message, target: discord.Member, countdown: int, check_role: bool = True):
    msg = await send(msg, "Attempting to lock target: " + target.mention)
    if check_role and (target.top_role >= msg.guild.me.top_role or Missile.is_rainbow(target.id)):
        await Missile.append_message(msg, 'Cannot lock target.')
        raise PermissionError
    else:
        await Missile.append_message(msg, 'Target locked.')
        for i in range(countdown, 0, -1):
            await Missile.append_message(msg, str(i))
            await asyncio.sleep(1)


async def kick(msg: discord.Message, target: discord.Member, countdown: int, reason: str):
    try:
        await ensure_target(msg, target, countdown)
        await target.kick(reason=reason)
        await send(msg, target.mention + ' has been kicked.')
    except PermissionError:
        return


async def ban(msg: discord.Message, target: discord.Member, countdown: int, reason: str):
    try:
        await ensure_target(msg, target, countdown)
        await target.ban(reason=reason)
        await send(msg, target.mention + ' has been banned.')
    except PermissionError:
        return


async def mute(msg: discord.Message, target: discord.Member, length: int, countdown: int, reason: str):
    try:
        await ensure_target(msg, target, countdown)
        role = None
        import bitbay
        import hamilton
        if msg.guild.id == bitbay.guild_id:
            role = msg.guild.get_role(718210713893601301)  # Muted Pirate
        elif msg.guild.id == hamilton.guild_id:
            role = msg.guild.get_role(474578007156326412)  # Asteroid Belt
        if role:
            await target.add_roles(role, reason=reason)
            await send(msg, 'Muted' + target.mention)
            if length:
                await asyncio.sleep(length)
                await target.remove_roles(role, reason='Deactivating ' + reason)
                await send(msg, 'Unmuted ' + target.mention)
    except PermissionError:
        return


async def unmute(msg: discord.Message, target: discord.Member, reason: str):
    role = None
    import bitbay
    import hamilton
    if msg.guild.id == bitbay.guild_id:
        role = msg.guild.get_role(718210713893601301)  # Muted Pirate
    elif msg.guild.id == hamilton.guild_id:
        role = msg.guild.get_role(474578007156326412)  # Asteroid Belt
    if role:
        await target.remove_roles(role, reason=reason)
        await send(msg, 'Unmuted ' + target.mention)


class Ikaros(Cog):
    """Moderation commands. For AutoMod please check out Aegis in the future
    Version 0.3"""

    def __init__(self, bot):
        self.bot = bot

    @command()
    @has_any_role(702608566845964338, 452859434104913931, 702889819570831572)
    @Missile.guild_only()
    async def role(self, ctx: Context, role: discord.Role, target: discord.Member):
        """Gives/removes a member's role"""
        if role >= ctx.guild.me.top_role:
            await reply(ctx, 'The role specified >= my highest role.')
            return
        if not Missile.is_rainbow(ctx.author.id) and role >= ctx.author.top_role:
            await reply(ctx, 'The role specified >= your highest role.')
            return
        if role.is_bot_managed():
            await reply(ctx, "Cannot assign a bot role")
            return
        if role in target.roles:
            await target.remove_roles(role, reason=f'Ikaros: Deleted by {ctx.author}')
            await reply(ctx, f'Removed **{role.name}** from {target}')
        else:
            await target.add_roles(role, reason=f'Ikaros: Added by {ctx.author}')
            await reply(ctx, f'Assigned **{role.name}** to {target}')

    @command(name='kick')
    @has_permissions(kick_members=True)
    @bot_has_permissions(kick_members=True)
    @Missile.guild_only()
    async def kick_cmd(self, ctx: Context, target: discord.Member, countdown: int = 3):
        await kick(ctx.message, target, countdown, f'Ikaros: Kicked by {ctx.author}')

    @command(name='ban')
    @has_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    @Missile.guild_only()
    async def ban_cmd(self, ctx: Context, target: discord.Member, countdown: int = 3):
        await ban(ctx.message, target, countdown, f'Ikaros: Banned by {ctx.author}')

    @command(name='mute')
    @has_guild_permissions(mute_members=True)
    @bot_has_guild_permissions(manage_roles=True)
    @Missile.guild_only()
    async def mute_cmd(self, ctx: Context, target: discord.Member, length: int = 0, countdown: int = 3):
        await mute(ctx.message, target, length, countdown, f'Ikaros: Muted by {ctx.author}')

    @command(name='unmute')
    @has_guild_permissions(mute_members=True)
    @bot_has_guild_permissions(manage_roles=True)
    @Missile.guild_only()
    async def unmute_cmd(self, ctx: Context, target: discord.Member):
        await unmute(ctx.message, target, f'Ikaros: Unmuted by {ctx.author}')

    @command()
    @Missile.guild_only()
    async def surprise(self, ctx: Context, target: discord.Member, countdown: int = 3):
        await ctx.message.delete()
        await ensure_target(ctx.message, target, countdown, False)
        await ctx.send('🥳 Surprise')
