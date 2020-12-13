import asyncio
import concurrent
import json
from concurrent.futures.thread import ThreadPoolExecutor
from random import randint

import aiohttp
import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import commands

__version__ = '4.0.3'

from dimsecret import debug, youtube
from missile import Missile


class Ricciardo(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Ricciardo')
        self.new = True
        self.pool = ThreadPoolExecutor()
        self.data = dict()
        if debug:  # Debug system uses Windows while production server uses Linux
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())  # https://github.com/aio-libs/aiohttp/issues/4324

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')
        if self.new:
            self.new = False
            with open('data.json', 'r') as f:
                self.data = json.load(f)
            await self.raceline_task()

    @commands.Cog.listener()
    async def on_disconnect(self):
        self.new = True

    async def raceline_task(self):
        while True:
            rss_data = self.bot.echo.cursor.execute('SELECT * FROM RssData').fetchall()
            rss_futures = []
            for index, row in enumerate(rss_data):
                rss_futures.append(self.pool.submit(self.rss_process, index, row))
            message = default_msg = '' if debug else '<@&664210105318768661> '
            bbm_futures = [self.pool.submit(self.bbm_process, addon_id) for addon_id in self.data['BBM'].keys()]
            concurrent.futures.wait([self.pool.submit(self.yt_process)])
            concurrent.futures.wait(rss_futures)
            concurrent.futures.wait(bbm_futures)
            for future in rss_futures:
                if future.result():
                    self.bot.echo.cursor.execute('UPDATE RssData SET newstitle = ? WHERE url = ?',
                                                 (future.result()[0], rss_data[future.result()[1]]['url']))
            for future in bbm_futures:
                message += future.result()
            if message != default_msg:
                await self.bot.missile.announcement.send(message)
            self.logger.debug('Synced pool')
            with open('data.json', 'w') as f:
                json.dump(self.data, f, indent=2, separators=(',', ': '))
            self.bot.echo.db.commit()
            await asyncio.sleep(600)

    def rss_process(self, index, row):
        return asyncio.new_event_loop().run_until_complete(self.async_rss_process(index, row))

    async def async_rss_process(self, index, row):
        async with aiohttp.ClientSession() as session:
            self.logger.info(f"{index}: Checking RSS...")
            async with session.get(row['url']) as response:
                self.logger.debug(f"{index}: Fetching response...")
                text = await response.text()
        self.logger.debug(f"{index}: Parsing response...")
        feed = feedparser.parse(text).entries[0]
        result = None
        if row['newstitle'] != feed.title:
            self.logger.info(f'{index}: Detected news: {feed.title}')
            content = BeautifulSoup(feed.description, 'html.parser')
            rss_sub = self.bot.echo.cursor.execute('SELECT rssChID, footer FROM RssSub WHERE url = ?', (row['url'],)).fetchall()
            emb = discord.Embed(title=feed.title, description=content.get_text(), url=feed.link)
            emb.colour = discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
            for row in rss_sub:
                local_emb = emb.copy()
                channel = self.bot.get_channel(row['rssChID'])
                local_emb.set_footer(text=f"{row['footer']} | {feed.published}")
                asyncio.run_coroutine_threadsafe(channel.send(embed=local_emb), self.bot.loop)
            self.logger.info(f"{index}: Sent Discord")
            result = (feed.title, index)
        self.logger.info(f"{index}: Done")
        return result

    def bbm_process(self, addon_id: int):
        return asyncio.new_event_loop().run_until_complete(self.async_bbm_process(addon_id))

    async def async_bbm_process(self, addon_id: int):
        message = ''
        self.logger.info(f"Checking BBM {addon_id}...")
        async with aiohttp.ClientSession() as session:
            async with session.get(f'https://addons-ecs.forgesvc.net/api/v2/addon/{addon_id}') as response:
                self.logger.debug(f'Fetching BBM {addon_id}...')
                json_response = await response.json()
            self.logger.debug(f'Parsing BBM {addon_id}...')
            for i, latest_file in enumerate(json_response['latestFiles']):
                if latest_file['displayName'] not in self.data['BBM'][addon_id]:
                    async with session.get(
                            f"https://addons-ecs.forgesvc.net/api/v2/addon/{addon_id}/file/{latest_file['id']}/changelog") as response:
                        change_log = await response.text()
                    change_log = BeautifulSoup(change_log, 'html.parser')
                    game_version = None if len(latest_file['gameVersion']) == 0 else latest_file['gameVersion'][0]
                    message += f"An update of **{json_response['name']}** is now available!\n" \
                               f"__**{latest_file['displayName']}** for **{game_version}**__\n" \
                               f"{change_log.get_text()}\n\n"
                self.data['BBM'][addon_id][i] = latest_file['displayName']
        return message

    def yt_process(self):
        asyncio.new_event_loop().run_until_complete(self.async_yt())

    async def async_yt(self):
        self.logger.info('Checking YT')
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.googleapis.com/youtube/v3/activities?part=snippet,contentDetails&channelId=UCTuGoJ-MoQuSYVgtmJTa3-w&maxResults=1&key=' + youtube) as response:
                activities = await response.json()
                if activities['items'][0]['snippet']['type'] == 'upload':
                    video_id = activities['items'][0]['contentDetails']['upload']['videoId']
                    if self.data['YT'] != video_id:
                        self.logger.debug('New YT video detected')
                        asyncio.run_coroutine_threadsafe(self.bot.missile.announcement.send(
                            "http://youtube.com/watch?v=" + video_id), self.bot.loop)
                        self.data['YT'] = video_id

    @commands.group()
    async def rss(self, invoke_without_command=True):
        pass

    @rss.command(aliases=['s', 'sub'])
    @commands.check(Missile.is_owner)
    async def subscribe(self, ctx, ch: discord.TextChannel, url: str, *, footer: str):
        result = self.bot.echo.cursor.execute("SELECT EXISTS(SELECT 1 FROM RssSub WHERE rssChID = ? AND url = ?)",
                                              (ch.id, url)).fetchone()[0]
        if result:
            await ctx.send(f'{ch.mention} has already subscribed to this URL!')
            return
        result = self.bot.echo.cursor.execute("SELECT EXISTS(SELECT 1 FROM RssData WHERE url = ?)",
                                              (url, )).fetchone()[0]
        if not result:
            self.bot.echo.cursor.execute("INSERT INTO RssData VALUES (?, '')", (url,))
        self.bot.echo.cursor.execute("INSERT INTO RssSub VALUES (?, ?, ?)", (ch.id, url, footer))
        self.bot.echo.db.commit()
        await ctx.send('Subscribed!')
