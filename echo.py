import random
import sqlite3

from discord.ext import commands

__version__ = '0'


class Echo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Echo')
        self.db = sqlite3.connect('DimBot.db')
        self.cursor = self.db.cursor()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx, index: int = 0):
        if index == 0:
            self.cursor.execute("SELECT COUNT(msg) FROM quotes")
            index = random.randint(1, self.cursor.fetchone()[0])
        self.cursor.execute("SELECT * FROM quotes WHERE ROWID = ?", str(index))
        quote = self.cursor.fetchone()
        if quote:
            await ctx.send(f"> {quote[0]}\n- {quote[1]}")
        else:
            await ctx.send('No quote found!')

    @quote.command()
    async def init(self, ctx):
        self.cursor.execute("CREATE TABLE quotes (msg text, quoter text)")
        self.db.commit()

    @quote.command()
    async def add(self, ctx, *, args):
        await ctx.send('Quoter?')

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.channel

        msg = await self.bot.wait_for('message', timeout=10, check=check)
        if msg:
            self.cursor.execute("INSERT INTO quotes VALUES (?, ?)", (args, msg.content))
            self.db.commit()
            await ctx.send(f"Added quote #{self.cursor.lastrowid}")
