import base64
import random
import re
from random import randint
from typing import Optional

import discord
from discord.ext.commands import Cog, Context, command, has_any_role, group, cooldown, BucketType

import missile
from dimsecret import debug

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
    target_no_pp = 'Your opponent is not trained yet.'
    log = "**__May 4, 5:00PM GMT+1__**\n" \
          "May the force be with you! You are now a soldier in the battlefield! Oh and also `d.pp cw`"

    def __init__(self, size: int, viagra, sesami, is_good, stun=0):
        self.size: int = size
        self.viagra: int = 0  # -1: Not available 0: Not activated 1-3: rounds left
        self.score = 0
        self.sesami_oil: bool = sesami
        self.stun: int = stun
        self.is_good: int = is_good


class BitBay(Cog):
    """Utilities for 128BB
    Version 1.3.3"""

    def __init__(self, bot):
        self.bot: missile.Bot = bot
        self.organs: dict = {}  # Dict for storing pp size
        self.mpm = True  # Message Pattern Matching master switch
        self.no_pp_msg = f"No light saber found. Have you set it up by {bot.default_prefix}pp?"
        self.stunned = f'You are stunned! Use `{bot.default_prefix}pp sf` to remove the effect!'
        with open('ls.json', 'r') as f:
            import json
            self.clan_war = json.load(f)
        self.clan_war[0] = self.clan_war['0']
        self.clan_war[1] = self.clan_war['1']
        self.clan_war.pop('0')
        self.clan_war.pop('1')
        self.fight_count = 742

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

    @command(aliases=('enc',))
    async def encode(self, ctx: Context, *, url: str):
        """Encodes base64 via command"""
        if ctx.channel.type == discord.ChannelType.text:
            await ctx.message.delete()
        if missile.is_url(url):
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

    @command(aliases=('dec',))
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
        description = f'{"Sith lord" if pp.is_good else "Jedi master"}\n-|{"=" * pp.size}'
        if pp.viagra > 0:
            description = f'**{description}**\nViagra rounds left: {pp.viagra}'
        elif pp.viagra == 0:
            description += '\nBlaster available!'
        if pp.sesami_oil:
            description += '\nOne with the force'
        if pp.size == max_pp_size:
            description += '\n**MAX POWER**'
        if pp.stun:
            description += f'\n**STUNNED:** {pp.stun} rounds left'
        return description

    def pp_embed(self, user):
        return missile.Embed(user.display_name + "'s light saber", self.draw_pp(user.id))

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
        viagra = (randint(0, 100) < 25) - 1
        sesami = randint(0, 100) < 10
        is_good = randint(0, 100) < 50
        pp = self.get_pp(user.id)
        if pp:
            if pp.stun:
                await ctx.reply(f"{user} is stunned, you can't change his light saber!")
                return
            pp.size = size
            pp.viagra = viagra
            pp.is_good = is_good
            if sesami:
                pp.sesami_oil = True
        else:
            self.organs[user.id] = PP(size, viagra, sesami, is_good)
        await ctx.reply(embed=self.pp_embed(user))

    @pp.command()
    async def info(self, ctx: Context, user: discord.User = None):
        """Shows the pp info"""
        user = user if user else ctx.author
        pp = self.get_pp(user.id)
        if pp:
            await ctx.reply(embed=missile.Embed(f'Light saber size: {pp.size}', self.draw_pp(user.id)))
        else:
            await ctx.send(self.no_pp_msg)

    @pp.command()
    async def slap(self, ctx: Context, user: discord.User):
        """Use pp to slap others"""
        if self.get_pp(ctx.author.id):
            await ctx.send(embed=missile.Embed(description=self.draw_pp(ctx.author.id), thumbnail=user.avatar_url))
        else:
            await ctx.send(self.no_pp_msg)

    @pp.command()
    @missile.is_rainbow()
    async def max(self, ctx: Context, target: discord.User = None, viagra=True, sesami=True):
        target = target if target else ctx.author
        viagra -= 1
        self.organs[target.id] = PP(max_pp_size, viagra, sesami, randint(0, 100) < 50)
        await ctx.reply(embed=self.pp_embed(target))

    @pp.command()
    async def min(self, ctx: Context):
        """Minimises your pp strength"""
        my = self.get_pp(ctx.author.id)
        stun = my.stun if my else 0
        self.organs[ctx.author.id] = PP(0, -1, False, randint(0, 100) < 50, stun=stun)
        await ctx.reply(embed=self.pp_embed(ctx.author))

    @pp.command()
    async def cut(self, ctx: Context):
        """Cuts your pp"""
        # Internally this removes the user from self.organs
        await ctx.reply('You cannot flee in Star Wars!')
        return
        pp = self.get_pp(ctx.author.id)
        if pp:
            if await self.bot.ask_reaction(ctx, '⚠Cutting your pp also resets your score! Are you sure?'):
                self.organs.pop(ctx.author.id)
                await ctx.send(embed=missile.Embed(ctx.author.display_name + "'s penis", f"8\n{'=' * pp.size}D",
                                                   color=discord.Color.red()))
        else:
            await ctx.send('You have no pp to cut!')

    @pp.command(aliases=('sf',))
    @cooldown(rate=1, per=10.0, type=BucketType.user)  # Each person can only call this once per 10s
    async def swordfight(self, ctx: Context, user: discord.User = None):
        """Use your pp as a weapon and fight"""
        if not user:  # User did not specify a target to fight
            if not self.organs:  # There is no one to fight
                await ctx.reply(f'No one has light saber. Either `{self.bot.default_prefix}pp` yourself or any members first,'
                                f' or `{self.bot.default_prefix}pp sf @anyone`')
                return
            user = self.bot.get_user(random.choice(list(self.organs.keys())))
        my = self.get_pp(ctx.author.id)
        his = self.get_pp(user.id)
        content = ''
        if my:
            if my.stun:
                stun_msg = 'Focusing energy on your muscle, your hand is slowly moving.'
                my.stun -= 1
                if not my.stun:
                    stun_msg += '\nWith a masculine roar, you are wielding your light saber again.'
                await ctx.reply(stun_msg)
                return
            if his:
                self.fight_count += 1
                if my.viagra > 1:
                    my.viagra -= 1
                elif my.viagra == 1:
                    my.viagra = -1
                    content = f"{ctx.author} ran out of ammo!"
                if his.sesami_oil:
                    his.sesami_oil = False
                    await ctx.reply('Your opponent instantly deflects your attack.')
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
                self.clan_war[my.is_good] += xp
            else:
                await ctx.reply(PP.target_no_pp)
                return
        else:
            await ctx.reply(self.no_pp_msg)
            return
        await ctx.send(
            content=content,
            embed=missile.Embed(title, f"**{ctx.author.name}'s light saber:**\n{self.draw_pp(ctx.author.id)}\n"
                                       f"**{user.name}'s light saber:**\n{self.draw_pp(user.id)}\n\n{gain_msg}"))

    @pp.command()
    async def lb(self, ctx: Context):
        """Shows the pp leaderboard"""
        self.organs = dict(
            sorted(self.organs.items(), key=lambda item: item[1].score, reverse=True))  # Sort self.xp by score
        base = 'Light saber score leaderboard:\n'
        for key in self.organs.keys():
            base += f"{self.bot.get_user(key).name}: **{self.organs[key].score}** "
        await ctx.reply("Don't forget to checkout d.pp cw!\n" + base)

    @pp.command()
    async def cw(self, ctx: Context):
        embed = missile.Embed(
            'Star Wars war table', 'All of the scores here are Republic/Empire'
        )
        embed.add_field('Scores', f"{self.clan_war[0]}/{self.clan_war[1]}")
        part = [0, 0]
        for p in self.organs.values():
            part[p.is_good] += 1
        embed.add_field('Participants', f"{part[0]}/{part[1]}")
        embed.add_field('Fight count', self.fight_count)
        await ctx.reply(embed=embed)

    @pp.command()
    async def viagra(self, ctx: Context):
        """In your pp, WE TRUST"""
        pp = self.get_pp(ctx.author.id)
        if pp:
            if pp.stun:
                await ctx.reply(self.stunned)
                return
            if pp.viagra:
                await ctx.reply('You are already holding a blaster! Ammo left: ' + str(pp.viagra))
            elif pp.viagra == 0:
                pp.viagra = 3
                pp.size *= 2
                await ctx.send(f'{ctx.author.mention} is holding a blaster!!! New damage points: {pp.size}')
            else:
                await ctx.reply("You don't have a blaster!")
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
                await ctx.reply(f"https://gfycat.com/cheapaggravatingbarasinga-star-wars-7-the-force-awakens-people-blogs\nStunned {user}")
                # await ctx.reply(f"Reaching out your arm with, you stunned {user}")
            else:
                await ctx.reply(PP.target_no_pp)
        else:
            await ctx.reply("You need to have a blaster and focused!!")

    @pp.command()
    async def changelog(self, ctx: Context):
        """Shows the latest changelog of the PP command"""
        await ctx.reply(PP.log)
