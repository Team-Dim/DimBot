import asyncio
import re
from random import randint
from time import mktime

import aiohttp
import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import commands
from discord.ext.commands import Context

from dimsecret import debug, youtube
from missile import Missile


class Ricciardo(commands.Cog):
    """Relaying RSS, BBM and YouTube feeds to discord channels.
    Version 5.0"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Ricciardo')
        self.session = aiohttp.ClientSession()  # A master Session for all requests within this class
        self.addon_ids = [274058, 306357, 274326]  # List of addon IDs for BBM operations
        self.data = {}
        if debug:  # Debug system uses Windows while production server uses Linux
            asyncio.set_event_loop_policy(  # change to check os in future
                asyncio.WindowsSelectorEventLoopPolicy())  # https://github.com/aio-libs/aiohttp/issues/4324

    @commands.Cog.listener()
    async def on_ready(self):
        while True:
            # Dispatch tasks every 10 minutes
            self.bot.loop.create_task(self.raceline_task())
            await asyncio.sleep(600)

    @commands.Cog.listener()
    async def on_guild_remove(self, guild: discord.Guild):
        """When the bot leaves a server, remove subscriptions related to the server."""
        ch_ids = [ch.id for ch in guild.text_channels]
        q_marks = ','.join(['?'] * len(ch_ids))
        self.bot.echo.cursor.execute(f"DELETE FROM BbmRole WHERE bbmChID IN ({q_marks})", (ch_ids,))
        self.bot.echo.cursor.execute(f"DELETE FROM BbmAddon WHERE bbmChID IN ({q_marks})", (ch_ids,))
        self.bot.echo.cursor.execute(f"DELETE FROM RssSub WHERE rssChID IN ({q_marks})", (ch_ids,))
        self.bot.echo.cursor.execute(f"DELETE FROM RssData WHERE url NOT IN (SELECT url FROM RssSub)")
        self.bot.echo.cursor.execute(f"DELETE FROM YtSub WHERE ytChID IN ({q_marks})", (ch_ids,))
        self.bot.echo.cursor.execute("DELETE FROM YtData WHERE channelID NOT IN (SELECT channelID FROM YtSub)")

    async def raceline_task(self):
        """Dispatches RSS, BBM and YouTube update detectors"""
        bbm_futures = {}
        for addon_id in self.addon_ids:
            bbm_futures[addon_id] = self.bot.loop.create_task(self.bbm_process(addon_id))  # Dispatch BBM tasks
        resultless_futures = []
        rss_data = self.bot.echo.cursor.execute('SELECT * FROM RssData').fetchall()
        for index, row in enumerate(rss_data):
            # Dispatches RSS tasks
            resultless_futures.append(self.bot.loop.create_task(self.rss_process(index + 1, row)))
        yt_data = self.bot.echo.cursor.execute('SELECT * FROM YtData').fetchall()  # Fetches YouTube data from db
        for row in yt_data:
            # Dispatches YouTube tasks
            resultless_futures.append(self.bot.loop.create_task(self.yt_process(row)))

        # The tasks are running. Now prepares when all BBM tasks return.
        # Fetches role subscriptions for BBM
        bbm_role = self.bot.echo.cursor.execute('SELECT * FROM BbmRole').fetchall()
        await asyncio.wait(bbm_futures.values())  # Wait for all BBM tasks to return
        for row in bbm_role:
            # Fetch addons that the text channel has subscribed
            bbm_addon = self.bot.echo.cursor.execute('SELECT addonID FROM BbmAddon WHERE bbmChID = ?',
                                                     (row[0],)).fetchall()
            default_msg = ''
            if row['roleID']:  # If the database contains a role in BBMRole, Ping it
                default_msg = f"<@&{row['roleID']}>\n"
            msg = default_msg
            for addon in bbm_addon:
                msg += bbm_futures[addon[0]].result()  # Adds actual BBM update message
            if msg != default_msg:  # Only send if there are BBM updates
                self.bot.loop.create_task(self.bot.get_channel(row[0]).send(msg))
        await asyncio.wait(resultless_futures)  # Wait for all tasks to be finished
        self.logger.debug('Synced')
        self.bot.echo.db.commit()

    async def rss_process(self, rowid, row):
        """The main algorithm for RSS feed detector"""
        cursor = self.bot.echo.get_cursor()  # Each thread requires an instance of cursor
        self.logger.info(f"{rowid}: Checking RSS...")
        async with self.session.get(row['url']) as response:  # Sends a GET request to the URL
            self.logger.debug(f"{rowid}: Fetching response...")
            text = await response.text()
        self.logger.debug(f"{rowid}: Parsing response...")
        feed = feedparser.parse(text).entries[0]  # Converts RSS response to library objects and read the first entry
        pubtime = mktime(feed.published_parsed)  # Converts the feed's publish timestamp to an integer

        # A feed with a new title and the publish timestamp is newer than database's record
        if row['newstitle'] != feed.title and pubtime > row['time']:
            self.logger.info(f'{rowid}: Detected news: {feed.title}  Old: {row["newstitle"]}')
            content = BeautifulSoup(feed.description, 'html.parser')  # HTML Parser for extracting RSS feed content
            rss_sub = cursor.execute('SELECT rssChID, footer FROM RssSub WHERE url = ?',
                                     (row['url'],)).fetchall()  # Fetch channels that subscribed to this RSS URL
            # Limits the content size to prevent spam
            description = (content.get_text()[:497] + '...') if len(content.get_text()) > 500 else content.get_text()
            # Constructs base Embed object
            emb = discord.Embed(title=feed.title, description=description, url=feed.link, color=Missile.random_rgb())
            for row in rss_sub:
                local_emb = emb.copy()
                channel = self.bot.get_channel(row['rssChID'])
                local_emb.set_footer(text=f"{row['footer']} | {feed.published}")  # Adds channel-specific footer
                self.bot.loop.create_task(channel.send(embed=local_emb))
            self.logger.info(f"{rowid}: Sent Discord")
            cursor.execute('UPDATE RssData SET newstitle = ?, time = ? WHERE ROWID = ?',
                           (feed.title, pubtime, rowid))  # Updates the database with the new feed
        self.logger.info(f"{rowid}: Done")

    async def bbm_process(self, addon_id: int):
        """The main algorithm for the BBM update detector"""
        cursor = self.bot.echo.get_cursor()  # Each thread requires an instance of cursor
        message = ''
        records = cursor.execute('SELECT title FROM BbmData WHERE addonID = ?',
                                 (addon_id,)).fetchall()  # Read BBM records from the database
        self.logger.info(f"Checking BBM {addon_id}...")
        # Check for BBM updates
        async with self.session.get(f'https://addons-ecs.forgesvc.net/api/v2/addon/{addon_id}') as response:
            self.logger.debug(f'Fetching BBM {addon_id}...')
            addon = await response.json()
        self.logger.debug(f'Parsing BBM {addon_id}...')
        new = addon['latestFiles'].copy()  # Copies a list of BBM file names from the endpoint.
        for latest_file in addon['latestFiles']:  # For each addon ID
            for rec in records:  # Finds a database record with that addon ID
                # If the file name from endpoint is same as the record, that means there is no update for that addon.
                if latest_file['displayName'] == rec[0]:
                    records.remove(rec)
                    new.remove(latest_file)
                    break
        # All that remains is addons that have updates
        for i, latest_file in enumerate(new):
            # Fetch the changelog of that addon update
            async with self.session.get(
                    f"https://addons-ecs.forgesvc.net/api/v2/addon/{addon_id}/file/{latest_file['id']}/changelog") \
                    as response:
                change_log = await response.text()
            change_log = BeautifulSoup(change_log, 'html.parser')  # HTML Parser
            # Due to how inconsistent the endpoint is, sometimes there is literally missing information. Smh
            game_version = latest_file['gameVersion'][0] if latest_file['gameVersion'] else None
            # Adds update info to the base message
            message += f"An update of **{addon['name']}** is now available!\n" \
                       f"__**{latest_file['displayName']}** for **{game_version}**__\n" \
                       f"{change_log.get_text()}\n\n"
            cursor.execute('UPDATE BbmData SET title = ? WHERE title = ?',
                           (latest_file['displayName'], records[i][0]))  # Updates the database
        return message

    async def yt_process(self, row):
        """The main algorithm for detecting YouTube videos"""
        self.logger.info(f"Checking YouTube channel ID {row['channelID']}")
        # Fetch the channel's latest activity
        async with self.session.get('https://www.googleapis.com/youtube/v3/activities?part=snippet,'
                                    f"contentDetails&channelId={row['channelID']}&maxResults=1&key={youtube}") \
                as response:
            activities = await response.json()
            if activities['items'][0]['snippet']['type'] == 'upload':  # The latest activity type is upload
                video_id = activities['items'][0]['contentDetails']['upload']['videoId']
                if row['videoID'] != video_id:  # New video ID detected
                    self.logger.debug('New YT video detected for channel ID ' + row['channelID'])
                    # Fetches Discord channels that have subscribed to that YouTube channel
                    yt_sub = self.bot.echo.cursor.execute('SELECT ytChID from YtSub WHERE channelID = ?',
                                                          (row['channelID'],)).fetchall()
                    for sub in yt_sub:
                        ch = self.bot.get_channel(sub[0])
                        # Notifies the Discord channel that a new video has been found
                        self.bot.loop.create_task(ch.send("http://youtube.com/watch?v=" + video_id))
                    # Update database
                    self.bot.echo.cursor.execute('UPDATE YtData SET videoID = ? WHERE channelID = ?',
                                                 (video_id, row['channelID']))

    @commands.group(invoke_without_command=True)
    async def rss(self, ctx):
        """Commands for RSS feed update detector"""
        pass

    @rss.command(name='subscribe', aliases=['s', 'sub'])
    @Missile.is_channel_owner_cmd_check()
    async def rss_subscribe(self, ctx: Context, url: str, *, footer: str = ''):
        # noinspection PyBroadException
        # Above comment suppresses Exception Too Broad for PyCharm.
        # Don't see why we have to check for specific exceptions
        try:  # Checks whether the URL is a RSS feed host
            async with self.session.get(url) as resp:
                text = await resp.text()
            if not feedparser.parse(text).entries:
                raise Exception
        except Exception:
            await ctx.send('The host does not seem to send RSS feeds.')
            return
        # Checks whether the incident channel has already subscribed to the URL
        result = self.bot.echo.cursor.execute("SELECT EXISTS(SELECT 1 FROM RssSub WHERE rssChID = ? AND url = ?)",
                                              (ctx.channel.id, url)).fetchone()[0]
        if result:
            await ctx.send(ctx.channel.mention + ' has already subscribed to this URL!')
            return
        # Checks whether this URL exists in the database
        result = self.bot.echo.cursor.execute("SELECT EXISTS(SELECT 1 FROM RssData WHERE url = ?)",
                                              (url,)).fetchone()[0]
        if not result:  # A new RSS URL. Needs to add it to RSS URL list.
            self.bot.echo.cursor.execute("INSERT INTO RssData VALUES (?, '', 0)", (url,))
        # Add subscribe information
        self.bot.echo.cursor.execute("INSERT INTO RssSub VALUES (?, ?, ?)", (ctx.channel.id, url, footer))
        await ctx.send('Subscribed!')

    @rss.command(name='unsubscribe', aliases=['u', 'unsub'])
    @Missile.is_channel_owner_cmd_check()
    async def rss_unsubscribe(self, ctx: Context, url: str):
        """Unsubscribe from a RSS URL"""
        # Attempts to delete the subscription record. If the record is deleted, count = 1.
        # If there was no such record, nothing will be deleted, so count = 0
        count = self.bot.echo.cursor.execute('DELETE FROM RssSub WHERE rssChID = ? AND url = ?',
                                             (ctx.channel.id, url)).rowcount
        if count:
            # Checks if any Discord channel still subscribes to that URL
            exist = \
                self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM RssSub WHERE url = ?)', (url,)).fetchone()[0]
            if not exist:  # As no one is subscribing, we don't need the URL in the database anymore.
                self.bot.echo.cursor.execute('DELETE FROM RssData WHERE url = ?', (url,))
            await ctx.send('Unsubscribed.')
        else:
            await ctx.send("This channel hasn't subscribed to this URL.")

    @commands.group(invoke_without_command=True)
    async def bbm(self, ctx):
        """Commands for BigBangMods update detector"""
        pass

    @bbm.command(name='subscribe', aliases=['s', 'sub'])
    @Missile.is_channel_owner_cmd_check()
    async def bbm_subscribe(self, ctx: Context, addon: int, role: discord.Role = None):
        """Subscribe to a BBM addon"""
        if addon not in self.addon_ids:  # Ensures that the user has inputted a valid addon ID
            await ctx.send('The addon ID must be one of the following: 274058, 306357, 274326')
            return
        # Checks whether the incident channel has already subscribed to the addon.
        if self.bot.echo.cursor.execute("SELECT EXISTS(SELECT 1 FROM BbmAddon WHERE bbmChID = ? AND addonID = ?)",
                                        (ctx.channel.id, addon)).fetchone()[0]:
            await ctx.send(f'{ctx.channel.mention} has already subscribed to this addon!')
            return
        # Checks whether a role has been set in the subscription record before.
        if not self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM BbmRole WHERE bbmChID = ?)',
                                            (ctx.channel.id,)).fetchone()[0]:
            # If such record does not exist, this channel has never subscribed to any addons before
            role = role.id if role else None  # The role mention feature is optional
            self.bot.echo.cursor.execute('INSERT INTO BbmRole VALUES (?, ?)', (ctx.channel.id, role))
        # Adds the record to the database
        self.bot.echo.cursor.execute("INSERT INTO BbmAddon VALUES (?, ?)", (ctx.channel.id, addon))
        await ctx.send('Subscribed!')

    @bbm.command(name='unsubscribe', aliases=['u', 'unsub'])
    @Missile.is_channel_owner_cmd_check()
    async def bbm_unsubscribe(self, ctx: Context, addon: int):
        """Unsubscribes from a BBM addon."""
        # Attempts to delete the subscription record. If the record is deleted, count = 1.
        # If there was no such record, nothing will be deleted, so count = 0
        count = self.bot.echo.cursor.execute('DELETE FROM BbmAddon WHERE bbmChID = ? AND addonID = ?',
                                             (ctx.channel.id, addon)).rowcount
        if count:
            # Checks whether the Discord channel still subscribes to any addon
            exist = self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM BbmAddon WHERE bbmChID = ?)',
                                                 (ctx.channel.id,)).fetchone()[0]
            if not exist:  # As the channel doesn't subscribe to any addons anymore, we can remove role info
                self.bot.echo.cursor.execute('DELETE FROM BbmRole WHERE bbmChID = ?', (ctx.channel.id,))
            await ctx.send('Unsubscribed.')
        else:
            await ctx.send("This channel hasn't subscribed to this addon.")

    @bbm.command(aliases=['r'])
    @Missile.is_channel_owner_cmd_check()
    async def role(self, ctx: Context, role: discord.Role = None):
        """Modifies the role to be pinged if a BBM update has been detected."""
        role = role.id if role else None
        self.bot.echo.cursor.execute('UPDATE BbmRole SET roleID = ? WHERE bbmChID = ?', (role, ctx.channel.id))
        await ctx.send('Updated!')

    @commands.group(invoke_without_command=True)
    async def yt(self, ctx):
        """Commands for YouTube video detector"""
        pass

    async def get_channel_id(self, query: str):
        """Returns the YouTube channel ID based on query type"""
        async with self.session.get(f'https://www.googleapis.com/youtube/v3/channels?'
                                    f'part=id&fields=items/id&{query}&key={youtube}') as r:
            j: dict = await r.json()
            if j:
                return j['items'][0]['id']
            raise ValueError

    @yt.command(name='subscribe', aliases=['s', 'sub'])
    @Missile.is_channel_owner_cmd_check()
    async def yt_subscribe(self, ctx: Context, ch: str):
        """'Subscribe' to a YouTube channel/user"""
        def already_sub(txt: int, yt: str):
            """Checks whether the Discord channel has subscribed to the YouTube channel."""
            return self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtSub WHERE ytChID = ? AND channelID = ?)',
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
                if not self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtData WHERE channelID = ?)',
                                                    (ch,)).fetchone()[0]:
                    # Adds the YouTube channel ID to the database with an invalid video ID so it will trigger later
                    self.bot.echo.cursor.execute("INSERT INTO YtData VALUES (?, ?)", (ch, ch))
            else:  # Link is YT Channel
                ch = obj[1]
                if already_sub(ctx.channel.id, ch):
                    await ctx.send('Already subscribed!')
                    return
                # The YouTube channel ID doesn't exist in the database
                if not self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtData WHERE channelID = ?)',
                                                    (ch,)).fetchone()[0]:
                    await self.get_channel_id('id=' + ch)
                    # Adds the YouTube channel ID to the database with an invalid video ID so it will trigger later
                    self.bot.echo.cursor.execute("INSERT INTO YtData VALUES (?, ?)", (ch, ch))
            self.bot.echo.cursor.execute("INSERT INTO YtSub VALUES (?, ?)", (ctx.channel.id, ch))
            await ctx.send(f'Subscribed to YouTube channel ID **{ch}**')
        except ValueError:
            await ctx.send('Invalid YouTube channel/user link.')

    @yt.command(name='unsubscribe', aliases=['u', 'unsub'])
    @Missile.is_channel_owner_cmd_check()
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
            count = self.bot.echo.cursor.execute('DELETE FROM YtSub WHERE ytChID = ? AND channelID = ?',
                                                 (ctx.channel.id, ch)).rowcount
            if count:
                # Checks whether the YouTube channel is still being subscribed to.
                exists = self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtSub WHERE channelID  = ?)',
                                                      (ch,)).fetchone()[0]
                if not exists:
                    # No channels still subscribe to this YouTube channel, so we can purge it
                    self.bot.echo.cursor.execute('DELETE FROM YtData WHERE channelID = ?', (ch,))
                await ctx.send('Unsubscribed.')
            else:
                await ctx.send("This channel hasn't subscribed to this YouTube channel/user.")
        except ValueError:
            await ctx.send('Invalid YouTube channel/user link.')
