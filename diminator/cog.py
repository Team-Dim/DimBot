import asyncio
import random
from copy import copy

import discord
from discord.ext import commands
from discord.ext.commands import Context, BucketType

import missile
from diminator.obj import UltraRockPaperScissor, PPNotFound, PP, max_pp_size


def pp_embed(user: discord.User, pp: PP):
    return missile.Embed(user.display_name + "'s pp", pp.draw())


class Diminator(commands.Cog):
    """Named by <@259576375424319489>, Mini games
    Version 0.2"""

    def __init__(self, bot):
        self.bot: missile.Bot = bot
        self.urps = {}

    @commands.cooldown(1, 10, commands.BucketType.user)
    @commands.command(name='urps')
    async def urps_cmd(self, ctx: commands.Context, h: int = 16):
        """Ultra Rock Paper Scissor
        `urps [1-15]` to pick a choice. If you didn't provide a number or
        the number is not 1-15, randomly chooses for you.

        If you started the round, you have to wait 10s. During this period, any person can send this command to join."""
        if not 1 <= h <= 15:
            h = random.randint(1, 15)
        if ctx.author.id not in self.urps:
            self.urps[ctx.author.id] = [ctx.message, UltraRockPaperScissor(h), 0]
        self.bot.loop.create_task(ctx.message.add_reaction('✅'))
        if len(self.urps) == 1:
            fake_ctx = copy(ctx.message)
            fake_ctx.author = self.bot.user
            self.urps[self.bot.user.id] = [fake_ctx, UltraRockPaperScissor(random.randint(1, 15)), 0]
            await asyncio.sleep(10)
            keys = tuple(self.urps)
            for i, key in enumerate(keys):
                for opponent in keys[i + 1:]:
                    score = self.urps[key][1].resolve(self.urps[opponent][1])
                    self.urps[key][2] += score
                    self.urps[opponent][2] -= score
            self.urps = dict(sorted(self.urps.items(), key=lambda e: e[1][2], reverse=True))
            resp = '**Score** | Name | Choice\n'
            for u in self.urps.values():
                resp += f'**{u[2]}** {u[0].author}, {u[1].name}\n'
            dest = []
            for u in self.urps.values():
                if u[0].channel not in dest:
                    await u[0].reply(resp)
                    dest.append(u[0].channel)
            self.urps = {}

    def get_pp(self, ctx: Context, target_id: int):
        us = self.bot.get_user_store(target_id)
        if us.pp:
            return us.pp
        raise PPNotFound(ctx.author.id == target_id)

    def get_pp_checked(self, ctx: Context, target_id: int):
        return self.get_pp(ctx, target_id).check_all(ctx.author.id == target_id)

    def get_random_pp_opponent(self):
        return self.bot.get_user(random.choice(tuple(self.bot.user_store.keys())))

    @commands.group(invoke_without_command=True, brief='Commands for interacting with your pp')
    async def pp(self, ctx: Context, user: discord.User = None):
        """
        If no valid subcommands are supplied, the command can be used in this way:
        `pp [user]`
        user: The target whose pp will be rerolled.
        """
        user = user if user else ctx.author
        pp = self.bot.get_user_store(user.id).pp
        if pp:
            pp.check_all(ctx.author == user)
            if pp.transam == 101:
                await ctx.reply("Target is in TRANS-AM so you can't modify it!")
                return
        elif user != ctx.author:
            raise PPNotFound(False)
        # Randomises user's pp properties
        size = random.randint(0, max_pp_size)
        viagra = (random.randint(0, 100) < 25) - 1
        sesami = random.randint(0, 100) < 10
        if pp:  # Updates a PP if exist
            pp.size = size
            pp.viagra = viagra
            if sesami:
                pp.sesami_oil = True
        else:  # Creates PP if not exist
            pp = self.bot.user_store[user.id].pp = PP(size, viagra, sesami)
        await ctx.reply(embed=pp_embed(user, pp))

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
        pp = PP(max_pp_size, viagra, sesami)
        pp.transam = 100
        self.bot.get_user_store(target.id).pp = pp
        await ctx.reply(embed=pp_embed(target, pp))

    @pp.command()
    async def min(self, ctx: Context):
        """Minimises your pp strength"""
        pp = self.get_pp(ctx, ctx.author.id)
        pp = self.bot.user_store[ctx.author.id].pp = PP(0, -1, False, pp.stun)
        await ctx.reply(embed=pp_embed(ctx.author, pp))

    @pp.command()
    async def cut(self, ctx: Context):
        """Cuts your pp"""
        pp = self.get_pp(ctx, ctx.author.id)
        if await self.bot.ask_reaction(ctx, '⚠Cutting your pp also resets your score! Are you sure?'):
            self.bot.user_store[ctx.author.id].pp = None
            await ctx.send(embed=discord.Embed(
                title=ctx.author.display_name + "'s penis",
                description=f"Ɛ\n{'Ξ' * pp.size}＞",
                color=discord.Color.red()))

    @pp.command(aliases=('sf',), brief='Use your pp as a weapon and fight')
    @commands.cooldown(rate=1, per=10.0, type=BucketType.user)  # Each person can only call this once per 10s
    async def swordfight(self, ctx: Context, user: discord.User = None):
        """pp swordfight [user]
        user: Your opponent. If you didn't specify a user as your opponent,
        bot randomly picks a user that has a pp registered, **INCLUDING YOURSELF**"""
        if not user:
            if not filter(lambda us: us.pp, self.bot.user_store.values()):
                await ctx.reply('No one has pp yet.')
                return
            user = self.get_random_pp_opponent()
        my = self.get_pp(ctx, ctx.author.id).check_lock(True)
        if my.transam:
            ctx.command.reset_cooldown(ctx)
        his = self.get_pp(ctx, user.id).check_lock(False).check_transam_deflect()
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
            await ctx.reply('Your opponent instantly deflects your attack with sesami oil.')
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
            if my.transam <= 100:
                my.transam += 1
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
        has_pps, no_pps = [], []
        for uid, us in self.bot.user_store.items():
            has_pps.append((uid, us)) if us.pp else no_pps.append((uid, us))
        new_us = {}
        base = 'pp score leaderboard:\n'
        for uid, us in sorted(has_pps, key=lambda u: u[1].pp.score, reverse=True):
            new_us[uid] = us  # Sort user store by score
            base += f"{self.bot.get_user(uid).name}: **{us.pp.score}** "
        for uid, us in no_pps:
            new_us[uid] = us
        self.bot.user_store = new_us
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
                user = self.get_random_pp_opponent()
            his = self.get_pp_checked(ctx, user.id)
            my.sesami_oil = my.viagra_available = False
            his.check_transam_deflect()
            his.stun = 2
            await ctx.reply(
                "https://i.pinimg.com/originals/0e/20/37/0e2037b27580b13d9141bc9cf0162b71.gif\n"
                f"Inhaling thunder, you stunned {user}!")
        else:
            await ctx.reply("You need to have viagra available and sesami oil!")

    @pp.command()
    async def changelog(self, ctx: Context):
        """Shows the latest changelog of the PP command"""
        await ctx.reply("""
        **__Aug 26, 1:10AM GMT+8__** (Rocket Update 3)\n
        New ability: `TRANS-AM`
        There is a new TRANS-AM meter. If you win in a swordfight, the counter increases by 1.
        When it reaches 100, you can activate it by `d.pp transam`, which grants you:
        
        - `d.pp sf` cooldown is removed.
        - All attacks from all opponents have a 80% chance of being neglected.
        - No one can modify your pp at all, even yourself.
        
        These effects will be cleared after 15s.
        """)

    @pp.command()
    @commands.cooldown(rate=1, per=30.0, type=BucketType.user)  # Each person can only call this once per 30s
    async def lock(self, ctx: Context):
        """Toggles your pp lock."""
        pp = self.get_pp(ctx, ctx.author.id)
        pp.lock = not pp.lock
        await ctx.reply(f'Your pp is now {"" if pp.lock else "un"}locked.')

    @pp.command()
    async def transam(self, ctx: Context):
        pp = self.get_pp(ctx, ctx.author.id)
        if pp.transam == 100:
            pp.transam = 101
            pp.size *= 2
            await ctx.reply('https://imgur.com/B6X6F6d\n**TRANS-AM!** Let the purified GN particles cover the world, '
                            'bring peace to every corner of the Earth with a true innovator!')
            await asyncio.sleep(15)
            pp.transam = 0
            pp.size //= 2
            await ctx.reply('TRANS-AM has worn off.')
        else:
            await ctx.reply(f'TRANS-AM still charging! ({pp.transam})%')
