import random
import sqlite3
from datetime import datetime

import discord
from discord.ext import commands

__version__ = '1.2'

from missile import Missile


# TODO: instead of hardcoded queries like execute('DELETE FROM'), use object oriented approaches like table.delete()
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

    # TODO: Use this function for Ricciardo after NEA
    def exists(self, table: str, args: dict) -> bool:
        base = f"SELECT EXISTS(SELECT 1 FROM {table} WHERE {' AND '.join([f'{key} = ?' for key in args.keys()])}"
        return self.cursor.execute(base, args.values()).fetchone()[0]

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx):
        """
        Wiki for interacting with quote database: https://github.com/TCLRainbow/DimBot/wiki/Project-Echo
        """
        pass

    @quote.command(aliases=['i'])
    async def index(self, ctx, index: int = 0):
        quote = self.get_quote(index)
        content = ''
        if not quote:
            count = self.cursor.execute('SELECT MAX(ROWID) FROM Quote').fetchone()[0]
            content = f'That quote ID is invalid. There are **{count}** quotes in the database. This is a random one:\n'
            while not quote:
                index = random.randint(1, count)
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
        user = user if user else ctx.author
        self.cursor.execute("SELECT ROWID, msg, quoter FROM Quote WHERE uid = ?", (user.id,))
        quotes = self.cursor.fetchall()
        content = f"The following are quotes uploaded by **{user}**:\n"
        for quote in quotes:
            content += f'> {quote[0]}. {quote[1]} - {quote[2]}\n'
        await ctx.send(content)

    @quote.command()
    @Missile.is_rainbow_cmd_check()
    async def exe(self, ctx, *, msg: str):
        try:
            tic = datetime.now()
            rows = self.db.execute(msg)
            result = rows.fetchall()
            toc = datetime.now()
            await ctx.send(f"{result}\n{rows.rowcount} row affected in {(toc - tic).total_seconds()*1000}ms")
        except sqlite3.Error as e:
            await ctx.send(f"**{e.__class__.__name__}**: {e}")

    @quote.command()
    @Missile.is_rainbow_cmd_check()
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
                rowid = self.cursor.execute('SELECT id FROM QuoteRowID LIMIT 1').fetchone()
                if rowid:
                    self.cursor.execute("INSERT INTO Quote(ROWID, msg, quoter, uid) VALUES (?, ?, ?, ?)",
                                        (rowid[0], args, quoter, ctx.author.id))
                    self.cursor.execute("DELETE FROM QuoteRowID WHERE id = ?", (rowid[0], ))
                else:
                    self.cursor.execute("INSERT INTO Quote VALUES (?, ?, ?)", (args, quoter, ctx.author.id))
                await ctx.send(f"Added quote #{self.cursor.lastrowid}")

    @quote.command(aliases=['d', 'del'])
    async def delete(self, ctx, index: int):
        quote = self.get_quote(index)
        if quote:
            if quote['uid'] == ctx.author.id or Missile.is_rainbow(ctx):
                q = f"> {quote['msg']}\nYou sure you want to delete this? React ✅ to confirm"
                q = await ctx.send(q)
                await q.add_reaction('✅')

                def check(reaction, user):
                    return user == ctx.author and str(reaction.emoji) == '✅'

                await self.bot.wait_for('reaction_add', timeout=10, check=check)
                self.cursor.execute("DELETE FROM Quote WHERE ROWID = ?", (index,))
                self.cursor.execute("INSERT INTO QuoteRowID VALUES (?)", (index,))
                await ctx.send('Deleted quote.')
            else:
                await ctx.send("You must be the quote uploader to delete the quote!")
        else:
            await ctx.send('No quote found!')

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        ch_ids = [ch.id for ch in guild.text_channels]
        q_marks = ','.join(['?']*len(ch_ids))
        self.cursor.execute(f"DELETE FROM BbmRole WHERE bbmChID IN ({q_marks})", (ch_ids,))
        self.cursor.execute(f"DELETE FROM BbmAddon WHERE bbmChID IN ({q_marks})", (ch_ids,))
        self.cursor.execute(f"DELETE FROM RssSub WHERE rssChID IN ({q_marks})", (ch_ids,))
        self.cursor.execute(f"DELETE FROM RssData WHERE url NOT IN (SELECT url FROM RssSub)")
        self.cursor.execute(f"DELETE FROM YtSub WHERE ytChID IN ({q_marks})", (ch_ids,))
        self.cursor.execute("DELETE FROM YtData WHERE channelID NOT IN (SELECT channelID FROM YtSub)")
