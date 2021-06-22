import asyncio
from typing import Union

import discord
from discord.ext.commands import Cog, command, Context, has_permissions, bot_has_permissions, has_guild_permissions, \
    bot_has_guild_permissions

import diminator
import missile
import tribe

ext = missile.MsgExt('Ikaros')


class Ikaros(Cog):
    """Active moderation system
    Version 0.6"""

    def __init__(self, bot):
        self.bot = bot

    async def ensure_target(self, msg: discord.Message, target: Union[discord.Member, discord.User], countdown: int,
                            check_role: bool = True):
        """A fancy way to ensure that the action can be applied on the target"""
        if countdown > 30 or countdown < 0:
            await ext.reply(msg, 'Countdown should be between 0 and 30!')
            return
        msg = await ext.send(msg, "Attempting to lock target: " + target.mention)
        if isinstance(target, discord.Member) and check_role:
            if target.top_role >= msg.guild.me.top_role or target.id == self.bot.owner_id:
                await missile.append_msg(msg, 'Cannot lock target.')
                raise PermissionError
        await missile.append_msg(msg, 'Target locked.')
        for i in range(countdown, 0, -1):
            await missile.append_msg(msg, str(i))
            await asyncio.sleep(1)

    async def kick(self, msg: discord.Message, target: discord.Member, countdown: int, reason: str):
        """Internal logic for kicking member"""
        try:
            if not msg.guild.me.guild_permissions.kick_members:
                await msg.channel.send("I don't have kick permission.")
                return
            await self.ensure_target(msg, target, countdown)
            await target.kick(reason=reason)
            await ext.send(msg, target.mention + ' has been kicked.')
        except PermissionError:
            return

    async def ban(self, msg: discord.Message, target: Union[discord.Member, discord.User],
                  length: int, countdown: int, reason: str):
        """Internal logic for banning member"""
        try:
            if not msg.guild.me.guild_permissions.ban_members:
                await msg.channel.send("I don't have ban permission.")
                return
            await self.ensure_target(msg, target, countdown)
            await msg.guild.ban(target, delete_message_days=0, reason=reason)
            await ext.send(msg, f'Banning {target.mention} for {length}s')
            if length:  # Unbans if there is a ban time length
                await asyncio.sleep(length)
                await self.unban(msg, target, 'Deactivating ' + reason)
        except PermissionError:
            return

    @staticmethod
    async def unban(msg: discord.Message, user: discord.User, reason: str):
        await msg.guild.unban(user, reason=reason)
        await ext.send(msg, user.mention + ' has been unbanned.')

    async def mute(self, msg: discord.Message, target: discord.Member, length: int, countdown: int, reason: str):
        """Internal logic for muting member"""
        try:
            if not msg.guild.me.guild_permissions.manage_roles:
                await msg.channel.send("I don't have Manage Roles permission.")
                return
            await self.ensure_target(msg, target, countdown)
            role = None
            # Temporary mute system setup that only works in my server
            if msg.guild.id == tribe.guild_id:
                role = msg.guild.get_role(474578007156326412)  # Asteroid Belt
            if role:
                await target.add_roles(role, reason=reason)
                await ext.send(msg, f'Muting {target.mention} for {length}s')
                if length:  # Unmutes if there is a mute time length
                    await asyncio.sleep(length)
                    if role in target.roles:
                        await target.remove_roles(role, reason='Deactivating ' + reason)
                        await ext.send(msg, 'Unmuted ' + target.mention)
        except PermissionError:
            return

    @staticmethod
    async def unmute(msg: discord.Message, target: discord.Member, reason: str):
        """Internal logic for unmuting member"""
        role = None
        if msg.guild.id == tribe.guild_id:
            role = msg.guild.get_role(474578007156326412)  # Asteroid Belt
        if role:
            await target.remove_roles(role, reason=reason)
            await ext.send(msg, 'Unmuted ' + target.mention)

    @command(brief='Assign/Remove a role from a member.')
    @has_guild_permissions(manage_roles=True)
    @bot_has_guild_permissions(manage_roles=True)
    @missile.guild_only()
    async def role(self, ctx: Context, role: discord.Role, target: discord.Member):
        """`role <role> <target>`"""
        if role >= ctx.guild.me.top_role:
            await ext.reply(ctx, 'The role specified >= my highest role.')
            return
        if ctx.author.id != self.bot.owner_id and role >= ctx.author.top_role:
            await ext.reply(ctx, 'The role specified >= your highest role.')
            return
        if role.is_bot_managed():
            await ext.reply(ctx, "Cannot assign a bot role")
            return
        if role in target.roles:
            await target.remove_roles(role, reason=f'Ikaros: Deleted by {ctx.author}')
            await ext.reply(ctx, f'Removed **{role.name}** from {target}')
        else:
            await target.add_roles(role, reason=f'Ikaros: Added by {ctx.author}')
            await ext.reply(ctx, f'Assigned **{role.name}** to {target}')

    @command(name='kick', brief='Kicks a member')
    @missile.bot_has_perm(kick_members=True)
    @has_permissions(kick_members=True)
    @missile.guild_only()
    async def kick_cmd(self, ctx: Context, target: discord.Member, countdown: int = 3):
        """`kick <target> [countdown]`
        countdown: Number of seconds to countdown before actually kicking the member. Defaults to 3"""
        await self.kick(ctx.message, target, countdown, f'Ikaros: Kicked by {ctx.author}')

    @command(name='ban', brief='Bans a user')
    @missile.bot_has_perm(ban_members=True)
    @has_permissions(ban_members=True)
    @missile.guild_only()
    async def ban_cmd(self, ctx: Context, target: Union[discord.Member, discord.User],
                      length: int = None, countdown: int = 3):
        """`ban <target> [length] [countdown]`
        length: Time length of the ban in seconds.
        countdown: Number of seconds to countdown before actually banning the member. Defaults to 3"""
        """Bans a member. Can define a time to auto unban"""
        await self.ban(ctx.message, target, length, countdown, f'Ikaros: Banned by {ctx.author}')

    @command(name='unban', brief='Unbans a user')
    @has_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    @missile.guild_only()
    async def unban_cmd(self, ctx: Context, target: discord.User):
        """unban <target>"""
        await self.unban(ctx.message, target, f'Ikaros: Unbanned by {ctx.author}')

    @command(name='mute', brief='Mutes a member')
    @has_guild_permissions(mute_members=True)
    @bot_has_guild_permissions(manage_roles=True)
    @missile.in_guilds(tribe.guild_id)
    async def mute_cmd(self, ctx: Context, target: discord.Member, length: int = 0, countdown: int = 3):
        """`mute <target> [length] [countdown]`
        length: Time length of the mute in seconds.
        countdown: Number of seconds to countdown before actually muting the member. Defaults to 3"""
        """Mutes a member. Can define a time to auto unmute"""
        await self.mute(ctx.message, target, length, countdown, f'Ikaros: Muted by {ctx.author}')

    @command(name='unmute', brief='Unmutes a member')
    @has_guild_permissions(mute_members=True)
    @bot_has_guild_permissions(manage_roles=True)
    @missile.in_guilds(tribe.guild_id)
    async def unmute_cmd(self, ctx: Context, target: discord.Member):
        """unmute <target>"""
        await self.unmute(ctx.message, target, f'Ikaros: Unmuted by {ctx.author}')

    @command(brief='Scares the member with a fake action')
    @missile.guild_only()
    async def surprise(self, ctx: Context, target: discord.Member, countdown: int = 3):
        """`surprise <target> [countdown]`
        countdown: Number of seconds to countdown for the fake action. Defaults to 3
        """
        with self.bot.get_cog('Aegis').no_ghost_ping(ctx.channel.id):
            await ctx.message.delete()
        await self.ensure_target(ctx.message, target, countdown, False)
        await ctx.send('🥳 Surprise')

    @command(brief='Purges messages (excluding the command)')
    @has_guild_permissions(manage_messages=True)
    @bot_has_guild_permissions(manage_messages=True, read_message_history=True)
    @missile.guild_only()
    async def purge(self, ctx: Context, amount_to_check: int, sender: discord.User = None):
        """`purge <amount to check> [sender]`
        amount to check: The amount of messages to check whether it is eligible to be deleted.
        Purge checks the messages in that channel from latest to oldest.
        If `sender` is empty, bot should purge exactly the amount of messages specified in the check.
        If `sender` is specified, bot will check the messages one by one and deletes those sent by the `sender`
        until it has checked `amount to check` number of messages."""
        with self.bot.get_cog('Aegis').no_ghost_ping_notification(ctx.channel.id):
            if sender:
                msgs = await ctx.channel.purge(
                    check=lambda m: m.author == sender, limit=amount_to_check, before=ctx.message
                )
            else:
                msgs = await ctx.channel.purge(limit=amount_to_check, before=ctx.message)
            await ext.send(ctx, f'Purged {len(msgs)} messages.')

    @command(brief='Checks how many members will be pruned')
    @missile.guild_only()
    @bot_has_guild_permissions(kick_members=True)
    async def preprune(self, ctx: Context, days: int):
        """`preprune <days>`
        days: The number of days before counting as inactive."""
        if 0 < days < 31:
            async with ctx.typing():
                await ctx.reply(f'**{await ctx.guild.estimate_pruned_members(days=days)}** members will be pruned.')
        else:
            await ctx.reply('Days should be 1-30 inclusive.')

    @command(brief='Locks down a server')
    @missile.bot_has_perm(manage_permissions=True)
    @missile.is_mod()
    @missile.guild_only()
    async def lockdown(self, ctx: Context, can_view_channel: bool = True):
        """`lockdown <can_view_channel>`
        If can_view_channel is True, then affected roles just can't send messages.
        If False, then they can't even view the channels."""
        async with ctx.typing():
            tasks = []
            og_perms = await self.bot.sql.get_lockdown(self.bot.db, guild=ctx.guild.id)
            if og_perms:
                for record in og_perms:
                    role = ctx.guild.get_role(record[0])
                    if role:
                        tasks.append(role.edit(permissions=discord.Permissions(record[1]), reason='Removing lockdown'))
                tasks.append(self.bot.sql.remove_lockdown(self.bot.db, guild=ctx.guild.id))
                await asyncio.wait(tasks)
                await ctx.reply('Removed lockdown.')
            else:
                mod = ctx.guild.get_role(await self.bot.sql.get_mod_role(self.bot.db, guild=ctx.guild.id))
                roles = ctx.guild.roles
                if mod:
                    for i in range(len(roles)-1, -1, -1):
                        if roles[i] >= mod or roles[i] >= ctx.guild.me.top_role:
                            roles.pop(i)
                        else:
                            break
                for role in roles:
                    if can_view_channel:
                        if role.permissions.send_messages:
                            tasks.append(self.bot.sql.add_lockdown(
                                    self.bot.db, guild=ctx.guild.id, role=role.id, perm=role.permissions.value
                                ))
                            tasks.append(role.edit(
                                    permissions=discord.Permissions(role.permissions.value, send_messages=False),
                                    reason='Manual lockdown'
                                ))
                    else:
                        if role.permissions.view_channel:
                            tasks.append(self.bot.sql.add_lockdown(
                                    self.bot.db, guild=ctx.guild.id, role=role.id, perm=role.permissions.value
                                ))
                            tasks.append(role.edit(
                                    permissions=discord.Permissions(role.permissions.value, view_channel=False),
                                    reason='Manual Lockdown'
                                ))
                await asyncio.wait(tasks)
                await ctx.reply('Lockdown.')


