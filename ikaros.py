import asyncio

import discord
from discord.ext.commands import Cog, command, Context, has_any_role

from missile import Missile


async def reply(ctx: Context, content: str):
    await ctx.reply('**Ikaros:** ' + content)


async def send(ctx: Context, content: str):
    return await ctx.send('**Ikaros:** ' + content)


class Ikaros(Cog):
    """Moderation commands. For AutoMod please check out Aegis in the future
    Version 0.2"""

    def __init__(self, bot):
        self.bot = bot

    @command()
    @Missile.guild_only()
    @has_any_role(702608566845964338, 452859434104913931, 702889819570831572)
    async def role(self, ctx: Context, role: discord.Role, target: discord.Member):
        """Gives/removes a member's role"""
        if role >= ctx.guild.me.roles[-1]:
            await reply(ctx, 'The role specified >= my highest role.')
            return
        if not Missile.is_rainbow(ctx) and role >= ctx.author.roles[-1]:
            await reply(ctx, 'The role specified >= your highest role.')
            return
        if role in target.roles:
            await target.remove_roles(role, reason=f'Ikaros: Deleted by {ctx.author}')
            await reply(ctx, f'Removed **{role.name}** from {target}')
        else:
            await target.add_roles(role, reason=f'Ikaros: Added by {ctx.author}')
            await reply(ctx, f'Assigned **{role.name}** to {target}')

    @command()
    @Missile.guild_only()
    @has_any_role(702608566845964338, 452859434104913931, 702889819570831572)
    async def kick(self, ctx: Context, target: discord.Member):
        msg = await send(ctx, "Target locked: " + target.mention)
        for i in range(3, 0, -1):
            await Missile.append_message(msg, str(i))
            await asyncio.sleep(1)
        await target.kick(reason=f'Ikaros: Kicked by {ctx.author}')
        switch = "**NOT**" if ctx.guild.get_member(target.id) else ''
        await ctx.send(target.mention + ' has ' + switch + ' been kicked.')
