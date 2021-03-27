import asyncio

import discord
from discord.ext.commands import Cog, command, Context, has_any_role, has_permissions, bot_has_permissions, \
    has_guild_permissions, bot_has_guild_permissions

from missile import Missile


async def reply(ctx_msg, content: str):
    """Appends Ikaros to the response and sends it"""
    await ctx_msg.reply('**Ikaros:** ' + content)


async def send(msg: discord.Message, content: str):
    """Appends Ikaros to the message and sends it"""
    return await msg.channel.send('**Ikaros:** ' + content)


async def ensure_target(msg: discord.Message, target: discord.Member, countdown: int, check_role: bool = True):
    """A fancy way to ensure that the action can be applied on the target"""
    msg = await send(msg, "Attempting to lock target: " + target.mention)
    if check_role and (target.top_role >= msg.guild.me.top_role or Missile.is_rainbow(target.id)):
        await Missile.append_message(msg, 'Cannot lock target.')
        raise PermissionError
    await Missile.append_message(msg, 'Target locked.')
    for i in range(countdown, 0, -1):
        await Missile.append_message(msg, str(i))
        await asyncio.sleep(1)


async def kick(msg: discord.Message, target: discord.Member, countdown: int, reason: str):
    """Internal logic for kicking member"""
    try:
        await ensure_target(msg, target, countdown)
        await target.kick(reason=reason)
        await send(msg, target.mention + ' has been kicked.')
    except PermissionError:
        return


async def ban(msg: discord.Message, target: discord.Member, length: int, countdown: int, reason: str):
    """Internal logic for banning member"""
    try:
        await ensure_target(msg, target, countdown)
        await target.ban(delete_message_days=0, reason=reason)
        await send(msg, f'Banning {target.mention} for {length}s')
        if length:  # Unbans if there is a ban time length
            await asyncio.sleep(length)
            await unban(msg, target, 'Deactivating ' + reason)
    except PermissionError:
        return


async def unban(msg: discord.Message, user: discord.User, reason: str):
    await msg.guild.unban(user, reason=reason)
    await send(msg, user.mention + ' has been unbanned.')


async def mute(msg: discord.Message, target: discord.Member, length: int, countdown: int, reason: str):
    """Internal logic for muting member"""
    try:
        await ensure_target(msg, target, countdown)
        role = None
        # Temporary mute system setup that only works in my server / 128BB
        import bitbay
        import tribe
        if msg.guild.id == bitbay.guild_id:
            role = msg.guild.get_role(718210713893601301)  # Muted Pirate
        elif msg.guild.id == tribe.guild_id:
            role = msg.guild.get_role(474578007156326412)  # Asteroid Belt
        if role:
            await target.add_roles(role, reason=reason)
            await send(msg, f'Muting {target.mention} for {length}s')
            if length:  # Unmutes if there is a mute time length
                await asyncio.sleep(length)
                await target.remove_roles(role, reason='Deactivating ' + reason)
                await send(msg, 'Unmuted ' + target.mention)
    except PermissionError:
        return


async def unmute(msg: discord.Message, target: discord.Member, reason: str):
    """Internal logic for unmuting member"""
    role = None
    import bitbay
    import tribe
    if msg.guild.id == bitbay.guild_id:
        role = msg.guild.get_role(718210713893601301)  # Muted Pirate
    elif msg.guild.id == tribe.guild_id:
        role = msg.guild.get_role(474578007156326412)  # Asteroid Belt
    if role:
        await target.remove_roles(role, reason=reason)
        await send(msg, 'Unmuted ' + target.mention)


class Ikaros(Cog):
    """Moderation commands. For AutoMod please check out Aegis in the future
    Version 0.4"""

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
        """Kicks a member"""
        await kick(ctx.message, target, countdown, f'Ikaros: Kicked by {ctx.author}')

    @command(name='ban')
    @has_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    @Missile.guild_only()
    async def ban_cmd(self, ctx: Context, target: discord.Member, length: int = None, countdown: int = 3):
        """Bans a member. Can define a time to auto unban"""
        await ban(ctx.message, target, length, countdown, f'Ikaros: Banned by {ctx.author}')

    @command(name='unban')
    @has_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    @Missile.guild_only()
    async def unban_cmd(self, ctx: Context, target: discord.User):
        """Unbans a user"""
        await unban(ctx.message, target, f'Ikaros: Unbanned by {ctx.author}')

    @command(name='mute')
    @has_guild_permissions(mute_members=True)
    @bot_has_guild_permissions(manage_roles=True)
    @Missile.guild_only()
    async def mute_cmd(self, ctx: Context, target: discord.Member, countdown: int = 3, length: int = None):
        """Mutes a member. Can define a time to auto unmute"""
        await mute(ctx.message, target, length, countdown, f'Ikaros: Muted by {ctx.author}')

    @command(name='unmute')
    @has_guild_permissions(mute_members=True)
    @bot_has_guild_permissions(manage_roles=True)
    @Missile.guild_only()
    async def unmute_cmd(self, ctx: Context, target: discord.Member):
        """Unmutes a member"""
        await unmute(ctx.message, target, f'Ikaros: Unmuted by {ctx.author}')

    @command()
    @Missile.guild_only()
    async def surprise(self, ctx: Context, target: discord.Member, countdown: int = 3):
        """Gives the member a surprise"""
        await ctx.message.delete()
        await ensure_target(ctx.message, target, countdown, False)
        await ctx.send('🥳 Surprise')
