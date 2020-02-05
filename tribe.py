from discord.ext.commands import Bot, Cog


class Tribe(Cog):
    def __init__(self, bot: Bot):
        self.bot = bot

    @Cog.listener()
    async def on_ready(self):
        print('cog ready')
