import discord
from discord.ext.commands import Cog

from missile import Missile


class Aegis(Cog):
    """AutoMod"""

    def __init__(self, bot):
        self.bot = bot

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        if len(msg.raw_mentions) > 5:
            aegis_msg = await msg.channel.send(f'**Aegis**: Detected mass ping ({len(msg.raw_mentions)})')
            if msg.author.top_role >= msg.guild.me.top_role or Missile.is_rainbow(msg.author.id):
                await Missile.append_message(aegis_msg, 'Cannot lock target.')
                return
            await msg.author.ban(reason=f'Aegis: Mass ping from {msg.author}')
            await msg.channel.send('Banned ' + msg.author.mention)
