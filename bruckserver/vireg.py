import digitalocean
from discord.ext import commands

import missile
import tribe
from bruckserver.pythania import Albon


class Verstapen(missile.Cog):
    """Creates and communicates with a minecraft server instance.
    Version 3.1"""

    def __init__(self, bot):
        super().__init__(bot, 'Verstapen')
        self.albon = Albon(bot)
        self.starting = False
        bot.loop.create_task(self.albon.run_server())

    @commands.command()
    @missile.in_guilds(tribe.guild_id, 892131166117834843)
    async def start(self, ctx):
        """Shows the IP of the minecraft server. If no mcser is running, it launches a new one and shows its IP.
        Only works in Dim's guild."""
        self.albon.add_channel(ctx.channel)
        if self.starting:
            await ctx.reply('Server is starting, please retry the command in 10 seconds!')
            return
        region = 'lon1'
        for droplet in filter(lambda d: d.name == 'mcser', self.albon.mgr.get_all_droplets()):
            await ctx.reply('Server is already running: ' + droplet.ip_address)
            return
        self.starting = True

        droplet = digitalocean.Droplet(
            token=self.albon.mgr.token,
            name='mcser',
            region=region,
            image=99729422,
            size_slug='s-1vcpu-2gb',
            ssh_keys=self.albon.mgr.get_all_sshkeys()
        )
        msg = await ctx.reply('Creating new instance')
        await ctx.bot.loop.run_in_executor(None, droplet.create)
        await missile.append_msg(msg, 'Attaching volume')
        await ctx.bot.loop.run_in_executor(None, droplet.get_actions()[0].wait)
        await ctx.bot.loop.run_in_executor(
            None,
            self.albon.mgr.get_volume('c7d4f919-737c-11ec-9294-0a58ac14c05f').attach, droplet.id, region)
        await missile.append_msg(msg, 'Attaching firewall')
        await ctx.bot.loop.run_in_executor(
            None,
            self.albon.mgr.get_firewall('3ebd8414-1f78-4222-bdc2-558027bc8c9c').add_droplets, (droplet.id,)
        )
        await ctx.bot.loop.run_in_executor(None, droplet.load)
        await missile.append_msg(msg, f'IP: **{droplet.ip_address}** Please wait for Linux to boot!')
        self.starting = False

    @commands.command()
    @missile.is_rainbow()
    async def post(self, ctx, path: str):
        async with self.bot.session.post('http://localhost/' + path) as r:
            await ctx.reply(f"{r.status}: {await r.text()}")

    @commands.command()
    async def players(self, ctx: commands.Context):
        """Shows the amount of players in the minecraft server.
        ⚠This only works if the server was launched via d.start"""
        msg = f"There are **{len(self.albon.online)}** players online:\n"
        msg += '\n'.join(self.albon.online)
        await ctx.reply(msg)
