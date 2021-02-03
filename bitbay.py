import base64

import discord

__version__ = '1.0'

from discord.ext.commands import Cog, Context, command


class BitBay(Cog):

    def __init__(self, bot):
        self.bot: discord.Client = bot

    @command(aliases=['enc'])
    async def encode(self, ctx: Context, *, url: str):
        await ctx.message.delete()
        if not url.lower().startswith('http'):
            url = ctx.author.mention + ': ' + url
        b: bytes = url.encode()
        encoded: bytes = base64.b64encode(b)
        await ctx.send(encoded.decode())

    @command(aliases=['dec'])
    async def decode(self, ctx: Context, content: str):
        b: bytes = content.encode()
        decoded: bytes = base64.b64decode(b)
        await ctx.author.send(decoded.decode())
        await ctx.message.add_reaction('✅')
