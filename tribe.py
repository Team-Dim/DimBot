import asyncio
from typing import Optional

import discord
from discord.ext.commands import Cog, Context, group, has_guild_permissions

import missile

guild_id = 285366651312930817


async def solo_vc(vc):
    await asyncio.sleep(vc.guild.afk_timeout)
    if len(vc.members) == 1:
        await vc.members[0].move_to(None)


class Hamilton(Cog):
    """Per-guild features
    Version 2.0"""

    def __init__(self, bot: missile.Bot):
        self.bot = bot
        self.invites = {}
        self.guild = bot.get_guild(guild_id)  # My own server
        self.logs = bot.get_channel(384636771805298689)  # #logs in my server
        self.bot_test = bot.get_channel(666431254312517633)  # #bot_test

    async def get_join_invite(self) -> discord.Invite:
        """Returns the invite used by a member.This is done by first caching self.invites in on_ready() then compare
        each invite count on on_member_join()"""
        invites = await self.get_invites_dict()
        for code in invites.keys():
            if code in self.invites:
                if invites[code] != self.invites[code]:
                    self.invites = invites
                    return code
            elif invites[code]:
                self.invites = invites
                return code

    async def get_invites_dict(self) -> dict:
        invites = await self.guild.invites()
        d = {}
        for invite in invites:
            d[invite.code] = invite.uses
        return d

    @Cog.listener()
    async def on_ready(self):
        self.invites = await self.get_invites_dict()  # Caches invites

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.guild and msg.content == msg.guild.me.mention:
            p = await self.bot.get_prefix(msg)
            if p == self.bot.default_prefix:
                await msg.channel.send(f'My prefix is **{self.bot.default_prefix}**')
            else:
                await msg.channel.send(f"My prefixes are **{'**, **'.join(p)}**")

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild == self.guild:  # Only activates if its in my server
            invite = await self.get_join_invite()
            await self.logs.send(f"{member.mention} ({member}) joined via code `{invite}`")
            if invite == 'g6Yrteq':  # Joined via BBM invite
                role = self.guild.get_role(664210105318768661)
                await member.add_roles(role)
                ch = self.bot.get_channel(372386868236386307)  # Bottyland
                await ch.send(
                    f'Welcome {member.mention}! You are automatically added to the role {role.name} '
                    f'for related announcements.'
                    f' If you wish to unsubscribe, please send `?rank {role.name}` in {ch.mention}.'
                )

    @Cog.listener()
    async def on_member_left(self, member: discord.Member):
        if member.guild == self.guild:
            await self.logs.send(f'{member.mention} has left.')

    @Cog.listener()
    async def on_voice_state_update(self, m: discord.Member, before, after: discord.VoiceState):
        """Anti AFK & Invisible"""
        if await self.bot.sql.get_anti_invisible(self.bot.db, guild=m.guild.id) and \
                after.channel and m.status == discord.Status.offline:
            await m.send(f"Please don't set your status as invisible while online in {m.guild.name} :)")
        if before.channel and len(before.channel.members) == 1 and not after.channel \
                and before.channel.guild.me.guild_permissions.move_members:
            await solo_vc(before.channel)
        elif after.channel and after.channel.guild.me.guild_permissions.move_members:  # Joined a VC
            if after.afk and after.channel.type == discord.ChannelType.voice:
                await m.move_to(None)  # Joined AFK VC
            elif len(after.channel.members) == 1:
                await solo_vc(after.channel)

    @Cog.listener()
    async def on_typing(self, channel, user, when):
        """I hate people being invisible"""
        if channel.type == discord.ChannelType.text and \
                await self.bot.sql.get_anti_invisible(self.bot.db, guild=user.guild.id) and \
                user.status == discord.Status.offline:
            await user.send(f"Please don't set your status as invisible while online in {user.guild.name} :)")

    @Cog.listener()
    async def on_guild_join(self, guild: discord.Guild):
        await self.bot_test.send(f'Joined server {guild.id} {guild.name} <@{self.bot.owner_id}>')
        if await self.bot.sql.is_guild_banned(self.bot.db, id=guild.id):
            await guild.leave()
            return
        await self.bot.sql.add_guild_cfg(self.bot.db, guildID=guild.id)
        if guild.me.guild_permissions.change_nickname:
            await guild.me.edit(nick=self.bot.nickname)

    @Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        await self.bot_test.send(f'Left server {guild.id} {guild.name}')

    @Cog.listener()
    async def on_guild_role_delete(self, role: discord.Role):
        await self.bot.sql.remove_joinable_role(self.bot.db, role=role.id)

    @group()
    @missile.guild_only()
    @has_guild_permissions(manage_guild=True)
    async def guild(self, ctx: Context):
        """Settings for server"""
        if not ctx.invoked_subcommand:
            self.bot.help_command.context = ctx
            await self.bot.help_command.send_group_help(ctx.command)

    @guild.command(brief='Changes the custom prefix of DimBot')
    async def prefix(self, ctx: Context, *, p: str = None):
        """`guild  prefix [p]`
        `p` is a SENTENCE so you can send like `Super bad prefix` as `p` without quotation marks.
        Note that d. will still work. Send the command without arguments to remove the custom prefix."""
        if p and (p.lower().startswith('dimbot') or ctx.me.mention in p):
            await ctx.reply('Only my little pog champ can use authoritative orders!')
        else:
            await self.bot.sql.update_guild_prefix(self.bot.db, guildID=ctx.guild.id, prefix=p)
            await ctx.reply('Updated server prefix.')

    @guild.command(brief='Sets the moderation role of the server')
    async def modrole(self, ctx: Context, role: discord.Role):
        """guild modrole <role>"""
        await self.bot.sql.set_mod_role(self.bot.db, role=role.id, guild=ctx.guild.id)
        await ctx.reply('Updated moderation role to ' + role.name)

    @guild.command(brief='Sets snipe discovery for the server')
    async def snipe(self, ctx: Context, level: int = 2):
        """This command sets whether snipes can work and whether they are visible in other servers.

        0: Snipe/GSnipe will not detect deleted messages in this server at all.
        1: Snipe will detect but the detected messages are only visible in this server (`gsnipe` won't display)
        2 (default): Snipe will detect and they are visible in other servers (`gsnipe` can display this server's snipes)"""
        if 0 <= level <= 2:
            await self.bot.sql.set_snipe_cfg(self.bot.db, snipe=level, guild=ctx.guild.id)
            await ctx.reply('Updated snipe discovery level')
        else:
            await ctx.reply(
                f'Invalid discovery level! Please send `{await self.bot.get_prefix(ctx.message)}help guild snipe`!')

    @guild.command(brief='Toggles auto kicking members from VC when they afk')
    async def antiafk(self, ctx: Context, enable: bool = True):
        """guild antiafk [enable]
        enable: Whether to enable the feature or not. Defaults to yes."""
        await self.bot.sql.set_anti_afk(self.bot.db, antiafk=enable, guild=ctx.guild.id)
        await ctx.reply('Updated!')

    @guild.command(aliases=('invis', 'invi'), brief='Toggles anti invisible feature')
    async def invisible(self, ctx: Context, enable: bool = False):
        """guild invisible [enable]
        enable: Whether to enable the feature or not. Defaults to no."""
        await self.bot.sql.set_anti_invisible(self.bot.db, invisible=enable, guild=ctx.guild.id)
        await ctx.reply('Updated!')

    @guild.command(brief='Sets a joinable role')
    async def setjr(self, ctx: Context, role: discord.Role, required_role: Optional[discord.Role],
                    check_highest: bool = True):
        """`guild setjr <role> [required role] [check highest]`
        role: The joinable role that is to be modified/added
        required role: The optional required role that is needed to join this role. You can literally skip this argument
        check highest: Whether only allows to join role if the role is at a lower position then the sender's
        highest role"""
        required = required_role.id if required_role else None
        if await self.bot.sql.get_joinable_role(self.bot.db, role.id):
            await self.bot.sql.update_joinable_role(self.bot.db, role=role.id, required=required,
                                                    checkHighest=check_highest)
        else:
            await self.bot.sql.add_joinable_role(self.bot.db, role=role.id, required=required,
                                                 checkHighest=check_highest)
        await ctx.reply(embed=missile.Embed(description=f"""Joinable role: {role.mention}
                                            Required role: {required_role.mention if required_role else 'None'}
                                            Check highest role: {check_highest}"""))

    @guild.command(brief='Deletes a joinable role')
    async def deljr(self, ctx: Context, role: discord.Role):
        """`guild deljr <role>
        role: The joinable role to be removed from the database"""
        await self.bot.sql.remove_joinable_role(self.bot.db, role=role.id)
        await ctx.reply('Deleted')
