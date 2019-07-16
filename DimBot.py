import asyncio
import json

import discord
import dimsecret
import feedparser
from discord.ext import commands
from random import randint
from bs4 import BeautifulSoup
from botglob import BotGlob

bot = commands.Bot(command_prefix='d.')
botglobal = BotGlob()
with open('urls.json', 'r') as file:
    rss_urls = json.load(file)
bot_ver = "0.1.1"


async def rss_process(domain: str):
    print(f"{domain}: Checking RSS...")
    try:
        feed = feedparser.parse(rss_urls[domain]['url']).entries[0]
        if domain not in botglobal.rss_data.keys():
            botglobal.rss_data[domain] = "None"
        if botglobal.rss_data[domain] != feed.title:
            print(f"{domain}: Detected news")
            botglobal.rss_updated = True
            await process_discord(domain, feed)
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
    role = botglobal.guild.get_role(rss_urls[domain]['role'])
    await role.edit(mentionable=True)
    await botglobal.ch.send(content=role.mention, embed=emb)
    await role.edit(mentionable=False)
    print(f"{domain}: Sent Discord")


@bot.event
async def on_ready():
    await bot.change_presence(activity=discord.Game(name=f"bot v{bot_ver}"))
    botglobal.guild = bot.get_guild(285366651312930817)
    if not botglobal.readied:
        botglobal.readied = True
        print('on_ready')
        chid = 372386868236386307 if dimsecret.debug else 581699408870113310
        botglobal.ch = bot.get_channel(chid)
        while True:
            botglobal.rss_updated = False
            for task in asyncio.as_completed([rss_process(domain) for domain in rss_urls]):
                u = await task
            if botglobal.rss_updated:
                with open('rss.json', 'w') as f:
                    json.dump(botglobal.rss_data, f)
            await asyncio.sleep(600)
    else:
        print('BOT IS ALREADY READY!')


bot.run(dimsecret.discord)
