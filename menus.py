from discord.ext import menus

import missile


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


class QuoteMenu(menus.Menu):

    def __init__(self, start: int, end: int = None):
        super().__init__()
        self.start = start
        self.end = end if end else start

    async def send_initial_message(self, ctx, channel):
        return

