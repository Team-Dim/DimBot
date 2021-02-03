import asyncio
import json
from random import randint
from time import mktime

import aiohttp
import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import commands

__version__ = '4.3'

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
            with open('data.json', 'r') as f:
                self.data = json.load(f)
            while True:
                await self.raceline_task()
                await asyncio.sleep(600)

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.new = True

    async def raceline_task(self):
        bbm = {}
        for addon_id in self.addon_ids:
            bbm[addon_id] = self.bot.loop.create_task(self.bbm_process(addon_id))
        rss_data = self.bot.echo.cursor.execute('SELECT * FROM RssData').fetchall()
        resultless_futures = []
        for index, row in enumerate(rss_data):
            resultless_futures.append(self.bot.loop.create_task(self.rss_process(index + 1, row)))
        resultless_futures.append(self.bot.loop.create_task(self.yt()))
        bbm_role = self.bot.echo.cursor.execute('SELECT * FROM BbmRole').fetchall()
        await asyncio.wait(resultless_futures)
        for row in bbm_role:
            bbm_addon = self.bot.echo.cursor.execute('SELECT addonID FROM BbmAddon WHERE bbmChID = ?',
                                                     (row[0],)).fetchall()
            default_msg = ''
            if row['roleID']:
                default_msg = f"<@&{row['roleID']}>\n"
            msg = default_msg
            for addon in bbm_addon:
                msg += bbm[addon[0]].result()
            if msg != default_msg:
                await self.bot.get_channel(row[0]).send(msg)
        self.logger.debug('Synced pool')
        with open('data.json', 'w') as f:
            json.dump(self.data, f)
        self.bot.echo.db.commit()

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

    async def yt(self):
        self.logger.info('Checking YT')
        async with self.session.get('https://www.googleapis.com/youtube/v3/activities?part=snippet,'
                                    'contentDetails&channelId=UCTuGoJ-MoQuSYVgtmJTa3-w&maxResults=1&key=' + youtube) \
                as response:
            activities = await response.json()
            if activities['items'][0]['snippet']['type'] == 'upload':
                video_id = activities['items'][0]['contentDetails']['upload']['videoId']
                if self.data['YT'] != video_id:
                    self.logger.debug('New YT video detected')
                    await self.bot.missile.announcement.send("http://youtube.com/watch?v=" + video_id)
                    self.data['YT'] = video_id

    @commands.group(invoke_without_command=True)
    async def rss(self):
        pass

    @rss.command(name='subscribe', aliases=['s', 'sub'])
    @commands.check(Missile.is_owner)
    async def rss_subscribe(self, ctx, ch: discord.TextChannel, url: str, *, footer: str = ''):
        from aiohttp import ClientConnectorError
        try:
            async with self.session.get(url) as resp:
                text = await resp.text()
            if not feedparser.parse(text).entries:
                raise ValueError
        except ClientConnectorError or ValueError:
            await ctx.send('The host does not seem to send RSS feeds.')
            return

        result = self.bot.echo.cursor.execute("SELECT EXISTS(SELECT 1 FROM RssSub WHERE rssChID = ? AND url = ?)",
                                              (ch.id, url)).fetchone()[0]
        if result:
            await ctx.send(ch.mention + ' has already subscribed to this URL!')
            return
        result = self.bot.echo.cursor.execute("SELECT EXISTS(SELECT 1 FROM RssData WHERE url = ?)",
                                              (url,)).fetchone()[0]
        if not result:
            self.bot.echo.cursor.execute("INSERT INTO RssData VALUES (?, '', 0)", (url,))
        self.bot.echo.cursor.execute("INSERT INTO RssSub VALUES (?, ?, ?)", (ch.id, url, footer))
        self.bot.echo.db.commit()
        await ctx.send('Subscribed!')

    @commands.group(invoke_without_command=True)
    async def bbm(self):
        pass

    @bbm.command(name='subscribe', aliases=['s', 'sub'])
    @commands.check(Missile.is_owner)
    async def bbm_subscribe(self, ctx: Context, ch: discord.TextChannel, addon: int, role: discord.Role = None):
        if addon not in self.addon_ids:
            await ctx.send('the addon ID must be one of the following: 274058, 306357, 274326')
            return
        result = self.bot.echo.cursor.execute("SELECT EXISTS(SELECT 1 FROM BbmAddon WHERE bbmChID = ? AND addonID = ?)",
                                              (ch.id, addon)).fetchone()[0]
        if result:
            await ctx.send(f'{ch.mention} has already subscribed to this addon!')
            return
        result = self.bot.echo.cursor.execute('SELECT EXISTS(SELECT 1 FROM BbmRole WHERE bbmChID = ?)', (ch.id,)).fetchone()[0]
        if not result:
            role = role.id if role else None
            self.bot.echo.cursor.execute('INSERT INTO BbmRole VALUES (?, ?)', (ch.id, role))
        self.bot.echo.cursor.execute("INSERT INTO BbmAddon VALUES (?, ?)", (ch.id, addon))
        self.bot.echo.db.commit()
        await ctx.send('Subscribed!')

    @bbm.command(aliases=['r'])
    @commands.check(Missile.is_owner)
    async def role(self, ctx: Context, role: discord.Role = None):
        role = role.id if role else None
        self.bot.echo.cursor.execute('UPDATE BbmRole SET roleID = ? WHERE bbmChID = ?', (role, ctx.channel.id))
        self.bot.echo.db.commit()
        await ctx.send('Updated!')

