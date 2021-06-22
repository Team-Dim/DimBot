import random
from random import randint

import discord
from discord.ext.commands import Cog, Context, group, cooldown, BucketType, CommandError

import missile

max_pp_size = 69


class BasePPException(CommandError):
    def __init__(self, message=None, *args):
        self.message = message
        super().__init__(message, args)

    def __str__(self):
        return self.message


class PPNotFound(BasePPException):

    def __init__(self, target_is_sender: bool):
        if target_is_sender:
            super().__init__("Please set up your pp by `{0}pp`!")
        else:
            super().__init__('Target has no pp.')


class PPStunned(BasePPException):
    def __init__(self, target_is_sender: bool):
        if target_is_sender:
            super().__init__('Your pp is stunned! Please use `{0}pp sf` to remove the effect!')
        else:
            super().__init__('Target is stunned!')


class PPLocked(BasePPException):
    def __init__(self, target_is_sender: bool):
        if target_is_sender:
            super().__init__('Your pp is locked! Please use `{0}pp lock` to unlock!')
        else:
            super().__init__('Target has enabled lock!')


class PP:

    def __init__(self, size: int, viagra, sesami, stun=0):
        self.size: int = size
        self.viagra: int = viagra  # -1: Not available 0: Not activated 1-3: rounds left
        self.score = 0
        self.sesami_oil: bool = sesami
        self.stun: int = stun
        self.lock: bool = False

    def draw(self) -> str:
        """Returns the string for displaying pp"""
        description = f'Ɛ{"Ξ" * self.size}＞'
        if self.lock:
            description = f"🔒Locked\n{description}"
        if self.viagra > 0:
            description = f'**{description}**\nViagra rounds left: {self.viagra}'
        elif self.viagra == 0:
            description += '\nViagra available!'
        if self.sesami_oil:
            description += '\nSesami oil'
        if self.size == max_pp_size:
            description += '\n**MAX POWER**'
        if self.stun:
            description += f'\n**STUNNED:** {self.stun} rounds left'
        return description

    def check_lock(self, b):
        if self.lock:
            raise PPLocked(b)
        return self


class Diminator(Cog):
    """PP command group
    Version 0.1"""

    def __init__(self, bot):
        self.bot: missile.Bot = bot
        self.organs: dict = {}  # Dict for storing pp size

    @staticmethod
    def pp_embed(user: discord.User, pp: PP):
        return missile.Embed(user.display_name + "'s pp", pp.draw())

    def get_pp(self, ctx: Context, target_id: int):
        if self.organs.get(target_id, None):
            return self.organs[target_id]
        raise PPNotFound(ctx.author.id == target_id)

    def get_pp_checked(self, ctx: Context, target_id: int):
        pp = self.get_pp(ctx, target_id)
        b = ctx.author.id == target_id
        if pp.stun:
            raise PPStunned(b)
        pp.check_lock(b)
        return pp

    @group(invoke_without_command=True, brief='Commands for interacting with your pp')
    async def pp(self, ctx: Context, user: discord.User = None):
        """
        If no valid subcommands are supplied, the command can be used in this way:
        `pp [user]`
        user: The target whose pp will be rerolled.
        """
        if user:  # If target already has pp, allows modifying. Else throw PPNotFound as you can't initialise others
            pp = self.get_pp(ctx, user.id)
            pp.check_lock(ctx.author == user)
        else:  # Check if sender has pp as no target is specified
            user = ctx.author
            pp = self.organs.get(ctx.author.id, None)
        if pp and pp.stun:  # Checks whether the to-be-rolled PP is stunned
            raise PPStunned(ctx.author.id == user.id)
        # Randomises user's pp properties
        size = randint(0, max_pp_size)
        viagra = (randint(0, 100) < 25) - 1
        sesami = randint(0, 100) < 10
        if pp:  # Updates a PP if exist
            pp.size = size
            pp.viagra = viagra
            if sesami:
                pp.sesami_oil = True
        else:  # Creates PP if not exist
            pp = self.organs[user.id] = PP(size, viagra, sesami)
        await ctx.reply(embed=self.pp_embed(user, pp))

    @pp.command(brief='Display pp info of a user')
    async def info(self, ctx: Context, user: discord.User = None):
        """pp info [user]
        user: The target to check. Defaults to command sender."""
        user = user if user else ctx.author
        pp = self.get_pp(ctx, user.id)
        await ctx.reply(embed=missile.Embed(f'pp size: {pp.size}', pp.draw()))

    @pp.command(brief='Use your pp to slap others')
    async def slap(self, ctx: Context, user: discord.User):
        """pp slap <user>
        user: The user to slap"""
        pp = self.get_pp(ctx, ctx.author.id)
        await ctx.send(embed=missile.Embed(description=pp.draw(), thumbnail=user.avatar_url))

    @pp.command()
    @missile.is_rainbow()
    async def max(self, ctx: Context, target: discord.User = None, viagra=True, sesami=True):
        target = target if target else ctx.author
        viagra -= 1
        self.organs[target.id] = PP(max_pp_size, viagra, sesami)
        await ctx.reply(embed=self.pp_embed(target, self.organs[target.id]))

    @pp.command()
    async def min(self, ctx: Context):
        """Minimises your pp strength"""
        pp = self.get_pp(ctx, ctx.author.id)
        pp = PP(0, -1, False, pp.stun)
        await ctx.reply(embed=self.pp_embed(ctx.author, pp))

    @pp.command()
    async def cut(self, ctx: Context):
        """Cuts your pp"""
        # Internally this removes the user from self.organs
        pp = self.get_pp(ctx, ctx.author.id)
        if await self.bot.ask_reaction(ctx, '⚠Cutting your pp also resets your score! Are you sure?'):
            self.organs.pop(ctx.author.id)
            await ctx.send(embed=discord.Embed(
                title=ctx.author.display_name + "'s penis",
                description=f"Ɛ\n{'Ξ' * pp.size}＞",
                color=discord.Color.red()))

    @pp.command(aliases=('sf',), brief='Use your pp as a weapon and fight')
    @cooldown(rate=1, per=10.0, type=BucketType.user)  # Each person can only call this once per 10s
    async def swordfight(self, ctx: Context, user: discord.User = None):
        """pp swordfight [user]
        user: Your opponent. If you didn't specify a user as your opponent,
        bot randomly picks a user that has a pp registered, **INCLUDING YOURSELF**"""
        if not user:
            user = self.bot.get_user(random.choice(list(self.organs.keys())))
        my = self.get_pp(ctx, ctx.author.id).check_lock(True)
        his = self.get_pp(ctx, user.id).check_lock(ctx.author == user)
        content = ''
        if my.stun:
            stun_msg = 'Focusing energy on your muscle, your hand is slowly moving.'
            my.stun -= 1
            if not my.stun:
                stun_msg += '\nWith a masculine roar, you are wielding your light saber again.'
            await ctx.reply(stun_msg)
            return
        if his.sesami_oil:
            his.sesami_oil = False
            await ctx.reply('Your opponent instantly deflects your attack.')
            return
        xp = my.size - his.size
        my.score += xp
        if my.viagra > 1:
            my.viagra -= 1
        elif my.viagra == 1:
            my.viagra = -1
            my.size //= 2
            content = f"{ctx.author} ran out of ammo!"
        if my.size > his.size:
            title = "VICTORY"
            gain_msg = f"You gained **{xp}** score!"
        elif my.size == his.size:
            title = "TIE"
            gain_msg = ''
        else:
            title = "LOST"
            gain_msg = f"You lost **{-xp}** score!"
        await ctx.send(
            content=content,
            embed=missile.Embed(title, f"**{ctx.author.name}'s pp:**\n{my.draw()}\n"
                                       f"**{user.name}'s pp:**\n{his.draw()}\n\n{gain_msg}"))

    @pp.command(aliases=('lb',))
    async def leaderboard(self, ctx: Context):
        """Shows the pp leaderboard"""
        self.organs = dict(
            sorted(self.organs.items(), key=lambda item: item[1].score, reverse=True))  # Sort self.xp by score
        base = 'pp score leaderboard:\n'
        for key in self.organs.keys():
            base += f"{self.bot.get_user(key).name}: **{self.organs[key].score}** "
        await ctx.reply(base)

    @pp.command(brief='In your pp, WE TRUST')
    async def viagra(self, ctx: Context):
        """If you have viagra available, doubles your pp size for 3 rounds."""
        pp = self.get_pp_checked(ctx, ctx.author.id)
        if pp.viagra:
            await ctx.reply('You are already one with your pp! Rounds left: ' + str(pp.viagra))
        elif pp.viagra == 0:
            pp.viagra = 3
            pp.size *= 2
            await ctx.send(f'{ctx.author.mention} has faith in his pp!!! New length: {pp.size}')
        else:
            await ctx.reply("You don't have viagra yet!")

    @pp.command(aliases=('zen',), brief='Stuns your opponent')
    async def zenitsu(self, ctx: Context, user: discord.User = None):
        """`pp zenitsu [user]`
        user: The target to stun. If you didn't specify a user as your opponent,
bot randomly picks a user that has a pp registered, **INCLUDING YOURSELF**"""
        my = self.get_pp_checked(ctx, ctx.author.id)
        if my.sesami_oil and my.viagra == 0:
            if not user:
                user = self.bot.get_user(random.choice(list(self.organs.keys())))
            his = self.get_pp_checked(ctx, user.id)
            his.stun = 2
            my.sesami_oil = my.viagra_available = False
            await ctx.reply(
                "https://i.pinimg.com/originals/0e/20/37/0e2037b27580b13d9141bc9cf0162b71.gif\n"
                f"Inhaling thunder, you stunned {user}!")
        else:
            await ctx.reply("You need to have viagra available and sesami oil!")

    @pp.command()
    async def changelog(self, ctx: Context):
        """Shows the latest changelog of the PP command"""
        await ctx.reply("""
    **__May 8, 3:58AM GMT+1__** (Rocket Update 2)\n
    Fixes a glitch where you can still attack others with lock on\n
    Lock command now has a cool down of 30s
    """)

    @pp.command()
    @cooldown(rate=1, per=30.0, type=BucketType.user)  # Each person can only call this once per 30s
    async def lock(self, ctx: Context):
        """Toggles your pp lock."""
        pp = self.get_pp(ctx, ctx.author.id)
        pp.lock = not pp.lock
        await ctx.reply(f'Your pp is now {"" if pp.lock else "un"}locked.')
