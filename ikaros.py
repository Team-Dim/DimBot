import asyncio

import discord
from discord.ext.commands import Cog, command, Context, has_any_role, has_permissions, bot_has_permissions

from missile import Missile


async def reply(ctx: Context, content: str):
    await ctx.reply('**Ikaros:** ' + content)


async def send(ctx: Context, content: str):
    return await ctx.send('**Ikaros:** ' + content)


class Ikaros(Cog):
    """Moderation commands. For AutoMod please check out Aegis in the future
    Version 0.2.1"""

    def __init__(self, bot):
        self.bot = bot

    @command()
    @Missile.guild_only()
    @has_any_role(702608566845964338, 452859434104913931, 702889819570831572)
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

    @command()
    @Missile.guild_only()
    @has_permissions(kick_members=True)
    @bot_has_permissions(kick_members=True)
    async def kick(self, ctx: Context, target: discord.Member, countdown: int = 3):
        msg = await send(ctx, "Attempting to lock target: " + target.mention)
        if target.top_role >= ctx.guild.me.top_role or Missile.is_rainbow(target.id):
            await Missile.append_message(msg, 'Cannot lock target.')
            return
        await Missile.append_message(msg, 'Target locked.')
        for i in range(countdown, 0, -1):
            await Missile.append_message(msg, str(i))
            await asyncio.sleep(1)
        await target.kick(reason=f'Ikaros: Kicked by {ctx.author}')
        await send(ctx, target.mention + ' has been kicked.')

    @command()
    @Missile.guild_only()
    @has_permissions(ban_members=True)
    @bot_has_permissions(ban_members=True)
    async def ban(self, ctx: Context, target: discord.Member, countdown: int = 3):
        msg = await send(ctx, "Attempting to lock target: " + target.mention)
        if target.top_role >= ctx.guild.me.top_role or Missile.is_rainbow(target.id):
            await Missile.append_message(msg, 'Cannot lock target.')
            return
        await Missile.append_message(msg, 'Target locked.')
        for i in range(countdown, 0, -1):
            await Missile.append_message(msg, str(i))
            await asyncio.sleep(1)
        await target.ban(reason=f'Ikaros: Banned by {ctx.author}')
        await send(ctx, target.mention + ' has been banned.')
