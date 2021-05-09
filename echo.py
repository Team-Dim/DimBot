import re

import discord
from discord.ext import commands

import missile


def split_quoter(quoter: str):
    quoter = re.split(r" *, *", quoter)
    return quoter[0], quoter[1] if len(quoter) > 1 else None


class Quote:

    def __init__(self, *args):
        self.msg = args[0]
        self.quoter = args[1]
        self.uid = args[2]
        self.quoter_group = args[3]
        self.time = args[4]


class Bottas(commands.Cog):
    """Storing messages.
    Version 3.0"""

    def __init__(self, bot):
        self.bot = bot

    @commands.group(invoke_without_command=True)
    async def quote(self, ctx):
        """
        Wiki for interacting with quote database: https://github.com/TCLRainbow/DimBot/wiki/Project-Echo
        """
        raise commands.errors.CommandNotFound

    @quote.command(aliases=('i',))
    async def index(self, ctx, index: int = 0):
        """Search a quote by its ID"""
        quote = await self.bot.sql.get_quote(self.bot.db, id=index)
        content = ''
        if not quote:  # Provided Quote ID is invalid
            count = await self.bot.sql.get_quotes_count(self.bot.db)
            quote = await self.bot.sql.get_random_quote(self.bot.db)
            index = quote[-1]
            content = f'That quote ID is invalid. There are **{count}** quotes in the database. This is a random one:\n'
        quote_obj = Quote(*quote)
        user = self.bot.get_user(quote_obj.uid)
        if not user:  # Ensures that user is not None
            try:
                user = await self.bot.fetch_user(quote_obj.uid)
            except discord.NotFound:
                user = '*unknown user*'
        content += f"Quote #{index}:\n> {quote_obj.msg} - {quote_obj.quoter}"
        if quote_obj.quoter_group:
            content += f", {quote_obj.quoter_group}"
        content += f"\n Uploaded by {user}"
        if quote_obj.time:
            content += f" at {quote_obj.time.split('.')[0]}"
        await ctx.reply(content)

    @quote.command(aliases=('q',))
    async def quoter(self, ctx, *, quoter_msg):
        """List quotes that are said by a quoter/a quoter group"""
        quoter, quoter_group = split_quoter(quoter_msg)
        quotes = await self.bot.sql.get_quoter_quotes(self.bot.db, quoter=quoter, QuoterGroup=quoter_group)
        content = f"The following are **{quoter_msg}**'s quotes:\n>>> "
        no_msg = False
        for quote in quotes:
            content += f'{quote[0]}. {quote[1]}\n'
            if len(content) >= 2048:
                no_msg = True
                break
        if no_msg:
            content = f"The following are IDs of **{quoter_msg}**'s quotes:\n"
            for quote in quotes:
                content += f'{quote[0]} '
        await ctx.reply(content)

    @quote.command(aliases=('u',))
    async def uploader(self, ctx, user: discord.User = None):
        """List quotes that are uploaded by a Discord user"""
        user = user if user else ctx.author
        quotes = await self.bot.sql.get_uploader_quotes(self.bot.db, uid=user.id)
        content = f"The following are quotes uploaded by **{user}**:\n>>> "
        no_msg = False
        for quote in quotes:
            content += f'{quote[0]}. {quote[1]} - {quote[2]}\n'
            if len(content) >= 2048:
                no_msg = True
                break
        if no_msg:
            content = f"The following are IDs of quotes uploaded by **{user}:\n"
            for quote in quotes:
                content += f'{quote[0]} '
        await ctx.send(content)

    @quote.command(name='add', aliases=('a',))
    async def quote_add(self, ctx: commands.Context, *, quote):
        """Adds a quote"""
        # Quote message validation
        await missile.check_arg(ctx, quote)
        # Check if a quote with the same content already exists in the database
        rowid = await self.bot.sql.quote_exists(self.bot.db, msg=quote)
        if rowid:
            await ctx.send(f'This quote duplicates with #{rowid}')
            return
        # Asks for the quoter who said the quote
        quoter = await self.bot.ask_msg(ctx, 'Quoter?')
        if quoter:
            # Quote message validation
            await missile.check_arg(ctx, quoter)
            quoter, quoter_group = split_quoter(quoter)
            # Determines the ROWID to be used for inserting the quote
            rowid = await self.bot.sql.get_next_row_id(self.bot.db)
            if rowid:  # Use ROWID from QuoteRowID if available. These IDs exist when a quote was deleted
                last_row_id = await self.bot.sql.add_quote_with_rowid(
                    self.bot.db, rowid=rowid, msg=quote, quoter=quoter, uid=ctx.author.id, QuoterGroup=quoter_group,
                    time=ctx.message.created_at
                )
                await self.bot.sql.delete_rowid(self.bot.db, id=rowid)
            else:  # Normal insertion, using an all new ROWID
                last_row_id = await self.bot.sql.add_quote(
                    self.bot.db, msg=quote, quoter=quoter, uid=ctx.author.id, QuoterGroup=quoter_group,
                    time=ctx.message.created_at
                )
            await ctx.send(f"Added quote #{last_row_id}")

    @quote.command(name='delete', aliases=('d',))
    async def quote_delete(self, ctx, index: int):
        """Deletes a quote by its quote ID"""
        quote = await self.bot.sql.get_quote(self.bot.db, id=index)
        if quote:  # Checks if the quote exists
            quote = Quote(*quote)
            # Check if sender is quote uploader or sender is me (db admin)
            if quote.uid == ctx.author.id or ctx.author.id == self.bot.owner_id:
                # Confirmation
                if await self.bot.ask_reaction(ctx, f"> {quote.msg}\n"
                                                    f"You sure you want to delete this? React ✅ to confirm"):
                    # Delete
                    await self.bot.sql.delete_quote(self.bot.db, id=index)
                    await self.bot.sql.add_next_rowid(self.bot.db, id=index)
                    await ctx.send('Deleted quote.')
            else:
                await ctx.send("You must be the quote uploader to delete the quote!")
        else:
            await ctx.send('No quote found!')

    @quote.command(aliases=('m',))
    async def message(self, ctx: commands.Context, *, keyword):
        """Search quotes by keywords"""
        quotes = await self.bot.sql.get_keyword_quotes(self.bot.db, kw=f'%{keyword}%')
        content = f'The following quotes contains **{keyword}**:\n>>> '
        no_msg = False
        for quote in quotes:
            q = Quote(*quote)
            content += f'{quote[-1]}. {q.msg} - {q.quoter}'
            if q.quoter_group:
                content += ', ' + q.quoter_group
            content += '\n'
            if len(content) >= 2048:
                no_msg = True
                break
        if no_msg:
            content = f"The following are IDs of quotes that contain **{keyword}**:\n"
            for quote in quotes:
                content += f'{quote[-1]} '
        await ctx.reply(content)

    @quote.command(aliases=('e',))
    async def edit(self, ctx: commands.Context, index: int):
        """Edits a quote"""
        quote = await self.bot.sql.get_quote(self.bot.db, id=index)
        if quote and (quote[2] == ctx.author.id or ctx.author.id == self.bot.owner_id):
            quote = Quote(*quote)
            content = await self.bot.ask_msg(ctx, 'Enter the new quote: (wait 10 seconds if it is the same)')
            if content:  # Quote message validation
                await missile.check_arg(ctx, content)
            else:
                content = quote.msg
            quoter = await self.bot.ask_msg(ctx, "Enter new quoter: (wait 10 seconds if it is the same)")
            if quoter:  # Quoter validation
                await missile.check_arg(ctx, quoter)
                quoter, quoter_group = split_quoter(quoter)
            else:
                quoter = quote.quoter
                quoter_group = quote.quoter_group
            await self.bot.sql.update_quote(
                self.bot.db, msg=content, quoter=quoter, QuoterGroup=quoter_group, id=index
            )
            await ctx.reply('Quote updated')
        else:
            await ctx.reply("You can't edit this quote!")

    @commands.group(invoke_without_command=True)
    async def tag(self, ctx: commands.Context, name: str = ''):
        """Commands related to tags. If a subcommand is provided, d.tag runs the subcommand. If the provided argument
        is not a subcommand, d.tag shows the content of the provided tag. If no arguments are provided, d.tag lists all
        tags within the server."""
        if name:
            content = await self.bot.sql.get_tag_content(self.bot.db, name=name, guildID=ctx.guild.id)
            if content:
                await ctx.reply(content[0])
            else:
                await ctx.reply(f"Tag `{name}` not found.")
        else:
            async with self.bot.sql.get_tags_name_cursor(self.bot.db, guildID=ctx.guild.id) as cursor:
                msg = ''
                async for row in cursor:
                    msg += row[0] + ', '
                await ctx.reply(f"`{msg[:-2]}`")

    @tag.command(name='add', aliases=['a'])
    @commands.has_permissions(manage_messages=True)
    async def tag_add(self, ctx: commands.Context, name: str, url: str):
        """Adds a tag."""
        if not missile.is_url(url):
            await ctx.reply('Tag content must be a HTTP WWW link!')
            return
        if '<@' in name:
            await ctx.reply('Why are you mentioning people in tag names?')
            return
        if await self.bot.sql.tag_exists(self.bot.db, name=name, content=url, guildID=ctx.guild.id):
            await ctx.reply('A tag with the same name/link already exists!')
            return
        await self.bot.sql.add_tag(self.bot.db, name=name, content=url, guildID=ctx.guild.id)
        await ctx.reply('Your tag has been created!')

    @tag.command(name='delete', aliases=['d'])
    @commands.has_permissions(manage_messages=True)
    async def tag_delete(self, ctx: commands.Context, name: str):
        """Deletes a tag"""
        if await self.bot.sql.tag_name_exists(self.bot.db, name=name, guildID=ctx.guild.id):
            await self.bot.sql.delete_tag(self.bot.db, name=name, guildID=ctx.guild.id)
            await ctx.reply('Deleted tag.')
        else:
            await ctx.reply(f"Tag `{name}` not found.")
