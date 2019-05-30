import asyncio
import json

import discord
import tokens
import feedparser
from discord.ext import commands
from random import randint
from bs4 import BeautifulSoup

bot = commands.Bot(command_prefix='>')
with open('urls.json', 'r') as file:
    rss_urls = json.load(file)
on_ready_triggered = False


@bot.event
async def on_ready():
    global on_ready_triggered
    if not on_ready_triggered:
        on_ready_triggered = True
        print('on_ready')
        with open('rss.json', 'r') as f:
            data = json.load(f)
        ch = bot.get_channel(581699408870113310)
        while True:
            for url in rss_urls:
                rss = feedparser.parse(rss_urls[url]).entries[0]
                if url not in data.keys():
                    data[url] = "None"
                if data[url] != rss.title:
                    print(f"Detected news for {url}, Sending...")
                    content = BeautifulSoup(rss.description, "html.parser")
                    emb = discord.Embed()
                    emb.colour = discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
                    emb.title = rss.title
                    emb.description = content.get_text()
                    emb.url = rss.link
                    emb.set_footer(text=f"{url} | {rss.published}")
                    await ch.send(embed=emb)
                    data[url] = rss.title
                    with open('rss.json', 'w') as f:
                        json.dump(data, f)
            await asyncio.sleep(600)


bot.run(tokens.discord)
