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
bot_ver = "0.2.0"
logging.basicConfig(format='[%(threadName)s/%(levelname)s] [%(asctime)s] %(message)s',
                    datefmt='%H:%M:%S',
                    level=logging.INFO)


def rss_process(domain: str):
    logging.info(f"{domain}: Checking RSS...")
    try:
        feed = feedparser.parse(rss_urls[domain]['url']).entries[0]
        if domain not in botglobal.rss_data.keys():
            botglobal.rss_data[domain] = ""
        if botglobal.rss_data[domain] != feed.title:
            logging.info(f"{domain}: Detected news")
            botglobal.rss_updated = True
            content = BeautifulSoup(feed.description, "html.parser")
            emb = discord.Embed()
            emb.colour = discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
            emb.title = feed.title
            emb.description = content.get_text()
            emb.url = feed.link
            emb.set_footer(text=f"{domain} | {feed.published}")
            asyncio.run_coroutine_threadsafe(send_discord(domain, emb), bot.loop)
            botglobal.rss_data[domain] = feed.title
        else:
            logging.info(f"{domain}: No updates.")
    except IndexError:
        logging.warning(f"{domain}: IndexError")


async def send_discord(domain, emb):
    role = botglobal.guild.get_role(rss_urls[domain]['role'])
    await role.edit(mentionable=True)
    await botglobal.ch.send(content=role.mention, embed=emb)
    await role.edit(mentionable=False)
    logging.info(f"{domain}: Sent Discord")


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=f"bot v{bot_ver}"))
    botglobal.guild = bot.get_guild(285366651312930817)
    if not botglobal.readied:
        botglobal.readied = True
        logging.debug('on_ready')
        chid = 372386868236386307 if dimsecret.debug else 581699408870113310
        botglobal.ch = bot.get_channel(chid)
        pool = ThreadPoolExecutor(max_workers=4)
        while True:
            botglobal.rss_updated = False
            for domain in rss_urls:
                pool.submit(rss_process, domain)
            if botglobal.rss_updated and not dimsecret.debug:
                with open('rss.json', 'w') as f:
                    json.dump(botglobal.rss_data, f)
            await asyncio.sleep(600)
    else:
        logging.warning('BOT IS ALREADY READY!')


bot.run(dimsecret.discord)
