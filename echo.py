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

    def get_quote(self, index: int):
        self.cursor.execute("SELECT * FROM quotes WHERE ROWID = ?", str(index))
        return self.cursor.fetchone()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx):
        await ctx.send("Wiki for interacting with quote database: https://github.com/TCLRainbow/DimBot/wiki/Project-Echo")

    @quote.command(aliases=['i'])
    async def index(self, ctx, index: int = 0):
        self.cursor.execute("SELECT COUNT(msg) FROM quotes")
        count = self.cursor.fetchone()[0]
        content = ''
        if index < 1 or index > count:
            index = random.randint(1, count)
            content += f'There are **{count}** quotes in the database. This is a random one:\n'
        quote = self.get_quote(index)
        content += f"Quote #{index}:\n> {quote[0]} - {quote[1]}\n Uploaded by {self.bot.get_user(quote[2])}"
        await ctx.send(content)

    @quote.command(aliases=['a'])
    async def add(self, ctx, *, args):
        await ctx.send('Quoter?')

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.channel

        msg = await self.bot.wait_for('message', timeout=10, check=check)
        if msg:
            self.cursor.execute("INSERT INTO quotes VALUES (?, ?, ?)", (args, msg.content, ctx.author.id))
            self.db.commit()
            await ctx.send(f"Added quote #{self.cursor.lastrowid}")

    @quote.command(aliases=['d', 'del'])
    async def delete(self, ctx, index: int):
        quote = self.get_quote(index)
        if quote:
            if quote[2] == ctx.author.id:
                self.cursor.execute("DELETE FROM quotes WHERE ROWID = ?", str(index))
                self.db.commit()
                await ctx.send("Deleted quote.")
            else:
                await ctx.send("You must be the quote uploader to delete the quote!")
        else:
            await ctx.send('No quote found!')

