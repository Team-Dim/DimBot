import asyncio

import discord
from discord.ext.commands import Cog, command, Context, has_permissions, bot_has_permissions, has_guild_permissions, \
    bot_has_guild_permissions, group

import bitbay
import obj
import tribe
from missile import Missile


async def reply(ctx_msg, content: str):
    """Appends Ikaros to the response and sends it"""
    await ctx_msg.reply('**Ikaros:** ' + content)


async def send(msg: discord.Message, content: str):
    """Appends Ikaros to the message and sends it"""
    return await msg.channel.send('**Ikaros:** ' + content)


class Ikaros(Cog):
    """Moderation commands. For AutoMod please check out Aegis
    Version 0.5.1"""

    def __init__(self, bot):
        self.bot = bot

    async def ensure_target(self, msg: discord.Message, target: discord.Member, countdown: int,
                            check_role: bool = True):
        """A fancy way to ensure that the action can be applied on the target"""
        msg = await send(msg, "Attempting to lock target: " + target.mention)
        if check_role and (target.top_role >= msg.guild.me.top_role or target.id == self.bot.owner_id):
            await obj.append_msg(msg, 'Cannot lock target.')
            raise PermissionError
        await obj.append_msg(msg, 'Target locked.')
        for i in range(countdown, 0, -1):
            await obj.append_msg(msg, str(i))
            await asyncio.sleep(1)

    async def kick(self, msg: discord.Message, target: discord.Member, countdown: int, reason: str):
        """Internal logic for kicking member"""
        try:
            if not msg.guild.me.guild_permissions.kick_members:
                await msg.channel.send("I don't have kick permission.")
                return
            await self.ensure_target(msg, target, countdown)
            await target.kick(reason=reason)
            await send(msg, target.mention + ' has been kicked.')
        except PermissionError:
            return

    async def ban(self, msg: discord.Message, target: discord.Member, length: int, countdown: int, reason: str):
        """Internal logic for banning member"""
        try:
            if not msg.guild.me.guild_permissions.ban_members:
                await msg.channel.send("I don't have ban permission.")
                return
            await self.ensure_target(msg, target, countdown)
            await target.ban(delete_message_days=0, reason=reason)
            await send(msg, f'Banning {target.mention} for {length}s')
            if length:  # Unbans if there is a ban time length
                await asyncio.sleep(length)
                await self.unban(msg, target, 'Deactivating ' + reason)
        except PermissionError:
            return

    @staticmethod
    async def unban(msg: discord.Message, user: discord.User, reason: str):
        await msg.guild.unban(user, reason=reason)
        await send(msg, user.mention + ' has been unbanned.')

    async def mute(self, msg: discord.Message, target: discord.Member, length: int, countdown: int, reason: str):
        """Internal logic for muting member"""
        try:
            if not msg.guild.me.guild_permissions.manage_roles:
                await msg.channel.send("I don't have Manage Roles permission.")
                return
            await self.ensure_target(msg, target, countdown)
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

    @staticmethod
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

    @command()
    @has_guild_permissions(manage_roles=True)
    @bot_has_guild_permissions(manage_roles=True)
    @Missile.guild_only()
    async def role(self, ctx: Context, role: discord.Role, target: discord.Member):
        """Gives/removes a member's role"""
        if role >= ctx.guild.me.top_role:
            await reply(ctx, 'The role specified >= my highest role.')
            return
        if ctx.author.id != self.bot.owner_id and role >= ctx.author.top_role:
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
        await self.kick(ctx.message, target, countdown, f'Ikaros: Kicked by {ctx.author}')

    @command(name='ban')
    @has_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    @Missile.guild_only()
    async def ban_cmd(self, ctx: Context, target: discord.Member, length: int = None, countdown: int = 3):
        """Bans a member. Can define a time to auto unban"""
        await self.ban(ctx.message, target, length, countdown, f'Ikaros: Banned by {ctx.author}')

    @command(name='unban')
    @has_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    @Missile.guild_only()
    async def unban_cmd(self, ctx: Context, target: discord.User):
        """Unbans a user"""
        await self.unban(ctx.message, target, f'Ikaros: Unbanned by {ctx.author}')

    @command(name='mute')
    @has_guild_permissions(mute_members=True)
    @bot_has_guild_permissions(manage_roles=True)
    @Missile.is_guild_cmd_check(bitbay.guild_id, tribe.guild_id)
    async def mute_cmd(self, ctx: Context, target: discord.Member, length: int = None, countdown: int = 3):
        """Mutes a member. Can define a time to auto unmute"""
        await self.mute(ctx.message, target, length, countdown, f'Ikaros: Muted by {ctx.author}')

    @command(name='unmute')
    @has_guild_permissions(mute_members=True)
    @bot_has_guild_permissions(manage_roles=True)
    @Missile.is_guild_cmd_check(bitbay.guild_id, tribe.guild_id)
    async def unmute_cmd(self, ctx: Context, target: discord.Member):
        """Unmutes a member"""
        await self.unmute(ctx.message, target, f'Ikaros: Unmuted by {ctx.author}')

    @command()
    @Missile.guild_only()
    async def surprise(self, ctx: Context, target: discord.Member, countdown: int = 3):
        """Gives the member a surprise"""
        await ctx.message.delete()
        await self.ensure_target(ctx.message, target, countdown, False)
        await ctx.send('🥳 Surprise')

    @group(invoke_without_command=True)
    @has_guild_permissions(manage_messages=True)
    @bot_has_guild_permissions(manage_messages=True, read_message_history=True)
    @Missile.guild_only()
    async def purge(self, ctx: Context, amount: int):
        """Purges messages (excluding the command)"""
        msgs = await ctx.channel.purge(limit=amount, before=ctx.message)
        await send(ctx.message, f'Purged {len(msgs)} messages.')

    @purge.command()
    @has_guild_permissions(manage_messages=True)
    @bot_has_guild_permissions(manage_messages=True, read_message_history=True)
    @Missile.guild_only()
    async def by(self, ctx: Context, sender: discord.User, amount: int):
        """d.purge but only deletes up to the specified amount of the sender's messages"""
        msgs = await ctx.channel.purge(check=lambda m: m.author == sender, limit=amount, before=ctx.message)
        await send(ctx.message, f'Purged {len(msgs)} messages.')

    @command()
    @Missile.guild_only()
    async def preprune(self, ctx: Context, days: int):
        """Checks how many members will be pruned. Must specify the number of days before counting as inactive."""
        if 0 < days < 31:
            async with ctx.typing():
                await ctx.reply(f'**{await ctx.guild.estimate_pruned_members(days=days)}** members will be pruned.')
        else:
            await ctx.reply('Days should be 1-30 inclusive.')
