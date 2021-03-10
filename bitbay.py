import base64
import random
import re
from random import randint
from typing import Optional

import discord
from discord.ext.commands import Cog, Context, command, has_any_role, group, cooldown, BucketType, Bot

from dimsecret import debug
from missile import Missile

max_pp_size = 69
guild_id = 675477913411518485
spam_ch_id = 723153902454964224


def convert(text: str) -> str:
    """Converts the given string to base64"""
    b: bytes = text.encode()
    encoded: bytes = base64.b64encode(b)
    return encoded.decode()


class PP:

    def __init__(self, size: int, viagra: bool):
        self.size: int = size
        self.viagra_available: bool = viagra
        self.viagra_rounds: int = 0
        self.score = 0


class BitBay(Cog):
    """Utilities for 128BB
    Version 1.3.1"""

    def __init__(self, bot):
        self.bot: Bot = bot
        self.organs: dict = {}  # Dict for storing pp size
        self.mpm = True  # Message Pattern Matching master switch
        self.no_pp_msg = f"No pp found. Have you set it up by {bot.default_prefix}pp?"

    def get_pp(self, uid: int) -> Optional[PP]:
        """Gets the pp of a User"""
        if uid in self.organs.keys():
            return self.organs[uid]
        return None

    def ensure_size(self, uid: int) -> int:
        """Ensures a value when getting pp size. If user has no pp, returns -1"""
        pp = self.get_pp(uid)
        if pp:
            return pp.size
        return -1

    def draw_pp(self, uid: int) -> str:
        """Returns the string for displaying pp"""
        pp = self.get_pp(uid)
        if pp:
            description = f'8{"=" * pp.size}D'
            if pp.viagra_rounds:
                description = f'**{description}**\nViagra rounds left: {pp.viagra_rounds}'
            elif pp.viagra_available:
                description += '\nViagra available!'
            if pp.size == max_pp_size:
                description += '\n**MAX POWER**'
            return description
        return self.no_pp_msg

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        """Message Pattern Matching logic"""
        if msg.guild and msg.guild.id == guild_id and self.mpm:
            if re.search(r".*(get|download|find|obtain|acquire).*(cemu|wii ?u) (rom|game)s?", msg.content,
                         re.IGNORECASE):
                await msg.reply("Please use the last link in the oldest pin in <#718989936837263450>")
            elif re.search(r".*(get|download|find|obtain|acquire).*(switch|yuzu|ryu) (rom|game)s?", msg.content,
                           re.IGNORECASE):
                await msg.reply("Please use <#730596209701421076>, don't use FitGirl repacks.")
            elif re.search(
                    r".*(get|download|find|obtain|acquire).*((shader.*(switch|yuzu|ryu))|((switch|yuzu|ryu).*shader))",
                    msg.content, re.IGNORECASE):
                await msg.reply("<#709944999399260190>")

    @command(aliases=['enc'])
    async def encode(self, ctx: Context, *, url: str):
        """Encodes base64 via command"""
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
        """Toggles the Message Pattern Matching switch"""
        await ctx.reply(('Disabled' if self.mpm else 'Enabled') + ' Message Pattern Matching (MPM)')
        self.mpm = not self.mpm

    @command(aliases=['dec'])
    async def decode(self, ctx: Context, content: str):
        """Decodes base64 via command"""
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
        """Notifies EAWindows that a new Yuzu EA build is available"""
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
        # Randomises user's pp size
        user = user if user else ctx.author
        size = randint(0, max_pp_size)
        viagra = randint(0, 100) < 25
        self.organs[user.id] = PP(size, viagra)
        await ctx.send(embed=discord.Embed(title=user.display_name + "'s penis", description=self.draw_pp(user.id),
                                           colour=Missile.random_rgb()))

    @pp.command()
    async def info(self, ctx: Context, user: discord.User = None):
        """Shows the pp info"""
        user = user if user else ctx.author
        pp = self.get_pp(user.id)
        if pp:
            await ctx.send(embed=discord.Embed(title='pp size: ' + str(pp.size),
                                               description=self.draw_pp(user.id),
                                               color=Missile.random_rgb()))
        else:
            await ctx.send(self.no_pp_msg)

    @pp.command()
    async def slap(self, ctx: Context, user: discord.User):
        """Use pp to slap others"""
        if self.get_pp(ctx.author.id):
            emb = discord.Embed(description=self.draw_pp(ctx.author.id), color=Missile.random_rgb())
            emb.set_thumbnail(url=user.avatar_url)
            await ctx.send(embed=emb)
        else:
            await ctx.send(self.no_pp_msg)

    @pp.command()
    @Missile.is_rainbow_cmd_check()
    async def max(self, ctx: Context, target: discord.User = None, viagra=True):
        target = target if target else ctx.author
        self.organs[target.id] = PP(max_pp_size, viagra)
        await ctx.send(embed=discord.Embed(title=target.display_name + "'s penis",
                                           description=self.draw_pp(target.id),
                                           colour=Missile.random_rgb()))

    @pp.command()
    async def min(self, ctx: Context):
        """Minimises your pp strength"""
        self.organs[ctx.author.id] = PP(0, False)
        await ctx.send(embed=discord.Embed(title=ctx.author.display_name + "'s penis", description='8D',
                                           colour=Missile.random_rgb()))

    @pp.command()
    async def cut(self, ctx: Context):
        """Cuts your pp"""
        # Internally this removes the user from self.organs
        pp = self.get_pp(ctx.author.id)
        if pp:
            if await self.bot.missile.ask_reaction(ctx, '⚠Cutting your pp also resets your score! Are you sure?'):
                self.organs.pop(ctx.author.id)
                await ctx.send(embed=discord.Embed(title=ctx.author.display_name + "'s penis",
                                                   description=f"8\n{'=' * pp.size}D", colour=discord.Colour.red()))
        else:
            await ctx.send('You have no pp to cut!')

    @pp.command(aliases=['sf'])
    @cooldown(rate=1, per=10.0, type=BucketType.user)  # Each person can only call this once per 10s
    async def swordfight(self, ctx: Context, user: discord.User = None):
        """Use your pp as a weapon and fight"""
        if not user:  # User did not specify a target to fight
            if not self.organs:  # There is no one to fight
                await ctx.reply(f'No one has pp. Either `{self.bot.default_prefix}pp` yourself or any members first,'
                                f' or `{self.bot.default_prefix}pp sf @anyone`')
                return
            user = self.bot.get_user(random.choice(list(self.organs.keys())))
        my = self.get_pp(ctx.author.id)
        his = self.get_pp(user.id)
        if my:
            if his:
                if my.size > his.size:
                    title = "VICTORY"
                elif my.size == his.size:
                    title = "TIE"
                else:
                    title = "LOST"
                xp = my.size - his.size
                gain_msg = f"You gained **{xp}** score!"
                my.score += xp
            else:
                title = "WIN...?"  # Should not gain xp if opponent has no pp
                gain_msg = 'You gained nothing!'
        elif his:
            title = "DESTROYED"
            my.score -= his.size  # Deducts score
            gain_msg = f"You lost **{his.size}** score!"
        else:
            title = "NOTHING"
            gain_msg = 'You have nothing to lose or gain...'
        await ctx.send(
            embed=discord.Embed(title=title,
                                description=f"**{ctx.author.name}'s penis:**\n{self.draw_pp(ctx.author.id)}\n"
                                            f"**{user.name}'s penis:**\n{self.draw_pp(user.id)}\n\n{gain_msg}",
                                colour=Missile.random_rgb()))
        if my:
            if my.viagra_rounds > 0:
                my.viagra_rounds -= 1
                if my.viagra_rounds == -1:
                    await ctx.send(f"Faith effect has worn off for {ctx.author.display_name}'s pp")
                    my.size >>= 1

    @pp.command()
    async def lb(self, ctx: Context):
        """Shows the pp leaderboard"""
        v = dict(sorted(self.organs.items(), key=lambda item: item[1].score, reverse=True))  # Sort self.xp by score
        base = 'pp score leaderboard:\n'
        for key in v.keys():
            base += f"{self.bot.get_user(key).name}: **{v[key].score}** "
        await ctx.reply(base)

    @pp.command()
    async def faith(self, ctx: Context):
        """In your pp, WE TRUST"""
        pp = self.get_pp(ctx.author.id)
        if pp:
            if pp.viagra_rounds:
                await ctx.reply('You are already one with your pp! Rounds left: ' + str(pp.viagra_rounds))
            elif pp.viagra_available:
                pp.viagra_available = False
                pp.size <<= 1
                pp.viagra_rounds = 2
                await ctx.send(ctx.author.mention + " has faith in his pp!!!!! New pp size: " + str(pp.size))
            else:
                await ctx.reply('Your pp is not ready for it!')
        else:
            await ctx.reply(self.no_pp_msg)
