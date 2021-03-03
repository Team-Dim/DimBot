import base64

import discord

__version__ = '1.2.1'

from discord.ext.commands import Cog, Context, command, has_any_role

from dimsecret import debug
from missile import Missile


def convert(text: str) -> str:
    """Converts the give string to base64"""
    b: bytes = text.encode()
    encoded: bytes = base64.b64encode(b)
    return encoded.decode()


class BitBay(Cog):

    def __init__(self, bot):
        self.bot: discord.Client = bot

    @command(aliases=['enc'])
    async def encode(self, ctx: Context, *, url: str):
        """Command for encoding a message to base64"""
        if isinstance(ctx.channel, discord.TextChannel):
            # Attempts to delete the message for privacy reasons
            await ctx.message.delete()
        if Missile.regex_is_url(url):  # Checks whether the argument is a URL
            # Allows the encoded url to be one-click decoded
            await ctx.send(f'<https://codebeautify.org/base64-decode?input={convert(url)}>')
        else:
            # The argument is not a URL. Prepend the sender's tag and encode it
            url = ctx.author.mention + ': ' + url
            await ctx.send(convert(url))

    @command(aliases=['dec'])
    async def decode(self, ctx: Context, content: str):
        """Decodes base64 via command"""
        import binascii
        try:
            b: bytes = content.encode()
            decoded: bytes = base64.b64decode(b)
            await ctx.author.send(decoded.decode())
            # Done
            await ctx.message.add_reaction('✅')
        except (UnicodeDecodeError, binascii.Error):
            # The argument is an invalid base64 string.
            await ctx.send('Malformed base64 string.')

    @command()
    # Only moderators in 128BB should be able to use this
    @has_any_role(702889819570831572, 720319730883362816)
    async def ea(self, ctx: Context, build: int, url: str):
        # Constructs the announcement that an EA build is available
        msg = f'<@&719572310129901710>\n\nYuzu Early Access {build}\n\nDownload:\n' \
              f'<https://codebeautify.org/base64-decode?input={convert(url)}>'
        if debug:
            await ctx.send(msg)  # Testing purposes
            return
        await self.bot.get_channel(702714661912707072).send(msg)  # Fire
