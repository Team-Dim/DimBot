import math

from discord.ext import menus

import missile
from sql import Quote


class WhoPing(menus.Menu):

    def __init__(self, pings, in_guild):
        super().__init__()
        self.pings: [] = pings
        self.in_guild: bool = in_guild
        self.index: int = 0

    async def get_embed(self):
        emb = missile.Embed(f'WhoPing record ({self.index + 1}/{len(self.pings)})', self.pings[self.index][2])
        user = await self.ctx.bot.ensure_user(self.pings[self.index][1])
        emb.add_field('Pinged by', user.mention)
        emb.add_field('Time', self.pings[self.index][3][5:-7])
        if not self.in_guild:
            emb.add_field('Server', self.ctx.bot.get_guild(self.pings[self.index][4]))
        emb.set_footer(text=self.pings[self.index][0])
        return emb

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=await self.get_embed())

    @menus.button('◀')
    async def on_previous(self, payload):
        if self.index:
            self.index -= 1
        else:
            self.index = len(self.pings)
        await self.message.edit(embed=await self.get_embed())

    @menus.button('▶')
    async def on_next(self, payload):
        if self.index == len(self.pings):
            self.index = 0
        else:
            self.index += 1
        await self.message.edit(embed=await self.get_embed())

    @menus.button('☑')
    async def on_read(self, payload):
        await self.bot.sql.delete_who_ping(self.bot.db, id=self.pings[self.index][0])
        del self.pings[self.index]
        if self.pings:
            await self.message.edit(embed=await self.get_embed())
        else:
            await self.message.edit(content='Nothing left.', embed=None)
            self.stop()

    @menus.button('⏹')
    async def on_stop(self, payload):
        await self.message.edit(content='WhoPing inspector ended.', embed=None)
        self.stop()


class QuotesMenu(menus.Menu):

    def __init__(self, quotes):
        super().__init__()
        self.quotes: () = quotes
        self.index: int = 0

    async def send_initial_message(self, ctx, channel):
        return await channel.send(embed=self.embed())

    def embed(self):
        emb = self.quotes[self.index].embed()
        emb.title = f'{self.index + 1}/{len(self.quotes)}'
        return emb

    @menus.button('◀')
    async def on_previous(self, payload):
        if self.index:
            self.index -= 1
        else:
            self.index = len(self.quotes)
        await self.message.edit(embed=self.embed())

    @menus.button('▶')
    async def on_next(self, payload):
        if self.index == len(self.quotes):
            self.index = 0
        else:
            self.index += 1
        await self.message.edit(embed=self.embed())


class QuoteMenu(menus.Menu):

    def __init__(self, qid, count):
        super().__init__()
        self.id: int = qid
        self.count: int = count

    async def send_initial_message(self, ctx, channel):
        quote = await ctx.bot.sql.get_quote(ctx.bot.db, id=self.id)
        return await channel.send(
            f"There are **{self.count}** quotes in the database.",
            embed=Quote(self.id, *quote).embed())

    @menus.button('◀')
    async def on_previous(self, payload):
        previous = await self.bot.sql.get_previous_quote(self.bot.db, id=self.id)
        if previous:
            previous = Quote(*previous)
            self.id = previous.id
            await self.message.edit(embed=previous.embed())

    @menus.button('▶')
    async def on_next(self, payload):
        next_quote = await self.bot.sql.get_next_quote(self.bot.db, id=self.id)
        if next_quote:
            next_quote = Quote(*next_quote)
            self.id = next_quote.id
            await self.message.edit(embed=next_quote.embed())

    @menus.button('🎲')
    async def on_random(self, payload):
        index = await self.bot.sql.get_random_id(self.bot.db)
        self.id = index[0]
        quote = Quote(self.id, *await self.bot.sql.get_quote(self.bot.db, id=self.id))
        await self.message.edit(embed=quote.embed())


class XPMenu(menus.Menu):

    def __init__(self, page):
        super().__init__()
        self.count: int = page * 10
        self.is_global: bool = True
        self.gid: int = 0

    async def send_initial_message(self, ctx, channel):
        if len(ctx.invoked_with) != 3:
            if ctx.guild:
                self.gid = ctx.guild.id
                self.is_global = False
            else:
                await ctx.reply('Server-specific leaderboard can only be viewed inside that server!')
                self.stop()
        return await ctx.reply(await self.draw())

    async def draw(self):
        if self.is_global:
            xps = await self.bot.sql.get_global_xp_leaderboard(self.bot.db, offset=self.count)
        else:
            xps = await self.bot.sql.get_xp_leaderboard(self.bot.db, guildID=self.gid, offset=self.count)
        if xps:
            content = '```c\n'
            count_pad = math.floor(math.log(self.count + 10, 10)) + 1
            xp_futures = tuple(map(lambda xp: self.bot.ensure_user(xp[0]), xps))
            for i, xp in enumerate(xps):
                content += f"Rank {str(self.count + i + 1): >{count_pad}}: {str(await xp_futures[i]):-<37} {xp[1]}\n"
            return content + '```'
        return False

    @menus.button('◀')
    async def on_previous(self, payload):
        if self.count:
            self.count -= 10
            await self.message.edit(content=await self.draw())

    @menus.button('▶')
    async def on_next(self, payload):
        self.count += 10
        content = await self.draw()
        if content:
            await self.message.edit(content=content)
        else:
            self.count -= 10
