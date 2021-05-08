import asyncio
import re
from time import mktime

import aiosql
import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import commands
from discord.ext.commands import Context

import missile
from dimsecret import youtube


class Ricciardo(missile.Cog):
    """Relaying RSS, BBM and YouTube feeds to discord channels.
    Version 5.0"""

    def __init__(self, bot):
        super().__init__(bot, 'Ricciardo')
        self.addon_ids = (274058, 306357, 274326)  # List of addon IDs for BBM operations

    @commands.Cog.listener()
    async def on_ready(self):
        while True:
            # Dispatch tasks every 10 minutes
            self.bot.loop.create_task(self.raceline_task())
            await asyncio.sleep(600)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """When the bot leaves a server, remove subscriptions related to the server."""
        ch_ids = f"({','.join(str(ch.id) for ch in guild.text_channels)})"
        sql_str = f"""
        --name: del_cfg#
        DELETE FROM BbmRole WHERE bbmChID IN {ch_ids};
        DELETE FROM BbmAddon WHERE bbmChID IN {ch_ids};
        DELETE FROM RssSub WHERE rssChID IN {ch_ids};
        DELETE FROM RssData WHERE url NOT IN (SELECT url FROM RssSub);
        DELETE FROM YtSub WHERE ytChID IN {ch_ids};
        DELETE FROM YtData WHERE channelID NOT IN (SELECT channelID FROM YtSub);
        """
        query = aiosql.from_str(sql_str, 'aiosqlite')
        await query.del_cfg(self.bot.db)

    # noinspection PyBroadException
    async def raceline_task(self):
        """Dispatches RSS, BBM and YouTube update detectors"""
        bbm_futures = {}
        for addon_id in self.addon_ids:
            bbm_futures[addon_id] = self.bot.loop.create_task(self.bbm_process(addon_id))  # Dispatch BBM tasks
        resultless_futures = []
        async with self.bot.sql.get_rss_data_cursor(self.bot.db) as cursor:
            url_id = 1
            async for row in cursor:  # Dispatches RSS tasks
                resultless_futures.append(self.bot.loop.create_task(self.rss_process(url_id, row)))
                url_id += 1
        async with self.bot.sql.get_yt_data_cursor(self.bot.db) as cursor:
            async for row in cursor:  # Dispatches YouTube tasks
                resultless_futures.append(self.bot.loop.create_task(self.yt_process(row)))
        # The tasks are running. Now prepares when all BBM tasks return.
        await asyncio.wait(bbm_futures.values())  # Wait for all BBM tasks to return
        async with self.bot.sql.get_bbm_roles_cursor(self.bot.db) as bbm_role:  # Fetches role subscriptions for BBM
            async for row in bbm_role:
                default_msg = ''
                if row[1]:  # If the database contains a role in BBMRole, Ping it
                    default_msg = f"<@&{row[1]}>\n"
                msg = default_msg
                # Fetch addons that the text channel has subscribed
                async with self.bot.sql.get_subscribed_addons_cursor(self.bot.db, id=row[0]) as bbm_addon:
                    async for addon in bbm_addon:
                        msg += bbm_futures[addon[0]].result()  # Adds actual BBM update message
                    if msg != default_msg:  # Only send if there are BBM updates
                        self.bot.loop.create_task(self.bot.get_channel(row[0]).send(msg))
        # Wait for all tasks to be finished
        await asyncio.wait(resultless_futures)
        self.logger.debug('Synced')

    async def rss_process(self, rowid, row):
        """The main algorithm for RSS feed detector"""
        self.logger.info(f"RSS {rowid}: Checking RSS...")
        async with self.bot.session.get(row[0]) as response:  # Sends a GET request to the URL
            self.logger.debug(f"RSS {rowid}: Fetching response...")
            text = await response.text()
        self.logger.debug(f"RSS {rowid}: Parsing response...")
        feed = feedparser.parse(text).entries[0]  # Converts RSS response to library objects and read the first entry
        pubtime = mktime(feed.published_parsed)  # Converts the feed's publish timestamp to an integer

        # A feed with a new title and the publish timestamp is newer than database's record
        if row[1] != feed.title and pubtime > row[2]:
            self.logger.info(f'RSS {rowid}: Detected news: {feed.title}  Old: {row[1]}')
            content = BeautifulSoup(feed.description, 'html.parser')  # HTML Parser for extracting RSS feed content
            # Limits the content size to prevent spam
            description = (content.get_text()[:497] + '...') if len(content.get_text()) > 500 else content.get_text()

            # Fetch channels that subscribed to this RSS URL
            async with self.bot.sql.get_rss_subscriptions_cursor(self.bot.db, url=row[0]) as rss_subs:
                # Constructs base Embed object
                self.logger.debug(f"RSS {rowid}: Begin reading RssSub")
                emb = missile.Embed(feed.title, description, url=feed.link)
                async for rss_sub in rss_subs:
                    local_emb = emb.copy()
                    channel = self.bot.get_channel(rss_sub[0])
                    self.logger.debug(f"RSS {rowid}: RssSub channel {channel}")
                    local_emb.set_footer(text=f"{rss_sub[1]} | {feed.published}")  # Adds channel-specific footer
                    self.bot.loop.create_task(channel.send(embed=local_emb))
            self.logger.info(f"RSS {rowid}: Dispatched Discord message tasks")
            # Updates the database with the new feed
            await self.bot.sql.update_rss_data(self.bot.db, title=feed.title, time=pubtime, id=rowid)
            self.logger.debug(f"RSS {rowid}: Updated DB")
        self.logger.info(f"RSS {rowid}: Done")

    async def bbm_process(self, addon_id: int):
        """The main algorithm for the BBM update detector"""
        message = ''
        # Read BBM records from the database
        # Check for BBM updates
        async with self.bot.session.get(f'https://addons-ecs.forgesvc.net/api/v2/addon/{addon_id}') as response:
            self.logger.debug(f'Fetching BBM {addon_id}...')
            addon = await response.json()
        old_names = []
        async with self.bot.sql.get_bbm_addons_cursor(self.bot.db, id=addon_id) as titles:
            self.logger.debug(f"Reading addon titles for {addon_id}")
            async for old_title in titles:
                exists = False
                for l_file in addon['latestFiles']:
                    if old_title[0] == l_file['displayName']:
                        exists = True
                        addon['latestFiles'].remove(l_file)
                        break
                if not exists:
                    old_names.append(old_title[0])
                self.logger.info(f'BBM {addon_id} ({old_title[0]}) has update? {not exists}')
        # All that remains is addons that have updates
        for i, latest_file in enumerate(addon['latestFiles']):
            # Fetch the changelog of that addon update
            async with self.bot.session.get(
                    f"https://addons-ecs.forgesvc.net/api/v2/addon/{addon_id}/file/{latest_file['id']}/changelog") \
                    as response:
                self.logger.debug(f'BBM {addon_id} fetching changelogs')
                change_log = await response.text()
            change_log = BeautifulSoup(change_log, 'html.parser')  # HTML Parser
            # Due to how inconsistent the endpoint is, sometimes there is literally missing information. Smh
            game_version = latest_file['gameVersion'][0] if latest_file['gameVersion'] else None
            # Adds update info to the base message
            message += f"An update of **{addon['name']}** is now available!\n" \
                       f"__**{latest_file['displayName']}** for **{game_version}**__\n" \
                       f"{change_log.get_text()}\n\n"
            # Updates the database
            await self.bot.sql.update_bbm_addon(self.bot.db, old=titles[i][0], new=latest_file['displayName'])
            self.logger.debug(f'BBM {addon_id} updated DB')
        self.logger.info(f'BBM {addon_id} completed')
        return message

    async def yt_process(self, row):
        return
        """The main algorithm for detecting YouTube videos"""
        self.logger.info(f"Checking YouTube channel ID {row['channelID']}")
        # Fetch the channel's latest activity
        async with self.bot.session.get('https://www.googleapis.com/youtube/v3/activities?part=snippet,'
                                        f"contentDetails&channelId={row['channelID']}&maxResults=1&key={youtube}") \
                as response:
            activities = await response.json()
            if activities['items'][0]['snippet']['type'] == 'upload':  # The latest activity type is upload
                video_id = activities['items'][0]['contentDetails']['upload']['videoId']
                if row['videoID'] != video_id:  # New video ID detected
                    self.logger.debug('New YT video detected for channel ID ' + row['channelID'])
                    # Fetches Discord channels that have subscribed to that YouTube channel
                    yt_sub = self.bot.cursor.execute('SELECT ytChID from YtSub WHERE channelID = ?',
                                                     (row['channelID'],)).fetchall()
                    for sub in yt_sub:
                        ch = self.bot.get_channel(sub[0])
                        # Notifies the Discord channel that a new video has been found
                        self.bot.loop.create_task(ch.send("https://youtube.com/watch?v=" + video_id))
                    # Update database
                    self.bot.cursor.execute('UPDATE YtData SET videoID = ? WHERE channelID = ?',
                                            (video_id, row['channelID']))

    @commands.group(invoke_without_command=True)
    async def rss(self, ctx):
        """Commands for RSS feed update detector"""
        pass

    @rss.command(name='subscribe', aliases=['s', 'sub'])
    @missile.is_channel_owner()
    async def rss_subscribe(self, ctx: Context, url: str, *, footer: str = ''):
        # noinspection PyBroadException
        # Above comment suppresses Exception Too Broad for PyCharm.
        # Don't see why we have to check for specific exceptions
        try:  # Checks whether the URL is a RSS feed host
            async with self.bot.session.get(url) as resp:
                text = await resp.text()
            if not feedparser.parse(text).entries:
                raise Exception
        except Exception:
            await ctx.send('The host does not seem to send RSS feeds.')
            return
        # Checks whether the incident channel has already subscribed to the URL
        result = self.bot.cursor.execute("SELECT EXISTS(SELECT 1 FROM RssSub WHERE rssChID = ? AND url = ?)",
                                         (ctx.channel.id, url)).fetchone()[0]
        if result:
            await ctx.send(ctx.channel.mention + ' has already subscribed to this URL!')
            return
        # Checks whether this URL exists in the database
        result = self.bot.cursor.execute("SELECT EXISTS(SELECT 1 FROM RssData WHERE url = ?)",
                                         (url,)).fetchone()[0]
        if not result:  # A new RSS URL. Needs to add it to RSS URL list.
            self.bot.cursor.execute("INSERT INTO RssData VALUES (?, '', 0)", (url,))
        # Add subscribe information
        self.bot.cursor.execute("INSERT INTO RssSub VALUES (?, ?, ?)", (ctx.channel.id, url, footer))
        await ctx.send('Subscribed!')

    @rss.command(name='unsubscribe', aliases=['u', 'unsub'])
    @missile.is_channel_owner()
    async def rss_unsubscribe(self, ctx: Context, url: str):
        """Unsubscribe from a RSS URL"""
        # Attempts to delete the subscription record. If the record is deleted, count = 1.
        # If there was no such record, nothing will be deleted, so count = 0
        count = self.bot.cursor.execute('DELETE FROM RssSub WHERE rssChID = ? AND url = ?',
                                        (ctx.channel.id, url)).rowcount
        if count:
            # Checks if any Discord channel still subscribes to that URL
            exist = \
                self.bot.cursor.execute('SELECT EXISTS(SELECT 1 FROM RssSub WHERE url = ?)', (url,)).fetchone()[0]
            if not exist:  # As no one is subscribing, we don't need the URL in the database anymore.
                self.bot.cursor.execute('DELETE FROM RssData WHERE url = ?', (url,))
            await ctx.send('Unsubscribed.')
        else:
            await ctx.send("This channel hasn't subscribed to this URL.")

    @commands.group(invoke_without_command=True)
    async def bbm(self, ctx):
        """Commands for BigBangMods update detector"""
        pass

    @bbm.command(name='subscribe', aliases=['s', 'sub'])
    @missile.is_channel_owner()
    async def bbm_subscribe(self, ctx: Context, addon: int, role: discord.Role = None):
        """Subscribe to a BBM addon"""
        if addon not in self.addon_ids:  # Ensures that the user has inputted a valid addon ID
            await ctx.send('The addon ID must be one of the following: 274058, 306357, 274326')
            return
        # Checks whether the incident channel has already subscribed to the addon.
        if self.bot.cursor.execute("SELECT EXISTS(SELECT 1 FROM BbmAddon WHERE bbmChID = ? AND addonID = ?)",
                                   (ctx.channel.id, addon)).fetchone()[0]:
            await ctx.send(f'{ctx.channel.mention} has already subscribed to this addon!')
            return
        # Checks whether a role has been set in the subscription record before.
        if not self.bot.cursor.execute('SELECT EXISTS(SELECT 1 FROM BbmRole WHERE bbmChID = ?)',
                                       (ctx.channel.id,)).fetchone()[0]:
            # If such record does not exist, this channel has never subscribed to any addons before
            role = role.id if role else None  # The role mention feature is optional
            self.bot.cursor.execute('INSERT INTO BbmRole VALUES (?, ?)', (ctx.channel.id, role))
        # Adds the record to the database
        self.bot.cursor.execute("INSERT INTO BbmAddon VALUES (?, ?)", (ctx.channel.id, addon))
        await ctx.send('Subscribed!')

    @bbm.command(name='unsubscribe', aliases=['u', 'unsub'])
    @missile.is_channel_owner()
    async def bbm_unsubscribe(self, ctx: Context, addon: int):
        """Unsubscribes from a BBM addon."""
        # Attempts to delete the subscription record. If the record is deleted, count = 1.
        # If there was no such record, nothing will be deleted, so count = 0
        count = self.bot.cursor.execute('DELETE FROM BbmAddon WHERE bbmChID = ? AND addonID = ?',
                                        (ctx.channel.id, addon)).rowcount
        if count:
            # Checks whether the Discord channel still subscribes to any addon
            exist = self.bot.cursor.execute('SELECT EXISTS(SELECT 1 FROM BbmAddon WHERE bbmChID = ?)',
                                            (ctx.channel.id,)).fetchone()[0]
            if not exist:  # As the channel doesn't subscribe to any addons anymore, we can remove role info
                self.bot.cursor.execute('DELETE FROM BbmRole WHERE bbmChID = ?', (ctx.channel.id,))
            await ctx.send('Unsubscribed.')
        else:
            await ctx.send("This channel hasn't subscribed to this addon.")

    @bbm.command(aliases=['r'])
    @missile.is_channel_owner()
    async def role(self, ctx: Context, role: discord.Role = None):
        """Modifies the role to be pinged if a BBM update has been detected."""
        role = role.id if role else None
        self.bot.cursor.execute('UPDATE BbmRole SET roleID = ? WHERE bbmChID = ?', (role, ctx.channel.id))
        await ctx.send('Updated!')

    @commands.group(invoke_without_command=True)
    async def yt(self, ctx):
        """Commands for YouTube video detector"""
        pass

    async def get_channel_id(self, query: str):
        """Returns the YouTube channel ID based on query type"""
        async with self.bot.session.get(f'https://www.googleapis.com/youtube/v3/channels?'
                                        f'part=id&fields=items/id&{query}&key={youtube}') as r:
            j: dict = await r.json()
            if j:
                return j['items'][0]['id']
            raise ValueError

    @yt.command(name='subscribe', aliases=['s', 'sub'])
    @missile.is_channel_owner()
    async def yt_subscribe(self, ctx: Context, ch: str):
        """'Subscribe' to a YouTube channel/user"""

        def already_sub(txt: int, yt: str):
            """Checks whether the Discord channel has subscribed to the YouTube channel."""
            return self.bot.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtSub WHERE ytChID = ? AND channelID = ?)',
                                           (txt, yt)).fetchone()[0]

        try:
            # Uses RegEx to ensure that the URL is a valid YouTube User/Channel link
            if not re.search(r"^((https?://)?(www\.)?youtube\.com/)(user/.+|channel/UC.+)", ch):
                raise ValueError
            obj = ch.split('youtube.com/')[1].split('/')

            if obj[0] == 'user':  # The link is a YT user link
                ch = await self.get_channel_id('forUsername=' + obj[1])
                if already_sub(ctx.channel.id, ch):
                    await ctx.send('Already subscribed!')
                    return
                # The YouTube channel ID doesn't exist in the database
                if not self.bot.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtData WHERE channelID = ?)',
                                               (ch,)).fetchone()[0]:
                    # Adds the YouTube channel ID to the database with an invalid video ID so it will trigger later
                    self.bot.cursor.execute("INSERT INTO YtData VALUES (?, ?)", (ch, ch))
            else:  # Link is YT Channel
                ch = obj[1]
                if already_sub(ctx.channel.id, ch):
                    await ctx.send('Already subscribed!')
                    return
                # The YouTube channel ID doesn't exist in the database
                if not self.bot.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtData WHERE channelID = ?)',
                                               (ch,)).fetchone()[0]:
                    await self.get_channel_id('id=' + ch)
                    # Adds the YouTube channel ID to the database with an invalid video ID so it will trigger later
                    self.bot.cursor.execute("INSERT INTO YtData VALUES (?, ?)", (ch, ch))
            self.bot.cursor.execute("INSERT INTO YtSub VALUES (?, ?)", (ctx.channel.id, ch))
            await ctx.send(f'Subscribed to YouTube channel ID **{ch}**')
        except ValueError:
            await ctx.send('Invalid YouTube channel/user link.')

    @yt.command(name='unsubscribe', aliases=['u', 'unsub'])
    @missile.is_channel_owner()
    async def yt_unsubscribe(self, ctx: Context, ch: str):
        """'Unsubscribe' from a YouTube channel/user"""
        try:
            # Uses RegEx to ensure that the URL is a valid YouTube User/Channel link
            if not re.search(r"^((https?://)?(www\.)?youtube\.com/)(user/.+|channel/UC.+)", ch):
                raise ValueError
            obj = ch.split('youtube.com/')[1].split('/')

            if obj[0] == 'user':
                ch = await self.get_channel_id('forUsername=' + obj[1])  # Fetches channel ID by username
            # Attempts to delete the subscription record. If the record is deleted, count = 1.
            # If there was no such record, nothing will be deleted, so count = 0
            count = self.bot.cursor.execute('DELETE FROM YtSub WHERE ytChID = ? AND channelID = ?',
                                            (ctx.channel.id, ch)).rowcount
            if count:
                # Checks whether the YouTube channel is still being subscribed to.
                exists = self.bot.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtSub WHERE channelID  = ?)',
                                                 (ch,)).fetchone()[0]
                if not exists:
                    # No channels still subscribe to this YouTube channel, so we can purge it
                    self.bot.cursor.execute('DELETE FROM YtData WHERE channelID = ?', (ch,))
                await ctx.send('Unsubscribed.')
            else:
                await ctx.send("This channel hasn't subscribed to this YouTube channel/user.")
        except ValueError:
            await ctx.send('Invalid YouTube channel/user link.')
