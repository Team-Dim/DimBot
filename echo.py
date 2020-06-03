import random
import sqlite3

import discord
from discord.ext import commands

__version__ = '1.0.4'

from bruckserver import vireg


class Echo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Echo')
        self.db = sqlite3.connect('DimBot.db')
        self.cursor = self.db.cursor()

    def get_quote(self, index: int):
        self.cursor.execute("SELECT * FROM quotes WHERE ROWID = ?", (index,))
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

    @quote.command(aliases=['q'])
    async def quoter(self, ctx, *, quoter):
        self.cursor.execute("SELECT ROWID, msg FROM quotes WHERE quoter = ?", (quoter,))
        quotes = self.cursor.fetchall()
        content = f"The following are **{quoter}**'s quotes:\n"
        for quote in quotes:
            content += f'> {quote[0]}. {quote[1]}\n'
        await ctx.send(content)

    @quote.command(aliases=['u'])
    async def uploader(self, ctx, user: discord.User):
        self.cursor.execute("SELECT ROWID, msg, quoter FROM quotes WHERE uid = ?", (user.id,))
        quotes = self.cursor.fetchall()
        content = f"The following are quotes uploaded by **{user}**:\n"
        for quote in quotes:
            content += f'> {quote[0]}. {quote[1]} - {quote[2]}\n'
        await ctx.send(content)

    @quote.command()
    @commands.check(vireg.is_rainbow)
    async def exe(self, ctx):
        await ctx.send('SQL statement?')

        def check(m):
            return m.author.id == ctx.author.id and m.channel == ctx.channel

        msg = await self.bot.wait_for('message', check=check)
        self.cursor.execute(msg.content)
        self.db.commit()
        await ctx.send('Done')

    @quote.command(aliases=['a'])
    async def add(self, ctx, *, args):
        if '<@' in args:
            await ctx.send("You can't mention others in quote message!")
            return
        self.cursor.execute("SELECT ROWID FROM quotes WHERE msg = ?", (args, ))
        exists = self.cursor.fetchone()
        if exists:
            await ctx.send(f'This quote duplicates with #{exists[0]}')
        else:
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
                self.cursor.execute("DELETE FROM quotes WHERE ROWID = ?", (index,))
                self.db.commit()
                await ctx.send("Deleted quote.")
            else:
                await ctx.send("You must be the quote uploader to delete the quote!")
        else:
            await ctx.send('No quote found!')
