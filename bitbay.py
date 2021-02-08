import base64

import discord

__version__ = '1.1.1'

from discord.ext.commands import Cog, Context, command, has_any_role

from dimsecret import debug


def convert(text: str):
    b: bytes = text.encode()
    encoded: bytes = base64.b64encode(b)
    return encoded.decode()


class BitBay(Cog):

    def __init__(self, bot):
        self.bot: discord.Client = bot

    @command(aliases=['enc'])
    async def encode(self, ctx: Context, *, url: str):
        if isinstance(ctx.channel, discord.TextChannel):
            await ctx.message.delete()
        if url.lower().startswith('http'):
            await ctx.send(f'<https://codebeautify.org/base64-decode?input={convert(url)}>')
        else:
            url = ctx.author.mention + ': ' + url
            await ctx.send(convert(url))

    @command(aliases=['dec'])
    async def decode(self, ctx: Context, content: str):
        b: bytes = content.encode()
        import binascii
        try:
            decoded: bytes = base64.b64decode(b)
            await ctx.author.send(decoded.decode())
            await ctx.message.add_reaction('✅')
        except UnicodeDecodeError or binascii.Error:
            await ctx.send('Malformed base64 string.')

    @command()
    @has_any_role(702889819570831572, 720319730883362816)
    async def ea(self, ctx: Context, build: int, url: str):
        msg = f'<@&719572310129901710>\n\nYuzu Early Access {build}\n\nMediafire:\n' \
              f'<https://codebeautify.org/base64-decode?input={convert(url)}>'
        if debug:
            await ctx.send(msg)
        else:
            await self.bot.get_channel(702714661912707072).send(msg)
