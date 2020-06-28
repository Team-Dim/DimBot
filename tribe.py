import discord
from discord.ext.commands import Cog

__version__ = '1.3'


class Tribe(Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Tribe')
        self.invites = []
        self.bbm_role = None

    async def get_join_invite(self) -> discord.Invite:
        invites = await self.bot.missile.guild.invites()
        for i, invite in enumerate(invites):
            if invite.uses != self.invites[i].uses:
                self.invites = invites
                return invite

    @Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')
        self.invites = await self.bot.missile.guild.invites()

    @Cog.listener()
    async def on_member_join(self, member):
        invite = await self.get_join_invite()
        await self.bot.missile.logs.send(f"{member.mention} ({member}) joined via code `{invite.code}` {invite.channel.mention}")
        if invite.code == 'g6Yrteq':
            role = self.bot.missile.guild.get_role(664210105318768661)
            await member.add_roles(role)
            ch = self.bot.missile.bottyland
            await ch.send(
                f'Welcome {member.mention}! You are automatically added to the role {role.name} for related announcements.'
                f' If you wish to unsubscribe, please send `?rank {role.name}` in {ch.mention}.'
            )
