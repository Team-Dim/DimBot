import discord
from discord.ext.commands import Cog

guild_id = 285366651312930817


class Hamilton(Cog):
    """Dim's guild specific features
    Version 1.3.1"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Hamilton')
        self.invites = []
        self.bbm_role = None

    async def get_join_invite(self) -> discord.Invite:
        """Returns the invite used by a member.This is done by first caching self.invites in on_ready() then compare
        each invite count on on_member_join()"""
        invites = await self.bot.missile.guild.invites()
        for i, invite in enumerate(invites):
            if invite.uses != self.invites[i].uses:
                self.invites = invites
                return invite

    @Cog.listener()
    async def on_ready(self):
        # Caches invites
        self.invites = await self.bot.missile.guild.invites()

    @Cog.listener()
    async def on_member_join(self, member: discord.Member):
        if member.guild == self.bot.missile.guild:  # Only activates if its in my server
            invite = await self.get_join_invite()
            await self.bot.missile.logs.send(f"{member.mention} ({member}) joined via code `{invite.code}` "
                                             f"{invite.channel.mention}")
            if invite.code == 'g6Yrteq':  # Joined via BBM invite
                role = self.bot.missile.guild.get_role(664210105318768661)
                await member.add_roles(role)
                ch = self.bot.missile.bottyland
                await ch.send(
                    f'Welcome {member.mention}! You are automatically added to the role {role.name} '
                    f'for related announcements.'
                    f' If you wish to unsubscribe, please send `?rank {role.name}` in {ch.mention}.'
                )

    @Cog.listener()
    async def on_member_left(self, member: discord.Member):
        if member.guild == self.bot.missile.guild:
            await self.bot.missile.logs.send(f'{member.mention} has left.')

    @Cog.listener()
    async def on_voice_state_update(self, mem: discord.Member, before, after: discord.VoiceState):
        """I hate people being invisible"""
        if mem.guild == self.bot.missile.guild and after.channel and mem.status == discord.Status.offline:
            await mem.send(f"Please don't set your status as invisible while online in {mem.guild.name} :)")

    @Cog.listener()
    async def on_typing(self, channel, user, when):
        """I hate people being invisible"""
        if channel.type == discord.ChannelType.text:
            if user.guild == self.bot.missile.guild and user.status == discord.Status.offline \
                    and channel.type == discord.ChannelType.text:
                await user.send(f"Please don't set your status as invisible while online in {user.guild.name} :)")
