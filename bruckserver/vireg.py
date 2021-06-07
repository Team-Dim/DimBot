import digitalocean
from discord.ext import commands

import missile
import tribe
from bruckserver.pythania import Albon


class Verstapen(missile.Cog):
    """Creates and communicates with a minecraft server instance.
    Version 3.0"""

    def __init__(self, bot):
        super().__init__(bot, 'Verstapen')
        self.albon = Albon(bot)
        self.starting = False
        bot.loop.create_task(self.albon.run_server())

    @commands.command()
    @missile.in_guilds(tribe.guild_id, 686397146290979003)
    async def start(self, ctx):
        self.albon.add_channel(ctx.channel)
        if self.starting:
            await ctx.reply('Server is starting, please retry the command in 10 seconds!')
            return
        self.starting = True
        region = 'lon1'
        droplets = filter(lambda d: d.name == 'mcser', self.albon.mgr.get_all_droplets())
        for droplet in droplets:
            await ctx.reply('Server is already running: ' + droplet.ip_address)
            return
        droplet = digitalocean.Droplet(
            token=self.albon.mgr.token,
            name='mcser',
            region=region,
            image=85521198,
            size_slug='s-2vcpu-4gb'
        )
        msg = await ctx.reply('Creating new instance')
        droplet.create()
        await missile.append_msg(msg, 'Attaching volume')
        droplet.get_actions()[0].load()  # Simulates wait
        self.albon.mgr.get_volume('8ae33506-c54a-11eb-bf8e-0a58ac14c198').attach(droplet.id, region)
        await missile.append_msg(msg, 'Attaching firewall')
        self.albon.mgr.get_firewall('b55786d5-0c03-497c-a30c-5fa2a8b5e340').add_droplets((droplet.id,))
        droplet.load()
        await missile.append_msg(msg, f'IP: **{droplet.ip_address}** Please wait for Linux to boot!')
        self.starting = False

    @commands.command()
    @missile.is_rainbow()
    async def post(self, ctx, path: str):
        async with self.bot.session.post('http://localhost/' + path) as r:
            await ctx.reply(f"{r.status}: {await r.text()}")

    @commands.command()
    async def players(self, ctx: commands.Context):
        msg = f"There are **{len(self.albon.online)}** players online:\n"
        msg += '\n'.join(self.albon.online)
        await ctx.reply(msg)
