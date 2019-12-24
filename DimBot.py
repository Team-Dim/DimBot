import asyncio
import json
import logging
from concurrent.futures.thread import ThreadPoolExecutor
from random import randint

import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import commands

import dimsecret
from botglob import BotGlob

bot = commands.Bot(command_prefix='d.')
botglobal = BotGlob()
with open('urls.json', 'r') as file:
    rss_urls = json.load(file)
logger = logging.getLogger("DimBot")
lvl = logging.DEBUG if dimsecret.debug else logging.INFO
logger.setLevel(lvl)
ch = logging.StreamHandler()
ch.setLevel(lvl)
ch.setFormatter(logging.Formatter(fmt='[%(threadName)s/%(levelname)s] [%(asctime)s] %(message)s',
                                  datefmt='%H:%M:%S'))
logger.addHandler(ch)


def rss_process(domain: str):
    logger.info(f"{domain}: Checking RSS...")
    try:
        feed = feedparser.parse(rss_urls[domain]['url']).entries[0]
        if domain not in botglobal.rss_data.keys():
            botglobal.rss_data[domain] = ""
        if botglobal.rss_data[domain] != feed.title:
            logger.info(f"{domain}: Detected news: {feed.title}")
            botglobal.rss_updated = True
            botglobal.rss_data[domain] = feed.title
            content = BeautifulSoup(feed.description, "html.parser")
            emb = discord.Embed()
            emb.colour = discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
            emb.title = feed.title
            emb.description = content.get_text()
            emb.url = feed.link
            emb.set_footer(text=f"{domain} | {feed.published}")
            asyncio.run_coroutine_threadsafe(send_discord(domain, emb), bot.loop)
        else:
            logger.info(f"{domain}: No updates.")
    except IndexError:
        logger.warning(f"{domain}: IndexError")
    botglobal.done += 1


async def send_discord(domain, emb):
    await botglobal.ch.send(embed=emb)
    logger.info(f"{domain}: Sent Discord")


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name="bot v0.2.6"))
    botglobal.guild = bot.get_guild(285366651312930817)
    if not botglobal.readied:
        botglobal.readied = True
        logger.debug('on_ready')
        botglobal.ch = bot.get_channel(372386868236386307 if dimsecret.debug else 581699408870113310)
        pool = ThreadPoolExecutor(max_workers=2)
        while True:
            botglobal.rss_updated = False
            for domain in rss_urls:
                pool.submit(rss_process, domain)
            while botglobal.done != 5:
                pass
            logger.debug('Synced thread pool, continuing')
            if botglobal.rss_updated and not dimsecret.debug:
                with open('rss.json', 'w') as f:
                    json.dump(botglobal.rss_data, f)
            await asyncio.sleep(600)
    else:
        logger.warning('BOT IS ALREADY READY!')


bot.run(dimsecret.discord)
