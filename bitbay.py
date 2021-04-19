import base64
import random
import re
from random import randint
from typing import Optional

import discord
from discord.ext.commands import Cog, Context, command, has_any_role, group, cooldown, BucketType

import obj
from dimsecret import debug
from missile import Missile

max_pp_size = 69
guild_id = 675477913411518485
spam_ch_id = 723153902454964224
bot_ch_id = 718210372561141771


def encode(text: str) -> str:
    """Converts the given string to base64"""
    b: bytes = text.encode()
    encoded: bytes = base64.b64encode(b)
    return encoded.decode()


def decode(text: str) -> str:
    b: bytes = text.encode()
    decoded: bytes = base64.b64decode(b)
    return decoded.decode()


class PP:
    target_no_pp = 'Your opponent has no pp.'
    log = "**__Apr 18, 3:09AM GMT+1__**\n" \
          "Sesami oil: `d.pp` now has a 10% chance to generate sesami oil. It allows the holder to completely absorb " \
          "1 round of attack.\n"\
          "`d.pp zenitsu`: When you have viagra available AND sesami oil, calling this command allows you to " \
          "violently STUN your opponent for 2 rounds!"

    def __init__(self, size: int, viagra, sesami, stun=0):
        self.size: int = size
        self.viagra_available: bool = viagra
        self.viagra_rounds: int = 0
        self.score = 0
        self.sesami_oil: bool = sesami
        self.stun: int = stun


class BitBay(Cog):
    """Utilities for 128BB
    Version 1.3.3"""

    def __init__(self, bot):
        self.bot: obj.Bot = bot
        self.organs: dict = {}  # Dict for storing pp size
        self.mpm = True  # Message Pattern Matching master switch
        self.no_pp_msg = f"No pp found. Have you set it up by {bot.default_prefix}pp?"
        self.stunned = f'You are stunned! Use `{bot.default_prefix}pp sf` to remove the effect!'

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        """Message Pattern Matching logic"""
        if msg.guild and (msg.guild.id == guild_id or debug) and self.mpm and not msg.author.bot:
            if re.search(r".*BSoD", msg.content):
                await msg.reply('https://discord.com/channels/675477913411518485/675477914019430423/825823145315270687')
                return
            match = re.search(r".*(where|how) .*?(get|download|find|obtain|acquire) ", msg.content, re.IGNORECASE)
            if match:  # Download-related
                match = msg.content
                # match = match.string[match.span()[1]:]
                if re.search(r"(.* |^)(switch|yuzu|ryu)", match, re.IGNORECASE):
                    if re.search(r"(.* |^)(game|nsp|xci|rom)", match, re.IGNORECASE):
                        await msg.reply("Please use <#730596209701421076>, don't use FitGirl repacks.")
                    elif re.search(r"(.* |^)shader", match, re.IGNORECASE):
                        await msg.reply("<#709944999399260190>")
                    elif re.search(r"(.* |^)key", match, re.IGNORECASE):
                        await msg.reply("<#702908846565490708>")
                    elif re.search(r"(.* |^)change ?log", match, re.IGNORECASE):
                        await msg.reply("<#749927995183202376>")
                    elif re.search(r"(.* |^).*mod", match, re.IGNORECASE):
                        await msg.reply("Please check pins in <#702621234835226744>")
                    elif re.search(r"(.* |^)save", match, re.IGNORECASE):
                        await msg.reply("<#718565804345393182>")
                    elif re.search(r"(.* |^)mii", match, re.IGNORECASE):
                        await msg.reply("<#731478871823613962>")
                    elif re.search(r"(.* |^)firmware", match, re.IGNORECASE):
                        await msg.reply("Yuzu doesn't need firmware. Unsubscribe the guy that said it.\nSwitch firmware"
                                        " link is in the oldest pin at <#718990080387317850> but I PMed you")
                        await msg.author.send(decode('aHR0cHM6Ly9kYXJ0aHN0ZXJuaWUubmV0L3N3aXRjaC1maXJtd2FyZXMv'))
                elif re.search(r"(.* |^)(cemu|wii ?u)", match, re.IGNORECASE):
                    await msg.reply("May I suggest you <#718989936837263450> pins?")
                elif re.search(r"(.* |^)(citra|3ds) ", match, re.IGNORECASE):
                    await msg.reply("May I suggest you <#750213635975938112> pins?")
                elif re.search(r"(.* |^)(gc|gamecube|wii|dolphin) ", match, re.IGNORECASE):
                    await msg.reply("May I suggest you <#750178026704207944> pins?")
                elif re.search(r"(.* |^)n?ds", match, re.IGNORECASE):
                    await msg.reply("May I suggest you <#749996667511767090> pins?")
                elif re.search(r"(.* |^)(rom|game|shader|mod|key|save|mii|firmware)", match, re.IGNORECASE):
                    await msg.reply('Please specify the emulator you want e.g. `Where download switch games`\n'
                                    'Tips: You can send `d.dec <base64>` to decode all those aHxxxx text!')
                elif re.search(r"(.* |^)amiibo", match, re.IGNORECASE):
                    await msg.reply('<#796160202067017789>')

    @command(aliases=['enc'])
    async def encode(self, ctx: Context, *, url: str):
        """Encodes base64 via command"""
        if ctx.channel.type == discord.ChannelType.text:
            await ctx.message.delete()
        if Missile.regex_is_url(url):
            await ctx.send(f'<https://codebeautify.org/base64-decode?input={encode(url)}>')
        else:
            url = ctx.author.mention + ': ' + url
            await ctx.send(encode(url))

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
            await ctx.author.send(decode(content))
            await ctx.message.add_reaction('✅')
        except (UnicodeDecodeError, binascii.Error):
            await ctx.send('Malformed base64 string.')

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
            if pp.sesami_oil:
                description += '\nSesami oil'
            if pp.size == max_pp_size:
                description += '\n**MAX POWER**'
            if pp.stun:
                description += f'\n**STUNNED:** {pp.stun} rounds left'
            return description
        return self.no_pp_msg

    @group(invoke_without_command=True)
    async def pp(self, ctx: Context, user: discord.User = None):
        """
        Wiki for the d.pp commands: https://github.com/TCLRainbow/DimBot/wiki/pp
        """
        # Randomises user's pp size
        my = self.get_pp(ctx.author.id)
        if my and my.stun:
            await ctx.reply(self.stunned)
            return
        user = user if user else ctx.author
        size = randint(0, max_pp_size)
        viagra = randint(0, 100) < 25
        sesami = randint(0, 100) < 10
        pp = self.get_pp(user.id)
        if pp:
            if pp.stun:
                await ctx.reply(f"{user} is stunned, you can't change his pp!")
                return
            pp.size = size
            pp.viagra_available = viagra
            pp.viagra_rounds = 0
            if sesami:
                pp.sesami_oil = True
        else:
            self.organs[user.id] = PP(size, viagra, sesami)
        await ctx.send(embed=discord.Embed(title=user.display_name + "'s penis", description=self.draw_pp(user.id),
                                           colour=discord.Colour.random()))

    @pp.command()
    async def info(self, ctx: Context, user: discord.User = None):
        """Shows the pp info"""
        user = user if user else ctx.author
        pp = self.get_pp(user.id)
        if pp:
            await ctx.reply(embed=obj.Embed('pp size: ' + str(pp.size), self.draw_pp(user.id)))
        else:
            await ctx.send(self.no_pp_msg)

    @pp.command()
    async def slap(self, ctx: Context, user: discord.User):
        """Use pp to slap others"""
        if self.get_pp(ctx.author.id):
            await ctx.send(embed=obj.Embed(description=self.draw_pp(ctx.author.id), thumbnail=user.avatar_url))
        else:
            await ctx.send(self.no_pp_msg)

    @pp.command()
    @Missile.is_rainbow_cmd_check()
    async def max(self, ctx: Context, target: discord.User = None, viagra=True, sesami=True):
        target = target if target else ctx.author
        self.organs[target.id] = PP(max_pp_size, viagra, sesami)
        await ctx.reply(embed=obj.Embed(target.display_name + "'s penis", self.draw_pp(target.id)))

    @pp.command()
    async def min(self, ctx: Context):
        """Minimises your pp strength"""
        my = self.get_pp(ctx.author.id)
        stun = my.stun if my else 0
        self.organs[ctx.author.id] = PP(0, False, False, stun=stun)
        await ctx.reply(embed=obj.Embed(ctx.author.display_name + "'s penis", self.draw_pp(ctx.author.id)))

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
            if my.stun:
                stun_msg = 'Focusing energy on your muscle, your pp is slowly twitching.'
                my.stun -= 1
                if not my.stun:
                    stun_msg += '\nWith a masculine roar, your pp has fully recovered from the stun.'
                await ctx.reply(stun_msg)
                return
            if his:
                if his.sesami_oil:
                    his.sesami_oil = False
                    await ctx.reply('Your opponent has **Sesami oil**, it slid off your pp!')
                    return
                xp = my.size - his.size
                if my.size > his.size:
                    title = "VICTORY"
                    gain_msg = f"You gained **{xp}** score!"
                elif my.size == his.size:
                    title = "TIE"
                    gain_msg = ''
                else:
                    title = "LOST"
                    gain_msg = f"You lost **{-xp}** score!"
                my.score += xp
            else:
                title = "WIN...?"  # Should not gain xp if opponent has no pp
                gain_msg = 'You gained nothing!'
            if my.viagra_rounds > 1:
                my.viagra_rounds -= 1
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
                                colour=discord.Colour.random()))
        if my and my.viagra_rounds == 1:
            my.size = my.size // 2
            my.viagra_rounds = 0
            await ctx.send(f"Faith effect has worn off for {ctx.author.display_name}'s pp")

    @pp.command()
    async def lb(self, ctx: Context):
        """Shows the pp leaderboard"""
        self.organs = dict(
            sorted(self.organs.items(), key=lambda item: item[1].score, reverse=True))  # Sort self.xp by score
        base = 'pp score leaderboard:\n'
        for key in self.organs.keys():
            base += f"{self.bot.get_user(key).name}: **{self.organs[key].score}** "
        await ctx.reply(base)

    @pp.command()
    async def viagra(self, ctx: Context):
        """In your pp, WE TRUST"""
        pp = self.get_pp(ctx.author.id)
        if pp:
            if pp.stun:
                await ctx.reply(self.stunned)
                return
            if pp.viagra_rounds:
                await ctx.reply('You are already one with your pp! Rounds left: ' + str(pp.viagra_rounds))
            elif pp.viagra_available:
                pp.viagra_available = False
                pp.size = pp.size * 2
                pp.viagra_rounds = 3
                await ctx.send(ctx.author.mention + " has faith in his pp!!!!! New pp size: " + str(pp.size))
            else:
                await ctx.reply('Your pp is not ready for it!')
        else:
            await ctx.reply(self.no_pp_msg)

    @pp.command(aliases=('zen',))
    async def zenitsu(self, ctx: Context, user: discord.User = None):
        """Stuns your opponent"""
        my = self.get_pp(ctx.author.id)
        if my and my.sesami_oil and my.viagra_available:
            if not user:
                user = self.bot.get_user(random.choice(list(self.organs.keys())))
            his = self.get_pp(user.id)
            if his:
                his.stun = 2
                my.sesami_oil = my.viagra_available = False
                await ctx.reply(f"Inhaling thunder, you stunned {user}")
            else:
                await ctx.reply(PP.target_no_pp)
        else:
            await ctx.reply("You need to have sesami oil and viagra available!")

    @pp.command()
    async def changelog(self, ctx: Context):
        """Shows the latest changelog of the PP command"""
        await ctx.reply(PP.log)
