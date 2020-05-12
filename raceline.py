from discord.ext import commands


class Raceline(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = self.bot.missile.get_logger('Raceline')

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('on_ready')

