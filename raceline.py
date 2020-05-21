import asyncio
import json
from concurrent.futures.thread import ThreadPoolExecutor
from random import randint

import aiohttp
import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import commands

__version__ = '3.1'

from dimsecret import debug


class Raceline(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Raceline')
        self.new = True
        if debug:
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())  # https://github.com/aio-libs/aiohttp/issues/4324

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')
        if self.new:
            self.new = False
            with open('urls.json', 'r') as f:
                url = json.load(f)
            with open('rss.json', 'r') as f:
                rss = json.load(f)
            await self.rss_task(url, rss)

    async def rss_task(self, url: dict, rss: dict):
        while True:
            with ThreadPoolExecutor() as e:
                for domain in url.keys():
                    e.submit(self.rss_process, domain, url, rss)
            self.logger.debug('Synced pool')
            with open('rss.json', 'w') as f:
                json.dump(rss, f, indent=2, separators=(',', ': '))
            await asyncio.sleep(600)

    def rss_process(self, domain, url, rss):
        asyncio.new_event_loop().run_until_complete(self.async_rss_process(domain, url, rss))

    async def async_rss_process(self, domain, url, rss):
        async with aiohttp.ClientSession() as session:
            self.logger.info(f"{domain}: Checking RSS...")
            async with session.get(url[domain]) as response:
                self.logger.debug(f"{domain}: Fetching response...")
                text = await response.text()
        self.logger.debug(f"{domain}: Parsing response...")
        feed = feedparser.parse(text).entries[0]
        if domain not in rss.keys():
            rss[domain] = ''
        if rss[domain] != feed.title:
            self.logger.info(f'{domain}: Detected news: {feed.title}')
            rss[domain] = feed.title
            content = BeautifulSoup(feed.description, 'html.parser')
            emb = discord.Embed(title=feed.title, description=content.get_text(), url=feed.link)
            emb.colour = discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
            emb.set_footer(text=f"{domain} | {feed.published}")
            asyncio.run_coroutine_threadsafe(self.bot.missile.newsfeed.send(embed=emb), self.bot.loop)
            self.logger.info(f"{domain}: Sent Discord")
        self.logger.info(f"{domain}: Done")
