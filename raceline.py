import asyncio
import json
from concurrent.futures.thread import ThreadPoolExecutor
from random import randint

import aiohttp
import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import commands


class Raceline(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Raceline')
        self.pool = ThreadPoolExecutor()

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.info('on_ready')
        with open('urls.json', 'r') as f:
            url = json.load(f)
        with open('rss.json', 'r') as f:
            rss = json.load(f)
        await self.rss_task(url, rss)

    async def rss_task(self, url: dict, rss: dict):
        session = aiohttp.ClientSession()
        for domain in url.keys():
            self.logger.info(f"{domain}: Checking RSS...")
            response = await session.get(url[domain])
            self.logger.debug(f"{domain}: Fetching response...")
            text = await response.text()
            self.logger.debug(f"{domain}: Parsing response...")
            feed = feedparser.parse(text).entries[0]
            if domain not in rss.keys():
                rss[domain] = ''
            if rss[domain] != feed.title:
                self.logger.info(f'{domain}: Detected news')
                rss[domain] = feed.title
                content = BeautifulSoup(feed.description, 'html.parser')
                emb = discord.Embed(title=feed.title, description=content.get_text(), url=feed.link)
                emb.colour = discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
                emb.set_footer(text=f"{domain} | {feed.published}")
                await self.bot.missile.newsfeed.send(embed=emb)
                self.logger.info(f"{domain}: Sent Discord")
            self.logger.debug(f"{domain}: Done")
        with open('rss.json', 'w') as f:
            json.dump(rss, f, indent=2, separators=(',', ': '))
        await asyncio.sleep(600)
        await self.rss_task(url, rss)
