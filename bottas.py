import random
import sqlite3

import discord
from discord.ext import commands

__version__ = '1.1'

from missile import Missile


class Bottas(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Bottas')
        self.db: sqlite3.Connection = sqlite3.connect('DimBot.db', check_same_thread=False,
                                                      detect_types=sqlite3.PARSE_DECLTYPES)
        self.cursor: sqlite3.Cursor = self.get_cursor()

    def get_cursor(self) -> sqlite3.Cursor:
        cursor = self.db.cursor()
        cursor.row_factory = sqlite3.Row
        return cursor

    def get_quote(self, index: int):
        self.cursor.execute("SELECT * FROM Quote WHERE ROWID = ?", (index,))
        return self.cursor.fetchone()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx):
        await ctx.send(
            "Wiki for interacting with quote database: https://github.com/TCLRainbow/DimBot/wiki/Project-Echo")

    @quote.command(aliases=['i'])
    async def index(self, ctx, index: int = 0):
        content = ''
        if index < 1:
            count = self.cursor.execute('SELECT COUNT(msg) FROM Quote').fetchone()[0]
            if index > count:
                index = random.randint(1, count)
                content += f'There are **{count}** quotes in the database. This is a random one:\n'
        quote = self.get_quote(index)
        content += f"Quote #{index}:\n> {quote[0]} - {quote[1]}\n Uploaded by {self.bot.get_user(quote[2])}"
        await ctx.send(content)

    @quote.command(aliases=['q'])
    async def quoter(self, ctx, *, quoter):
        self.cursor.execute("SELECT ROWID, msg FROM Quote WHERE quoter = ?", (quoter,))
        quotes = self.cursor.fetchall()
        content = f"The following are **{quoter}**'s quotes:\n"
        for quote in quotes:
            content += f'> {quote[0]}. {quote[1]}\n'
        await ctx.send(content)

    @quote.command(aliases=['u'])
    async def uploader(self, ctx, user: discord.User):
        self.cursor.execute("SELECT ROWID, msg, quoter FROM Quote WHERE uid = ?", (user.id,))
        quotes = self.cursor.fetchall()
        content = f"The following are quotes uploaded by **{user}**:\n"
        for quote in quotes:
            content += f'> {quote[0]}. {quote[1]} - {quote[2]}\n'
        await ctx.send(content)

    @quote.command()
    @Missile.is_rainbow()
    async def exe(self, ctx):
        msg = await self.bot.missile.ask_msg(ctx, 'SQL statement?')
        try:
            data = self.db.execute(msg).fetchall()
            await ctx.send(data)
            await ctx.send('SQL statement successfully executed.')
        except sqlite3.Error as e:
            await ctx.send(f"**{e.__class__.__name__}**: {e}")

    @quote.command()
    @Missile.is_rainbow()
    async def save(self, ctx):
        self.db.commit()
        await ctx.send('Saved')

    @quote.command(aliases=['a'])
    async def add(self, ctx, *, args):
        if '<@' in args:
            await ctx.send("You can't mention others in quote message!")
            return
        if '\n' in args:
            await ctx.send("The quote should be only one line!")
            return
        self.cursor.execute("SELECT ROWID FROM Quote WHERE msg = ?", (args,))
        exists = self.cursor.fetchone()
        if exists:
            await ctx.send(f'This quote duplicates with #{exists[0]}')
        else:
            quoter = await self.bot.missile.ask_msg(ctx, 'Quoter?')
            if quoter:
                if '<@' in quoter:
                    await ctx.send("You can't mention others in quote message!")
                    return
                if '\n' in quoter:
                    await ctx.send("The quote should be only one line!")
                    return
                self.cursor.execute("INSERT INTO Quote VALUES (?, ?, ?)", (args, quoter, ctx.author.id))
                self.db.commit()
                await ctx.send(f"Added quote #{self.cursor.lastrowid}")

    @quote.command(aliases=['d', 'del'])
    async def delete(self, ctx, index: int):
        quote = self.get_quote(index)
        if quote:
            if quote[2] == ctx.author.id:
                self.cursor.execute("DELETE FROM Quote WHERE ROWID = ?", (index,))
                self.db.commit()
                await ctx.send("Deleted quote.")
            else:
                await ctx.send("You must be the quote uploader to delete the quote!")
        else:
            await ctx.send('No quote found!')
