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

__version__ = '4.0.1'

from dimsecret import debug, youtube


class Raceline(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Raceline')
        self.new = True
        self.pool = ThreadPoolExecutor()
        self.data = dict()
        if debug:
            asyncio.set_event_loop_policy(
                asyncio.WindowsSelectorEventLoopPolicy())  # https://github.com/aio-libs/aiohttp/issues/4324

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')
        if self.new:
            self.new = False
            with open('urls.json', 'r') as f:
                url = json.load(f)
            with open('data.json', 'r') as f:
                self.data = json.load(f)
            await self.raceline_task(url)

    async def raceline_task(self, url: dict):
        while True:
            resultless_futures = []
            for domain in url.keys():
                resultless_futures.append(self.pool.submit(self.rss_process, domain, url))
            message = default_msg = '' if debug else '<@!664210105318768661> '
            bbm_futures = [self.pool.submit(self.bbm_process, addon_id) for addon_id in self.data['BBM'].keys()]
            resultless_futures.append(self.pool.submit(self.yt_process))
            concurrent.futures.wait(resultless_futures)
            concurrent.futures.wait(bbm_futures)
            for future in bbm_futures:
                message += future.result()
            if message != default_msg:
                await self.bot.missile.announcement.send(message)
            self.logger.debug('Synced pool')
            with open('data.json', 'w') as f:
                json.dump(self.data, f, indent=2, separators=(',', ': '))
            await asyncio.sleep(600)

    def rss_process(self, domain, url):
        asyncio.new_event_loop().run_until_complete(self.async_rss_process(domain, url))

    async def async_rss_process(self, domain, url):
        async with aiohttp.ClientSession() as session:
            self.logger.info(f"{domain}: Checking RSS...")
            async with session.get(url[domain]) as response:
                self.logger.debug(f"{domain}: Fetching response...")
                text = await response.text()
        self.logger.debug(f"{domain}: Parsing response...")
        feed = feedparser.parse(text).entries[0]
        if domain not in self.data.keys():
            self.data[domain] = ''
        if self.data[domain] != feed.title:
            self.logger.info(f'{domain}: Detected news: {feed.title}')
            self.data[domain] = feed.title
            content = BeautifulSoup(feed.description, 'html.parser')
            emb = discord.Embed(title=feed.title, description=content.get_text(), url=feed.link)
            emb.colour = discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
            emb.set_footer(text=f"{domain} | {feed.published}")
            asyncio.run_coroutine_threadsafe(self.bot.missile.newsfeed.send(embed=emb), self.bot.loop)
            self.logger.info(f"{domain}: Sent Discord")
        self.logger.info(f"{domain}: Done")

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
                    message += f"An update of **{json_response['name']}** is now available!\n" \
                               f"__**{latest_file['displayName']}** for **{latest_file['gameVersion'][0]}**__\n" \
                               f"{change_log.get_text()}\n\n"
                self.data['BBM'][addon_id][i] = latest_file['displayName']

        return message

    def yt_process(self):
        asyncio.new_event_loop().run_until_complete(self.async_yt())

    async def async_yt(self):
        self.logger.info('Checking YT')
        async with aiohttp.ClientSession() as session:
            async with session.get('https://www.googleapis.com/youtube/v3/search?part=snippet&channelId=UCTuGoJ-MoQuSYVgtmJTa3-w&maxResults=10&order=date&type=video&key=' + youtube) as response:
                json_response = await response.json()
        if self.data['YT'] != json_response['items'][0]['id']['videoId']:
            self.logger.debug('New YT video detected')
            asyncio.run_coroutine_threadsafe(self.bot.missile.announcement.send("http://youtube.com/watch?v=" + json_response['items'][0]['id']['videoId']), self.bot.loop)
        self.data['YT'] = json_response['items'][0]['id']['videoId']
