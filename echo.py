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
    async def quote(self, ctx):
        await ctx.send("Wiki for interacting with quote databse: https://github.com/TCLRainbow/DimBot/wiki/Project-Echo")

    @quote.command()
    async def patch(self, ctx):
        self.db.execute("ALTER TABLE quotes ADD COLUMN uid INTEGER")

    @quote.command()
    async def index(self, ctx, index: int = 0):
        self.cursor.execute("SELECT COUNT(msg) FROM quotes")
        count = self.cursor.fetchone()[0]
        content = ''
        if index < 1 or index > count:
            index = random.randint(1, count)
            content += f'There are **{count}** quotes in the database. This is a random one:\n'
        self.cursor.execute("SELECT * FROM quotes WHERE ROWID = ?", str(index))
        quote = self.cursor.fetchone()
        content += f"Quote #{index}:\n> {quote[0]}\n- {quote[1]}"
        await ctx.send(content)

    @quote.command()
    async def add(self, ctx, *, args):
        await ctx.send('Quoter?')

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.channel

        msg = await self.bot.wait_for('message', timeout=10, check=check)
        if msg:
            self.cursor.execute("INSERT INTO quotes VALUES (?, ?, ?)", (args, msg.content, ctx.author.id))
            self.db.commit()
            await ctx.send(f"Added quote #{self.cursor.lastrowid}")
