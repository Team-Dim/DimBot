import asyncio
import platform
import json
from concurrent.futures.thread import ThreadPoolExecutor
from random import randint

import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import commands

from botglob import BotGlob
import dimsecret
from missile import Missile
from tribe import Tribe
from bruckserver import vireg, pythania

bot = commands.Bot(command_prefix='d.')
bot.missile = Missile(bot)

nickname = "ChingDim's nurse"
version = 'v0.3.3'
activity = discord.Activity(
        name='Silent flower 💮',
        type=discord.ActivityType.watching
)

if dimsecret.debug:
    nickname += f' [{version}]'
    news_ch = 372386868236386307
else:
    nickname += f' {{{version}}}'
    news_ch = 581699408870113310

botglobal = BotGlob()
with open('urls.json', 'r') as file:
    rss_urls = json.load(file)
logger = bot.missile.get_logger('DimBot')


@bot.command()
async def info(ctx):
    await ctx.send(
        f'Python `{platform.python_version()}`, discord.py `{discord.__version__}`. Debug mode: **{dimsecret.debug}**\n'
        'Bot source code: https://github.com/TCLRainbow/DimBot')


@bot.event
async def on_ready():
    bot.missile.guild = bot.get_guild(285366651312930817)
    bot.missile.bottyland = bot.get_channel(372386868236386307)
    bot.missile.bruck_ch = bot.get_channel(688948118712090644)
    logger.info(f'Guild count: {len(bot.guilds)}')
    for guild in bot.guilds:
        await guild.me.edit(nick=nickname)
    await bot.change_presence(activity=activity)
    botglobal.guild = bot.missile.guild
    # Maybe move below to cog 'Raceline'
    if not botglobal.readied:
        botglobal.readied = True
        logger.debug('on_ready')
        botglobal.ch = bot.get_channel(news_ch)
        pool = ThreadPoolExecutor()
        while True:
            botglobal.done = 0
            botglobal.rss_updated = False
            for domain in rss_urls:
                pool.submit(rss_process, domain)
            logger.debug('Start 10 minutes wait')
            await asyncio.sleep(600)
    else:
        logger.warning('BOT IS ALREADY READY!')


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
    logger.debug('%s: done' % domain)
    botglobal.done += 1
    if botglobal.done == len(rss_urls.keys()):
        logger.debug('Synced thread pool, continuing')
        if botglobal.rss_updated:
            with open('rss.json', 'w') as f:
                json.dump(botglobal.rss_data, f, indent=2, separators=(',', ': '))
            logger.debug('Updated file')


async def send_discord(domain, emb):
    await botglobal.ch.send(embed=emb)
    logger.info(f"{domain}: Sent Discord")


bot.add_cog(Tribe(bot))
bot.add_cog(vireg.Vireg(bot))
bot.run(dimsecret.discord)
