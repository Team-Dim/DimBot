import asyncio
import re

import discord
from discord.ext.commands import Cog

import bitbay
import missile

ext = missile.MsgExt('Aegis')


class Aegis(Cog):
    """AutoMod system
    Version 0.5"""

    def __init__(self, bot):
        self.bot = bot
        self.count = {}
        self.ghost_pings = {}  # Ghost ping message cache

    def act_wrap(self, msg: discord.Message, warn_type: str):
        self.count[msg.author.id][1] += 1
        self.count[msg.author.id][0] = []
        self.bot.loop.create_task(ext.reply(msg, f'Detected spam by {msg.author.mention}, type {warn_type}. '
                                                 f'Warn: {self.count[msg.author.id][1]}'))
        self.bot.loop.create_task(self.act(msg, f'Aegis: Spam, type {warn_type}'))

    @Cog.listener()
    async def on_message(self, msg: discord.Message):
        # Check whether message needs to be scanned by Aegis
        if not msg.guild or msg.author == msg.guild.me:
            return
        # Checks for crash gifs
        if re.search(r".*(gfycat.com/safeofficialharvestmouse|gfycat.com/grizzledwildinsect)", msg.content):
            await msg.delete()
            await ext.send(msg.channel, 'Detected crash GIF by ' + msg.author.mention)
        if msg.author.id not in self.count:  # Creates record for the message author
            self.count[msg.author.id] = [[], 0]  # [Tracked messages, warn count]
        raw_mention_count = len(msg.raw_mentions)
        if raw_mention_count >= 5:  # Mass ping
            self.count[msg.author.id][1] += 3
            self.bot.loop.create_task(ext.send(msg,
                                               f'Detected mass ping ({raw_mention_count}) by {msg.author.mention}. '
                                               f'Warn: {self.count[msg.author.id][1]}'))
            self.bot.loop.create_task(self.act(msg, 'Aegis: Mass ping'))
        elif msg.channel.id not in (
                bitbay.spam_ch_id, bitbay.bot_ch_id, 826418682154188851):  # Checks whether channel ignores spam
            ml = len(self.count[msg.author.id][0])
            if ml == 9:  # There are 9 previous messages:
                if (msg.created_at - self.count[msg.author.id][0][0]).total_seconds() < 10:  # 10 msg in 10s
                    self.act_wrap(msg, 'X')
                else:
                    self.count[msg.author.id][0].pop(0)  # We only track up to 10 previous messages
            if not msg.author.bot:
                if ml >= 4:  # There are 4 previous messages
                    if (msg.created_at - self.count[msg.author.id][0][ml - 4]).total_seconds() < 5:  # 5 msg in 5s
                        self.act_wrap(msg, 'V')
                # ml = len(self.count[msg.author.id][0])
                elif ml > 1 > (msg.created_at - self.count[msg.author.id][0][ml - 2]).total_seconds():  # 3 msg in 1s
                    self.act_wrap(msg, 'I')
            for t in self.count[msg.author.id][0]:  # If previous messages are >10s older than current, purge cache
                if (msg.created_at - t).total_seconds() >= 10:
                    self.count[msg.author.id][0].pop(0)
            self.count[msg.author.id][0].append(msg.created_at)  # Add current message for tracking

    async def act(self, msg: discord.Message, reason: str):
        """Takes action"""
        if type(msg.author) == discord.User:
            await msg.channel.send('⚠DETECTED UNUSUAL WEBHOOK ACTIVITIES, DELETING THE WEBHOOK\nPlease notify'
                                   'admins in this server!')
            webhooks = await msg.channel.webhooks()
            for webhook in webhooks:
                if webhook.id == msg.author.id:
                    webhook.delete(reason='Aegis: Unusual webhook activities')
                    await msg.channel.send(f'Deleted webhook <@{webhook.id}>')
                    return
            return
        ikaros = self.bot.get_cog('Ikaros')
        if self.count[msg.author.id][1] == 2:  # 3 warns in the past 2h
            await ikaros.mute(msg, msg.author, 10, 0, reason + ', threat level 1')  # 10s mute
        elif self.count[msg.author.id][1] == 3:  # 3 warns in the past 2h
            await ikaros.mute(msg, msg.author, 3600, 0, reason + ', threat level 2')  # 1h mute
        elif self.count[msg.author.id][1] == 4:  # 4 warns in the past 2h
            await ikaros.kick(msg, msg.author, 0, reason + ', threat level 3')  # Immediate kick
        elif self.count[msg.author.id][1] >= 5:  # >5 warns in the past 2h
            await ikaros.ban(msg, msg.author, 0, 0, reason + ', threat level 4')  # Immediate ban
        await asyncio.sleep(7200)  # Reduces total warn count by 1 after 2h
        self.count[msg.author.id][1] -= 1

    @Cog.listener()
    async def on_message_delete(self, msg: discord.Message):
        """Event handler when a message has been deleted"""
        # Ghost ping detector
        # Check whether the message is related to the bot
        if msg.author == msg.guild.me or msg.content.startswith(await self.bot.get_prefix(msg)):
            return
        if msg.guild and msg.id in self.ghost_pings.keys():  # The message has/used to have pings
            for m in self.ghost_pings[msg.id]:
                # Tells the victim that he has been ghost pinged
                await m.send(f'{msg.author.mention} ({msg.author}) pinged you in **{msg.guild.name}** and deleted it.')
            # Reports in the incident channel that the culprit deleted a ping
            await ext.send(msg, msg.author.mention + ' has deleted a ping')
            # Removes the message from the cache as it has been deleted on Discord
            self.ghost_pings.pop(msg.id)
        elif msg.guild and msg.mentions and not msg.edited_at:  # The message has pings and has not been edited
            for m in msg.mentions:
                if not m.bot:
                    # Tells the victim that he has been ghost pinged
                    try:
                        await m.send(
                            f'{msg.author.mention} ({msg.author}) pinged you in **{msg.guild.name}** and deleted it.')
                    except discord.Forbidden:
                        pass
            # Reports in the incident channel that the culprit deleted a ping
            await ext.send(msg, msg.author.mention + ' has deleted a ping')

    @Cog.listener()
    async def on_message_edit(self, before: discord.Message, after: discord.Message):
        """Event handler when a message has been edited. Detect ghost pings due to edited message"""
        if before.guild and not before.edited_at and before.mentions:  # A message that contains pings has been edited
            #  Add the message to ghost pings cache
            self.ghost_pings[before.id] = [m for m in before.mentions if not m.bot]
        if before.guild and before.id in self.ghost_pings.keys():  # Message requires ghost ping checking
            has_removed = False
            for m in self.ghost_pings[before.id]:
                if m not in after.mentions:  # A ping has been removed
                    has_removed = True
                    # Tells the victim that he has been ghost pinged
                    await m.send(f'{before.author.mention} pinged you in **{before.guild.name}** and deleted it.')
                    self.ghost_pings[before.id].remove(m)
            if has_removed:
                # Reports in the incident channel that the culprit deleted a ping
                await ext.send(before, before.author.mention + ' has removed a ping from a message')
            if not self.ghost_pings[before.id]:  # All original pings have bene removed.
                self.ghost_pings.pop(before.id)  # No longer have to track as there are no pings anymore.
