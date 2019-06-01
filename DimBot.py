import asyncio
import json

import discord
import tokens
import feedparser
from discord.ext import commands
from random import randint
from bs4 import BeautifulSoup
from botglob import BotGlob

bot = commands.Bot(command_prefix='d.')
botglobal = BotGlob()
with open('urls.json', 'r') as file:
    rss_urls = json.load(file)


async def rss_process(domain: str):
    print(f"{domain}: Checking RSS...")
    try:
        feed = feedparser.parse(rss_urls[domain]).entries[0]
        if domain not in botglobal.rss_data.keys():
            botglobal.rss_data[domain] = "None"
        if botglobal.rss_data[domain] != feed.title:
            print(f"{domain}: Detected news")
            await asyncio.gather(
                process_discord(domain, feed)
            )
            botglobal.rss_data[domain] = feed.title
        else:
            print(f"{domain}: No updates.")
    except IndexError:
        print(f"{domain}: IndexError")


async def process_discord(domain: str, feed):
    content = BeautifulSoup(feed.description, "html.parser")
    emb = discord.Embed()
    emb.colour = discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
    emb.title = feed.title
    emb.description = content.get_text()
    emb.url = feed.link
    emb.set_footer(text=f"{domain} | {feed.published}")
    await botglobal.ch.send(embed=emb)
    print(f"{domain}: Sent Discord")


@bot.event
async def on_ready():
    if not botglobal.readied:
        botglobal.readied = True
        print('on_ready')
        botglobal.ch = bot.get_channel(581699408870113310)
        while True:
            tasks = []
            for domain in rss_urls:
                tasks.append(rss_process(domain))
            await asyncio.gather(*tasks)
            with open('rss.json', 'w') as f:
                json.dump(botglobal.rss_data, f)
            await asyncio.sleep(600)
    else:
        print('BOT IS ALREADY READY!')


bot.run(tokens.discord)
