import discord
from discord.ext.commands import Cog


class Tribe(Cog):
    """
    :param self.invites List[]
    """

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Tribe')
        self.bbm_invite: int = 0
        self.invites = None

    async def get_invite_used(self):
        invites = await self.bot.missile.guild.invites()
        # invite = next(

    async def get_invite_uses(self, code: str):
        invites = await self.bot.missile.guild.invites()
        return next(x for x in invites if x.code == code).uses

    async def notify_role_added(self, member: discord.Member, role: discord.Role):
        ch = self.bot.missile.bottyland
        await ch.send(
            f'Welcome {member.mention}! You are automatically added to the role {role.name} for related announcements.'
            f' If you wish to unsubscribe, please send `?rank {role.name}` in {ch.mention}.'
        )

    @Cog.listener()
    async def on_ready(self):
        self.logger.debug('on ready')
        self.invites = await self.bot.missile.guild.invites()
        self.bbm_invite = await self.get_invite_uses('g6Yrteq')

    @Cog.listener()
    async def on_member_join(self, member):
        count = await self.get_invite_uses('g6Yrteq')
        if count != self.bbm_invite:
            self.logger.info(f'{member.name}({member.id}) joined via BBM invite.')
            role = self.bot.missile.guild.get_role(664210105318768661)
            await member.add_roles(role)
            self.logger.debug(f'Added to role {role.name}')
            await self.notify_role_added(member, role)
            self.bbm_invite = count
