import random

import discord
from discord.ext import commands

import missile


# TODO: instead of hardcoded queries like execute('DELETE FROM'), use object oriented approaches like table.delete()
class Bottas(commands.Cog):
    """Storing messages.
    Version 2.1"""

    def __init__(self, bot):
        self.bot = bot

    def get_quote(self, index: int):
        """Gets a quote from the db via ROWID"""
        self.bot.cursor.execute("SELECT * FROM Quote WHERE ROWID = ?", (index,))
        return self.bot.cursor.fetchone()

    # TODO: Use this function for Ricciardo after NEA
    def exists(self, table: str, args: dict) -> bool:
        base = f"SELECT EXISTS(SELECT 1 FROM {table} WHERE {' AND '.join([f'{key} = ?' for key in args.keys()])}"
        return self.bot.cursor.execute(base, args.values()).fetchone()[0]

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx):
        """
        Wiki for interacting with quote database: https://github.com/TCLRainbow/DimBot/wiki/Project-Echo
        """
        raise commands.errors.CommandNotFound

    @quote.command(aliases=('i',))
    async def index(self, ctx, index: int = 0):
        """Search a quote by its ID"""
        quote = self.get_quote(index)
        content = ''
        if not quote:  # Provided Quote ID is invalid
            count = self.bot.cursor.execute('SELECT COUNT(ROWID) FROM Quote').fetchone()[0]
            content = f'That quote ID is invalid. There are **{count}** quotes in the database. This is a random one:\n'
            while not quote:  # Randomly generates a valid quote
                index = random.randint(1, count)
                quote = self.get_quote(index)
        user = self.bot.get_user(quote[2])
        if not user:  # Ensures that user is not None
            user = await self.bot.fetch_user(quote[2])
        content += f"Quote #{index}:\n> {quote[0]} - {quote[1]}\n Uploaded by {user}"
        await ctx.send(content)

    @quote.command(aliases=('q',))
    async def quoter(self, ctx, *, quoter):
        """List quotes that are said by a quoter"""
        self.bot.cursor.execute("SELECT ROWID, msg FROM Quote WHERE quoter = ?", (quoter,))
        quotes = self.bot.cursor.fetchall()
        content = f"The following are **{quoter}**'s quotes:\n"
        for quote in quotes:
            content += f'> {quote[0]}. {quote[1]}\n'
        await ctx.send(content)

    @quote.command(aliases=['u'])
    async def uploader(self, ctx, user: discord.User = None):
        """List quotes that are uploaded by a Discord user"""
        user = user if user else ctx.author
        self.bot.cursor.execute("SELECT ROWID, msg, quoter FROM Quote WHERE uid = ?", (user.id,))
        quotes = self.bot.cursor.fetchall()
        content = f"The following are quotes uploaded by **{user}**:"
        for quote in quotes:
            to_be_added = f'\n> {quote[0]}. {quote[1]} - {quote[2]}'
            if len(content + to_be_added) >= 2000:
                break
            content += to_be_added
        await ctx.send(content)

    @quote.command(name='add', aliases=['a'])
    async def quote_add(self, ctx, *, args):
        """Adds a quote"""
        # Quote message validation
        if '<@' in args:
            await ctx.send("You can't mention others in quote message!")
            return
        if '\n' in args:
            await ctx.send("The quote should be only one line!")
            return
        # Check if a quote with the same content already exists in the database
        self.bot.cursor.execute("SELECT ROWID FROM Quote WHERE msg = ?", (args,))
        exists = self.bot.cursor.fetchone()
        if exists:
            await ctx.send(f'This quote duplicates with #{exists[0]}')
        else:
            # Asks for the quoter who said the quote
            quoter = await self.bot.ask_msg(ctx, 'Quoter?')
            if quoter:
                # Quote message validation
                if '<@' in quoter:
                    await ctx.send("You can't mention others in quote message!")
                    return
                if '\n' in quoter:
                    await ctx.send("The quote should be only one line!")
                    return

                # Determines the ROWID to be used for inserting the quote
                rowid = self.bot.cursor.execute('SELECT id FROM QuoteRowID LIMIT 1').fetchone()
                if rowid:  # Use ROWID from QuoteRowID if available. These IDs exist when a quote was deleted
                    self.bot.cursor.execute("INSERT INTO Quote(ROWID, msg, quoter, uid) VALUES (?, ?, ?, ?)",
                                            (rowid[0], args, quoter, ctx.author.id))
                    self.bot.cursor.execute("DELETE FROM QuoteRowID WHERE id = ?", (rowid[0],))
                else:  # Normal insertion, using a fresh ROWID
                    self.bot.cursor.execute("INSERT INTO Quote VALUES (?, ?, ?)", (args, quoter, ctx.author.id))
                await ctx.send(f"Added quote #{self.bot.cursor.lastrowid}")

    @quote.command(name='delete', aliases=['d'])
    async def quote_delete(self, ctx, index: int):
        """Deletes a quote by its quote ID"""
        quote = self.get_quote(index)  # Checks if the quote exists
        if quote:
            # Check if sender is quote uploader or sender is me (db admin)
            if quote['uid'] == ctx.author.id or ctx.author.id == self.bot.owner_id:
                # Confirmation
                if await self.bot.ask_reaction(ctx, f"> {quote['msg']}\n"
                                                    f"You sure you want to delete this? React ✅ to confirm"):
                    # Delete
                    self.bot.cursor.execute("DELETE FROM Quote WHERE ROWID = ?", (index,))
                    self.bot.cursor.execute("INSERT INTO QuoteRowID VALUES (?)", (index,))
                    await ctx.send('Deleted quote.')
            else:
                await ctx.send("You must be the quote uploader to delete the quote!")
        else:
            await ctx.send('No quote found!')

    @quote.command(aliases=['m'])
    async def message(self, ctx: commands.Context, *, search):
        """Search quotes by keywords"""
        quotes = self.bot.cursor.execute("SELECT ROWID, msg, quoter FROM Quote WHERE msg like ?",
                                         ('%' + search + '%',)).fetchall()
        base = f'The following quotes contains **{search}**:'
        for q in quotes:
            base += f"\n> {q['ROWID']}. {q['msg']} - {q['quoter']}"
        await ctx.send(base)

    @quote.command(aliases=['e'])
    async def edit(self, ctx: commands.Context, index: int):
        """Edits a quote"""
        quote = self.get_quote(index)
        if quote and (quote['uid'] == ctx.author.id or ctx.author.id == self.bot.owner_id):
            content = await self.bot.ask_msg(ctx, 'Enter the new quote: (wait 10 seconds to cancel)')
            if content:
                # Quote message validation
                if '<@' in content:
                    await ctx.send("You can't mention others in quote message!")
                    return
                if '\n' in content:
                    await ctx.send("The quote should be only one line!")
                    return
                quoter = await self.bot.ask_msg(ctx, "Enter new quoter: (wait 10 seconds if it is the same)")
                if quoter:
                    # Quote message validation
                    if '<@' in quoter:
                        await ctx.send("You can't mention others in quote message!")
                        return
                    if '\n' in quoter:
                        await ctx.send("The quote should be only one line!")
                        return
                    self.bot.cursor.execute("UPDATE Quote SET msg = ?, quoter = ? WHERE ROWID = ?",
                                            (content, quoter, index))
                else:
                    self.bot.cursor.execute("UPDATE Quote SET msg = ? WHERE ROWID = ?", (content, index))
                await ctx.reply('Quote updated')
        else:
            await ctx.reply("You can't edit this quote!")

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx: commands.Context, name: str = ''):
        """Commands related to tags. If a subcommand is provided, d.tag runs the subcommand. If the provided argument
        is not a subcommand, d.tag shows the content of the provided tag. If no arguments are provided, d.tag lists all
        tags within the server."""
        if name:
            await self.bot.get_command('tag s')(ctx, name)
        else:
            tags = self.bot.cursor.execute("SELECT name FROM Tag WHERE guildID = ? ORDER BY name",
                                           (ctx.guild.id,)).fetchall()
            await ctx.reply(f"`{', '.join((tag[0] for tag in tags))}`")

    @tag.command(aliases=['s'])
    async def show(self, ctx: commands.Context, name: str):
        """Shows a tag"""
        tag = self.bot.cursor.execute("SELECT content FROM Tag WHERE name = ? AND guildID = ?",
                                      (name, ctx.guild.id)).fetchone()
        if tag:
            await ctx.reply(tag[0])
        else:
            await ctx.reply(f"Tag `{name}` not found.")

    @tag.command(name='add', aliases=['a'])
    @commands.has_permissions(manage_messages=True)
    async def tag_add(self, ctx: commands.Context, name: str, url: str):
        """Adds a tag."""
        if not missile.is_url(url):
            await ctx.reply('Tag content must be a HTTP WWW link!')
            return
        if self.bot.cursor.execute("SElECT EXISTS(SELECT 1 FROM Tag WHERE (name = ? OR content = ?) AND guildID = ?)",
                                   (name, url, ctx.guild.id)).fetchone()[0]:
            await ctx.reply('A tag with the same name/link already exists!')
            return
        if '<@' in name:
            await ctx.reply('Why are you mentioning people in tag names?')
            return
        self.bot.cursor.execute("INSERT INTO Tag VALUES (?, ?, ?)", (name, url, ctx.guild.id))
        await ctx.reply('Your tag has been created!')

    @tag.command(name='delete', aliases=['d'])
    @commands.has_permissions(manage_messages=True)
    async def tag_delete(self, ctx: commands.Context, name: str):
        """Deletes a tag"""
        if self.bot.cursor.execute("SELECT EXISTS(SELECT 1 FROM Tag WHERE name = ? AND guildID = ?)",
                                   (name, ctx.guild.id)).fetchone()[0]:
            self.bot.cursor.execute("DELETE FROM Tag WHERE name = ? AND guildID = ?", (name, ctx.guild.id))
            await ctx.reply('Deleted tag.')
        else:
            await ctx.reply(f"Tag `{name}` not found.")
