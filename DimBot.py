import asyncio
import builtins
import functools
import json
import threading
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
bot_ver = "0.2a"


def print(msg: str):
    builtins.print(f"[{threading.current_thread().name}] {msg}")


async def rss_process(domain: str, loop):
    print(f"{domain}: Checking RSS...")
    try:
        feed = feedparser.parse(rss_urls[domain]['url']).entries[0]
        if domain not in botglobal.rss_data.keys():
            botglobal.rss_data[domain] = ""
        if botglobal.rss_data[domain] != feed.title:
            print(f"{domain}: Detected news")
            botglobal.rss_updated = True
            await process_discord(domain, feed, loop)
            botglobal.rss_data[domain] = feed.title
        else:
            print(f"{domain}: No updates.")
    except IndexError:
        print(f"{domain}: IndexError")


async def process_discord(domain: str, feed, loop):
    content = BeautifulSoup(feed.description, "html.parser")
    emb = discord.Embed()
    emb.colour = discord.Colour.from_rgb(randint(0, 255), randint(0, 255), randint(0, 255))
    emb.title = feed.title
    emb.description = content.get_text()
    emb.url = feed.link
    emb.set_footer(text=f"{domain} | {feed.published}")
    asyncio.run_coroutine_threadsafe(sendDiscord(domain, emb), loop)


async def sendDiscord(domain, emb):
    role = botglobal.guild.get_role(rss_urls[domain]['role'])
    await role.edit(mentionable=True)
    await botglobal.ch.send(content=role.mention, embed=emb)
    await role.edit(mentionable=False)
    print(f"{domain}: Sent Discord")


def ycess(domain: str, loop):
    lp = asyncio.new_event_loop()
    lp.run_until_complete(rss_process(domain, loop))


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
            loop = asyncio.get_running_loop()
            for domain in rss_urls:
                await loop.run_in_executor(None, functools.partial(ycess, domain, loop))
            if botglobal.rss_updated:
                with open('rss.json', 'w') as f:
                    json.dump(botglobal.rss_data, f)
            await asyncio.sleep(600)
    else:
        print('BOT IS ALREADY READY!')


bot.run(dimsecret.discord)
