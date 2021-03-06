import base64
import random
import re
from random import randint

import discord
from discord.ext.commands import Cog, Context, command, has_any_role, group, cooldown, BucketType, Bot

from dimsecret import debug
from missile import Missile

max_pp_size = 69
guild_id = 675477913411518485
spam_ch_id = 723153902454964224


def convert(text: str) -> str:
    b: bytes = text.encode()
    encoded: bytes = base64.b64encode(b)
    return encoded.decode()


class BitBay(Cog):
    """Utilities for 128BB
    Version 1.3"""

    def __init__(self, bot):
        self.bot: Bot = bot
        self.organs: dict = {}
        self.xp: dict = {}
        self.mpm = True

    def get_size(self, uid: int) -> int:
        if uid in self.organs.keys():
            return self.organs[uid]
        return -1

    def draw_pp(self, size: int) -> str:
        if size == -1:
            return f"No pp found. Have you set it up by {self.bot.default_prefix}pp?"
        description = f'8{"=" * size}D'
        if size == max_pp_size:
            description += '\n**MAX POWER**'
        return description

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.guild and msg.guild.id == 675477913411518485 and self.mpm:
            if re.search(r".*(get|download|find|obtain|acquire).*(cemu|wii ?u) (rom|game)s?", msg.content,
                         re.IGNORECASE):
                await msg.reply("Please use the last link in the oldest pin in <#718989936837263450>")
            elif re.search(r".*(get|download|find|obtain|acquire).*(switch|yuzu|ryu) (rom|game)s?", msg.content,
                           re.IGNORECASE):
                await msg.reply("<#730596209701421076>")
            elif re.search(
                    r".*(get|download|find|obtain|acquire).*((shader.*(switch|yuzu|ryu))|((switch|yuzu|ryu).*shader))",
                    msg.content, re.IGNORECASE):
                await msg.reply("<#709944999399260190>")

    @command(aliases=['enc'])
    async def encode(self, ctx: Context, *, url: str):
        if ctx.channel.type == discord.ChannelType.text:
            await ctx.message.delete()
        if Missile.regex_is_url(url):
            await ctx.send(f'<https://codebeautify.org/base64-decode?input={convert(url)}>')
        else:
            url = ctx.author.mention + ': ' + url
            await ctx.send(convert(url))

    @command()
    @has_any_role(702608566845964338, 735911149681508383, 702889819570831572)
    async def mpm(self, ctx: Context):
        await ctx.reply(('Disabled' if self.mpm else 'Enabled') + ' Message Pattern Matching (MPM)')
        self.mpm = not self.mpm

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
    @has_any_role(702608566845964338, 702889819570831572, 720319730883362816)
    async def ea(self, ctx: Context, build: int, url: str):
        msg = f'<@&719572310129901710>\n\nYuzu Early Access {build}\n\nDownload:\n' \
              f'<https://codebeautify.org/base64-decode?input={convert(url)}>'
        if debug:
            await ctx.send(msg)
            return
        await self.bot.get_channel(702714661912707072).send(msg)

    @group(invoke_without_command=True)
    async def pp(self, ctx: Context, user: discord.User = None):
        """
        Wiki for the d.pp commands: https://github.com/TCLRainbow/DimBot/wiki/pp
        """
        user = user if user else ctx.author
        size = randint(0, max_pp_size)
        self.organs[user.id] = size
        await ctx.send(embed=discord.Embed(title=user.display_name + "'s penis", description=self.draw_pp(size),
                                           colour=Missile.random_rgb()))

    @pp.command()
    async def size(self, ctx: Context, user: discord.User = None):
        user = user if user else ctx.author
        size = self.get_size(user.id)
        if size == -1:
            await ctx.send(self.draw_pp(size))
            return
        await ctx.send('pp size: ' + str(size))

    @pp.command()
    async def slap(self, ctx: Context, user: discord.User):
        size = self.get_size(ctx.author.id)
        if size == -1:
            await ctx.send(self.draw_pp(size))
            return
        emb = discord.Embed(description=self.draw_pp(self.get_size(ctx.author.id)), colour=Missile.random_rgb())
        emb.set_thumbnail(url=user.avatar_url)
        await ctx.send(embed=emb)

    @pp.command()
    @Missile.is_rainbow_cmd_check()
    async def max(self, ctx: Context):
        self.organs[ctx.author.id] = max_pp_size
        await ctx.send(embed=discord.Embed(title=ctx.author.display_name + "'s penis",
                                           description=self.draw_pp(max_pp_size),
                                           colour=Missile.random_rgb()))

    @pp.command()
    async def min(self, ctx: Context):
        self.organs[ctx.author.id] = 0
        await ctx.send(embed=discord.Embed(title=ctx.author.display_name + "'s penis", description='8D',
                                           colour=Missile.random_rgb()))

    @pp.command()
    async def cut(self, ctx: Context):
        size = self.get_size(ctx.author.id)
        if size == -1:
            await ctx.send(self.draw_pp(size))
            return
        self.organs.pop(ctx.author.id)
        await ctx.send(embed=discord.Embed(title=ctx.author.display_name + "'s penis",
                                           description=f"8\n{'=' * size}D", colour=discord.Colour.red()))

    @pp.command(aliases=['sf'])
    @cooldown(rate=1, per=10.0, type=BucketType.user)
    async def swordfight(self, ctx: Context, user: discord.User = None):
        if not user:
            if not len(self.organs.keys()):
                await ctx.reply(f'No one has pp. Either `{self.bot.default_prefix}pp` yourself or any members first,'
                                f' or `{self.bot.default_prefix}pp sf @anyone`')
                return
            user = self.bot.get_user(random.choice(list(self.organs.keys())))
        me = self.get_size(ctx.author.id)
        him = self.get_size(user.id)
        if me > him:
            title = "VICTORY"
        elif me == him:
            title = "TIE"
        else:
            title = "LOST"
        xp = 0 if him == -1 else me - him
        if ctx.author.id not in self.xp:
            self.xp[ctx.author.id] = 0
        self.xp[ctx.author.id] += xp
        await ctx.send(
            embed=discord.Embed(title=title, description=f"**{ctx.author.name}'s penis:**\n{self.draw_pp(me)}\n"
                                                         f"**{user.name}'s penis:**\n{self.draw_pp(him)}\n\n"
                                                         f"You gained **{xp}** score!",
                                colour=Missile.random_rgb()))

    @pp.command()
    async def lb(self, ctx: Context):
        v = dict(sorted(self.xp.items(), key=lambda item: item[1], reverse=True))
        base = 'pp score leaderboard:\n'
        for key in v.keys():
            base += f"{self.bot.get_user(key).name}: **{v[key]}** "
        await ctx.reply(base)
