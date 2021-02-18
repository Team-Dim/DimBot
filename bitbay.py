import base64
from random import randint

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
        self.organs: dict = {}

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
        import binascii
        try:
            b: bytes = content.encode()
            decoded: bytes = base64.b64decode(b)
            await ctx.author.send(decoded.decode())
            await ctx.message.add_reaction('✅')
        except (UnicodeDecodeError, binascii.Error):
            await ctx.send('Malformed base64 string.')

    @command()
    @has_any_role(702889819570831572, 720319730883362816)
    async def ea(self, ctx: Context, build: int, url: str):
        msg = f'<@&719572310129901710>\n\nYuzu Early Access {build}\n\nDownload:\n' \
              f'<https://codebeautify.org/base64-decode?input={convert(url)}>'
        if debug:
            await ctx.send(msg)
        else:
            await self.bot.get_channel(702714661912707072).send(msg)

    @command()
    async def pp(self, ctx: Context, user: discord.User = None):
        user = user if user else ctx.author
        size = randint(0, 69)
        self.organs[user.id] = size
        await ctx.send(embed=discord.Embed(title=user.display_name + "'s penis",
                                           description=f'8{"="*size}D',
                                           colour=discord.Colour.from_rgb(randint(0, 255), randint(0, 255),
                                                                          randint(0, 255))))

    @command(aliases=['sf'])
    async def swordfight(self, ctx: Context, user: discord.User):
        def get_size(uid: int) -> int:
            if uid not in self.organs.keys():
                return 0
            return self.organs[uid]
        me = get_size(ctx.author.id)
        him = get_size(user.id)
        if me > him:
            title = "VICTORY"
        elif me == him:
            title = "TIE"
        else:
            title = "LOSE"
        await ctx.send(embed=discord.Embed(title=title, description=f"{ctx.author.name}'s penis:\n8{'='*me}D\n"
                                                                    f"{user.name}'s penis:\n8{'='*him}D",
                                           colour=discord.Colour.from_rgb(randint(0, 255), randint(0, 255),
                                                                          randint(0, 255))))
