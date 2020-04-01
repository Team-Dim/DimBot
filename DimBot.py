import asyncio
import hashlib
import json
import random
from concurrent.futures.thread import ThreadPoolExecutor
from random import randint

import discord
import feedparser
from bs4 import BeautifulSoup
from discord.ext import commands

import dimsecret
from botglob import BotGlob
from missile import Missile
from tribe import Tribe

bot = commands.Bot(command_prefix='d.')
bot.missile = Missile(bot)
playing = ' v0.3.1'
if dimsecret.debug:
    playing = f'DEBUG{playing}'
    news_ch = 372386868236386307
else:
    playing = f'bot{playing}'
    news_ch = 581699408870113310

botglobal = BotGlob()
with open('urls.json', 'r') as file:
    rss_urls = json.load(file)
logger = bot.missile.get_logger('DimBot')


# April Fools
@bot.event
async def on_message(msg):
    if msg.author.name != "DimBot":
        await msg.delete()
        hex_md5 = hashlib.md5(f'{msg.content}{msg.id}'.encode('utf-8')).hexdigest()
        md5 = str(bin(int(hex_md5, 16))[2:].zfill(128))
        count = 0
        if msg.author.id in bot.missile.dna.keys():
            og = bot.missile.dna[msg.author.id]
            for i in range(128):
                if og[i] == md5[i]:
                    count += 1
        current_count = 0
        if bot.missile.current_dna != '':
            for i in range(128):
                if bot.missile.current_dna[i] == md5[i]:
                    current_count += 1
        emb = discord.Embed(title=str(msg.author),
                            description=msg.content)
        emb.add_field(name='Coronavirus DNA', value=hex_md5)
        infection = round(random.uniform(0, 1) * 100, 1)
        self_mod = round(count/128 * 100, 1)
        infected_by = round(current_count/128 * 100, 1)
        emb.add_field(name='self-modified rate', value=str(self_mod))
        emb.add_field(name='Probability of infected by others', value=str(infected_by))
        await bot.missile.quch.send(embed=emb)
        if infection < self_mod and not role(msg.author):

            print(f'{msg.author.name} self infected')
            await bot.missile.quch.send(f"**WARNING!** {msg.author.mention}'s body has evolved coronavirus by himself!")
            await msg.author.add_roles(bot.missile.role)
        if infected_by < self_mod and not role(msg.author):
            print(f'{msg.author.name} infected by {bot.missile.current_author.name}')
            await bot.missile.quch.send(f"**OH FUCK!** {msg.author.mention} IS INFECTED BY {bot.missile.current_author.mention}!!!")
            await msg.author.add_roles(bot.missile.role)
        bot.missile.dna[msg.author.id] = md5
        bot.missile.current_dna = md5
        bot.missile.current_author = msg.author

def role(m):
    for role in m.roles:
        if role.id == 694735841909538836:
            return True
    return False


@bot.event
async def on_ready():
    bot.missile.quch = bot.get_channel(694714241827078224)
    bot.missile.guild = bot.get_guild(285366651312930817)
    bot.missile.role = bot.missile.guild.get_role(694735841909538836)
    bot.missile.bottyland = bot.get_channel(372386868236386307)
    await bot.change_presence(activity=discord.Game(name=playing))
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
bot.run(dimsecret.discord)
