import asyncio
import re
from random import randint
from time import mktime

import aiohttp
import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import commands

__version__ = '5.0'

from discord.ext.commands import Context

from dimsecret import debug, youtube
from missile import Missile


class Ricciardo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Ricciardo')
        self.new = True
        self.session = aiohttp.ClientSession()
        self.addon_ids = [274058, 306357, 274326]
        self.data = {}
        if debug:  # Debug system uses Windows while production server uses Linux
            asyncio.set_event_loop_policy(  # change to check os in future
                asyncio.WindowsSelectorEventLoopPolicy())  # https://github.com/aio-libs/aiohttp/issues/4324

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')
        if self.new:
            self.new = False
            while True:
                await self.raceline_task()
                self.bot.echo.db.commit()
                await asyncio.sleep(600)

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.new = True

    async def raceline_task(self):
        bbm_futures = {}
        for addon_id in self.addon_ids:
            bbm_futures[addon_id] = self.bot.loop.create_task(self.bbm_process(addon_id))
        resultless_futures = []
        rss_data = self.bot.echo.cursor.execute('SELECT * FROM RssData').fetchall()
        for index, row in enumerate(rss_data):
            resultless_futures.append(self.bot.loop.create_task(self.rss_process(index + 1, row)))
        yt_data = self.bot.echo.cursor.execute('SELECT * FROM YtData').fetchall()
        for row in yt_data:
            resultless_futures.append(self.bot.loop.create_task(self.yt_process(row)))
        bbm_role = self.bot.echo.cursor.execute('SELECT * FROM BbmRole').fetchall()
        await asyncio.wait(bbm_futures.values())
        for row in bbm_role:
            bbm_addon = self.bot.echo.cursor.execute('SELECT addonID FROM BbmAddon WHERE bbmChID = ?',
                                                     (row[0],)).fetchall()
            default_msg = ''
            if row['roleID']:
                default_msg = f"<@&{row['roleID']}>\n"
            msg = default_msg
            for addon in bbm_addon:
                msg += bbm_futures[addon[0]].result()
            if msg != default_msg:
                await self.bot.get_channel(row[0]).send(msg)
        await asyncio.wait(resultless_futures)
        self.logger.debug('Synced')

    async def rss_process(self, rowid, row):
        cursor = self.bot.echo.get_cursor()
        self.logger.info(f"{rowid}: Checking RSS...")
        async with self.session.get(row['url']) as response:
            self.logger.debug(f"{rowid}: Fetching response...")
            text = await response.text()
        self.logger.debug(f"{rowid}: Parsing response...")
        feed = feedparser.parse(text).entries[0]
        pubtime = mktime(feed.published_parsed)
        if row['newstitle'] != feed.title and pubtime > row['time']:
            self.logger.info(f'{rowid}: Detected news: {feed.title}  Old: {row["newstitle"]}')
            content = BeautifulSoup(feed.description, 'html.parser')
            rss_sub = cursor.execute('SELECT rssChID, footer FROM RssSub WHERE url = ?',
                                     (row['url'],)).fetchall()
            description = (content.get_text()[:497] + '...') if len(content.get_text()) > 500 else content.get_text()
            emb = discord.Embed(title=feed.title, description=description, url=feed.link)
            emb.colour = discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
            for row in rss_sub:
                # TODO: Create a class called RSSEmb which subclasses Embed in order to satisfy NEA
                local_emb = emb.copy()
                channel = self.bot.get_channel(row['rssChID'])
                local_emb.set_footer(text=f"{row['footer']} | {feed.published}")
                await channel.send(embed=local_emb)
            self.logger.info(f"{rowid}: Sent Discord")
            cursor.execute('UPDATE RssData SET newstitle = ?, time = ? WHERE ROWID = ?',
                           (feed.title, pubtime, rowid))
        self.logger.info(f"{rowid}: Done")

    async def bbm_process(self, addon_id: int):
        cursor = self.bot.echo.get_cursor()
        message = ''
        records = cursor.execute('SELECT title FROM BbmData WHERE addonID = ?',
                                 (addon_id,)).fetchall()
        self.logger.info(f"Checking BBM {addon_id}...")
        async with self.session.get(f'https://addons-ecs.forgesvc.net/api/v2/addon/{addon_id}') as response:
            self.logger.debug(f'Fetching BBM {addon_id}...')
            addon = await response.json()
        self.logger.debug(f'Parsing BBM {addon_id}...')
        new = addon['latestFiles'].copy()
        for latest_file in addon['latestFiles']:
            for rec in records:
                if latest_file['displayName'] == rec[0]:
                    records.remove(rec)
                    new.remove(latest_file)
                    break
        for i, latest_file in enumerate(new):
            async with self.session.get(
                    f"https://addons-ecs.forgesvc.net/api/v2/addon/{addon_id}/file/{latest_file['id']}/changelog") \
                    as response:
                change_log = await response.text()
            change_log = BeautifulSoup(change_log, 'html.parser')
            game_version = latest_file['gameVersion'][0] if latest_file['gameVersion'] else None
            message += f"An update of **{addon['name']}** is now available!\n" \
                       f"__**{latest_file['displayName']}** for **{game_version}**__\n" \
                       f"{change_log.get_text()}\n\n"
            cursor.execute('UPDATE BbmData SET title = ? WHERE title = ?',
                           (latest_file['displayName'], records[i][0]))
        return message

    async def yt_process(self, row):
        self.logger.info(f"Checking YouTube channel ID {row['channelID']}")
        async with self.session.get('https://www.googleapis.com/youtube/v3/activities?part=snippet,'
                                    f"contentDetails&channelId={row['channelID']}&maxResults=1&key={youtube}") \
                as response:
            activities = await response.json()
            if activities['items'][0]['snippet']['type'] == 'upload':
                video_id = activities['items'][0]['contentDetails']['upload']['videoId']
                if row['videoID'] != video_id:
                    self.logger.debug('New YT video detected for channel ID ' + row['channelID'])
                    yt_sub = self.bot.echo.cursor.execute('SELECT ytChID from YtSub WHERE channelID = ?',
                                                          (row['channelID'],)).fetchall()
                    for sub in yt_sub:
                        ch = self.bot.get_channel(sub[0])
                        await ch.send("http://youtube.com/watch?v=" + video_id)
                    self.bot.echo.cursor.execute('UPDATE YtData SET videoID = ? WHERE channelID = ?',
                                                 (video_id, row['channelID']))

    @commands.group(invoke_without_command=True)
    async def rss(self, ctx):
        pass

    @rss.command(name='subscribe', aliases=['s', 'sub'])
    @Missile.is_channel_owner_cmd_check()
    async def rss_subscribe(self, ctx: Context, url: str, *, footer: str = ''):
        # noinspection PyBroadException
        # Above comment suppresses Exception Too Broad for PyCharm.
        # Don't see why we have to check for specific exceptions
        try:
            async with self.session.get(url) as resp:
                text = await resp.text()
            if not feedparser.parse(text).entries:
                raise Exception
        except Exception:
            await ctx.send('The host does not seem to send RSS feeds.')
            return

        result = self.bot.echo.cursor.execute("SELECT EXISTS(SELECT 1 FROM RssSub WHERE rssChID = ? AND url = ?)",
                                              (ctx.channel.id, url)).fetchone()[0]
        if result:
            await ctx.send(ctx.channel.mention + ' has already subscribed to this URL!')
            return
        result = self.bot.echo.cursor.execute("SELECT EXISTS(SELECT 1 FROM RssData WHERE url = ?)",
                                              (url,)).fetchone()[0]
        if not result:
            self.bot.echo.cursor.execute("INSERT INTO RssData VALUES (?, '', 0)", (url,))
        self.bot.echo.cursor.execute("INSERT INTO RssSub VALUES (?, ?, ?)", (ctx.channel.id, url, footer))
        await ctx.send('Subscribed!')

    @rss.command(name='unsubscribe', aliases=['u', 'unsub'])
    @Missile.is_channel_owner_cmd_check()
    async def rss_unsubscribe(self, ctx: Context, url: str):
        count = self.bot.echo.cursor.execute('DELETE FROM RssSub WHERE rssChID = ? AND url = ?',
                                             (ctx.channel.id, url)).rowcount
        if count:
            exist = \
                self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM RssSub WHERE url = ?)', (url,)).fetchone()[0]
            if not exist:
                self.bot.echo.cursor.execute('DELETE FROM RssData WHERE url = ?', (url,))
            await ctx.send('Unsubscribed.')
        else:
            await ctx.send("This channel hasn't subscribed to this URL.")

    @commands.group(invoke_without_command=True)
    async def bbm(self, ctx):
        pass

    @bbm.command(name='subscribe', aliases=['s', 'sub'])
    @Missile.is_channel_owner_cmd_check()
    async def bbm_subscribe(self, ctx: Context, addon: int, role: discord.Role = None):
        if addon not in self.addon_ids:
            await ctx.send('The addon ID must be one of the following: 274058, 306357, 274326')
            return
        if self.bot.echo.cursor.execute("SELECT EXISTS(SELECT 1 FROM BbmAddon WHERE bbmChID = ? AND addonID = ?)",
                                        (ctx.channel.id, addon)).fetchone()[0]:
            await ctx.send(f'{ctx.channel.mention} has already subscribed to this addon!')
            return
        if not self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM BbmRole WHERE bbmChID = ?)',
                                            (ctx.channel.id,)).fetchone()[0]:
            role = role.id if role else None
            self.bot.echo.cursor.execute('INSERT INTO BbmRole VALUES (?, ?)', (ctx.channel.id, role))
        self.bot.echo.cursor.execute("INSERT INTO BbmAddon VALUES (?, ?)", (ctx.channel.id, addon))
        await ctx.send('Subscribed!')

    @bbm.command(name='unsubscribe', aliases=['u', 'unsub'])
    @Missile.is_channel_owner_cmd_check()
    async def bbm_unsubscribe(self, ctx: Context, addon: int):
        count = self.bot.echo.cursor.execute('DELETE FROM BbmAddon WHERE bbmChID = ? AND addonID = ?',
                                             (ctx.channel.id, addon)).rowcount
        if count:
            exist = self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM BbmAddon WHERE bbmChID = ?)',
                                                 (ctx.channel.id,)).fetchone()[0]
            if not exist:
                self.bot.echo.cursor.execute('DELETE FROM BbmRole WHERE bbmChID = ?', (ctx.channel.id,))
            await ctx.send('Unsubscribed.')
        else:
            await ctx.send("This channel hasn't subscribed to this addon.")

    @bbm.command(aliases=['r'])
    @Missile.is_channel_owner_cmd_check()
    async def role(self, ctx: Context, role: discord.Role = None):
        role = role.id if role else None
        self.bot.echo.cursor.execute('UPDATE BbmRole SET roleID = ? WHERE bbmChID = ?', (role, ctx.channel.id))
        await ctx.send('Updated!')

    @commands.group(invoke_without_command=True)
    async def yt(self, ctx):
        pass

    async def get_channel_id(self, query: str):
        async with self.session.get(f'https://www.googleapis.com/youtube/v3/channels?'
                                    f'part=id&fields=items/id&{query}&key={youtube}') as r:
            j: dict = await r.json()
            if j:
                return j['items'][0]['id']
            raise ValueError

    @yt.command(name='subscribe', aliases=['s', 'sub'])
    @Missile.is_channel_owner_cmd_check()
    async def yt_subscribe(self, ctx: Context, ch: str):
        def already_sub(txt: int, yt: str):
            return self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtSub WHERE ytChID = ? AND channelID = ?)',
                                                (txt, yt)).fetchone()[0]

        try:
            if not re.search(r"^((https?://)?(www\.)?youtube\.com/)(user/.+|channel/UC.+)", ch):
                raise ValueError
            obj = ch.split('youtube.com/')[1].split('/')

            if obj[0] == 'user':
                ch = await self.get_channel_id('forUsername=' + obj[1])
                if already_sub(ctx.channel.id, ch):
                    await ctx.send('Already subscribed!')
                    return
                if not self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtData WHERE channelID = ?)',
                                                    (ch,)).fetchone()[0]:
                    self.bot.echo.cursor.execute("INSERT INTO YtData VALUES (?, ?)", (ch, ch))
            else:
                ch = obj[1]
                if already_sub(ctx.channel.id, ch):
                    await ctx.send('Already subscribed!')
                    return
                if not self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtData WHERE channelID = ?)',
                                                    (ch,)).fetchone()[0]:
                    await self.get_channel_id('id=' + ch)
                    self.bot.echo.cursor.execute("INSERT INTO YtData VALUES (?, ?)", (ch, ch))
            self.bot.echo.cursor.execute("INSERT INTO YtSub VALUES (?, ?)", (ctx.channel.id, ch))
            await ctx.send(f'Subscribed to YouTube channel ID **{ch}**')
        except ValueError:
            await ctx.send('Invalid YouTube channel/user link.')

    @yt.command(name='unsubscribe', aliases=['u', 'unsub'])
    @Missile.is_channel_owner_cmd_check()
    async def yt_unsubscribe(self, ctx: Context, ch: str):
        try:
            if not re.search(r"^((https?://)?(www\.)?youtube\.com/)(user/.+|channel/UC.+)", ch):
                raise ValueError
            obj = ch.split('youtube.com/')[1].split('/')

            if obj[0] == 'user':
                ch = await self.get_channel_id('forUsername=' + obj[1])

            count = self.bot.echo.cursor.execute('DELETE FROM YtSub WHERE ytChID = ? AND channelID = ?',
                                                 (ctx.channel.id, ch)).rowcount
            if count:
                exists = self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM YtSub WHERE channelID  = ?)',
                                                      (ch,)).fetchone()[0]
                if not exists:
                    self.bot.echo.cursor.execute('DELETE FROM YtData WHERE channelID = ?', (ch,))
                await ctx.send('Unsubscribed.')
            else:
                await ctx.send("This channel hasn't subscribed to this YouTube channel/user.")
        except ValueError:
            await ctx.send('Invalid YouTube channel/user link.')
