import math
from datetime import datetime

import discord
from discord.ext import commands

import missile

l_naught = 50


def get_xp_gain(s: float):
    return round(math.e ** math.log((s + 1) ** 2, l_naught) * l_naught ** (1 / 3))


class XP(missile.Cog):
    """Experience point system
    Version 0.1"""

    def __init__(self, bot):
        super(XP, self).__init__(bot, 'XP')

    @commands.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.guild and not msg.author.bot:
            u_store = self.bot.user_store(msg.author.id)
            last_guild_s = u_store.get_last_xp_time(msg.guild.id)  # Must be b4 stamp
            stamp = datetime.now()
            if await self.bot.sql.user_xp_exists(self.bot.db, uid=msg.author.id, guildID=msg.guild.id):
                global_xp = await self.bot.sql.get_global_xp(self.bot.db, uid=msg.author.id)
                guild_xp = await self.bot.sql.get_xp(self.bot.db, uid=msg.author.id, guildID=msg.guild.id)
            elif await self.bot.sql.user_global_xp_exists(self.bot.db, uid=msg.author.id):
                global_xp = await self.bot.sql.get_global_xp(self.bot.db, uid=msg.author.id)
                await self.bot.sql.add_xp(self.bot.db, uid=msg.author.id, guildID=msg.guild.id)
                guild_xp = 0
            else:
                await self.bot.sql.add_xp(self.bot.db, uid=msg.author.id, guildID=msg.guild.id)
                await self.bot.sql.add_global_xp(self.bot.db, uid=msg.author.id)
                global_xp = guild_xp = 0
            global_s = min((stamp - u_store.last_xp_time[None]).total_seconds(), 60)
            guild_s = min((stamp - last_guild_s).total_seconds(), 60)
            global_gain = get_xp_gain(global_s)
            guild_gain = get_xp_gain(guild_s)
            self.logger.info(f"Global: {msg.author} spoke after {global_s}s, gain {global_gain}")
            self.logger.info(f"Guild: {msg.author} spoke after {guild_s}s, gain {guild_gain}")
            global_xp += global_gain
            guild_xp += guild_gain
            await self.bot.sql.update_global_xp(self.bot.db, xp=global_xp, uid=msg.author.id)
            await self.bot.sql.update_xp(self.bot.db, xp=guild_xp, uid=msg.author.id, guildID=msg.guild.id)
            u_store.last_xp_time[msg.guild.id] = u_store.last_xp_time[None] = stamp

    @commands.group(invoke_without_command=True)
    @missile.guild_only()
    async def xp(self, ctx: commands.Context, user: discord.User = None):
        """Shows the XP of someone"""
        user = user if user else ctx.author
        global_xp = await self.bot.sql.get_global_xp(self.bot.db, uid=user.id)
        if global_xp:
            global_count = await self.bot.sql.get_global_xp_count(self.bot.db)
            global_rank = 0
            async with self.bot.sql.get_global_xp_ranks_cursor(self.bot.db) as global_uids:
                async for global_uid in global_uids:
                    global_rank += 1
                    if global_uid[0] == user.id:
                        content = f"Cross-server XP: **{global_xp}**, Rank {global_rank}/{global_count}"
                        break
            guild_xp = await self.bot.sql.get_xp(self.bot.db, uid=user.id, guildID=ctx.guild.id)
            if guild_xp:
                count = await self.bot.sql.get_xp_count(self.bot.db, guildID=ctx.guild.id)
                guild_rank = 0
                async with self.bot.sql.get_xp_ranks_cursor(self.bot.db, guildID=ctx.guild.id) as guild_uids:
                    async for guild_uid in guild_uids:
                        guild_rank += 1
                        if guild_uid[0] == user.id:
                            content += f"\nServer-specific XP: **{guild_xp}**, Rank {guild_rank}/{count}"
                            break
        else:
            content = f"{user} has no XP record!"
        await ctx.reply(content)

    @xp.command(aliases=('lb',))
    @missile.guild_only()
    async def leaderboard(self, ctx: commands.Context, page: int = 0):
        """Shows the leaderboard"""
        count = 0
        content = ''
        async with self.bot.sql.get_xp_leaderboard_cursor(self.bot.db, guildID=ctx.guild.id, offset=page*10) as lb:
            async for row in lb:
                count += 1
                content += f"Rank {count}: {str(self.bot.get_user(row[0])):-<37} **{row[1]}**\n"
        if count:
            await ctx.reply(content)
