from aiohttp import web


class Albon:
    """HTTP server sub-project used by Verstapen
    Version 1.3"""

    def __init__(self, bot):
        self._channels = []
        self.bot = bot
        self.online = []
        self.logger = bot.missile.get_logger('Albon')

    @property
    def channels(self):
        return self._channels

    def add_channel(self, channel):
        if channel not in self._channels:
            self._channels.append(channel)

    async def run_server(self):
        routes = web.RouteTableDef()

        @routes.post('/hook')
        async def hook(request):
            self.logger.debug('Received Lokeon hook')
            for channel in self.channels:
                self.bot.loop.create_task(channel.send("Minecraft server 🤝 DimBot"))
            return web.Response()

        @routes.post('/join')
        async def join(request: web.Request):
            self.logger.debug('Received PlayerJoinEvent')
            data = await request.text()
            self.online.append(data)
            for channel in self.channels:
                self.bot.loop.create_task(channel.send(f'**{data}** 🤝 Minecraft server'))
            return web.Response()

        @routes.post('/quit')
        async def player_quit(request: web.Request):
            self.logger.debug('Received PlayerQuitEvent')
            data = await request.text()
            self.online.remove(data)
            for channel in self.channels:
                self.bot.loop.create_task(channel.send(f'**{data}** 👋 Minecraft server'))
            return web.Response()

        @routes.post('/shutdown')
        async def shutdown(request: web.Request):
            name = await request.text()
            if name == '':
                msg = ':angry: Minecraft server has been idle for 15 minutes. ' \
                      '**Please /stop in Minecraft when you are done!!!**\n'
            else:
                msg = f'**{name}** '
            msg += '🪓 Minecraft server'
            self.logger.debug('mcser is shutting down')
            for channel in self._channels:
                self.bot.loop.create_task(channel.send(msg))
            self._channels = []
            return web.Response()

        @routes.post('/exit')
        async def exit_code(request: web.Request):
            code = await request.text()
            msg = 'Minecraft server exited with code ' + code
            if code == '137':
                msg += '\n💥 Server crashed due to not enough RAM. ' \
                       '/stop in game and send `d.start 1` if this continues.'
            for channel in self._channels:
                self.bot.loop.create_task(channel.send(msg))
            return web.Response()

        @routes.post('/boot')
        async def boot(request):
            for channel in self._channels:
                self.bot.loop.create_task(channel.send('Linux 🤝 DimBot. Please wait for Minecraft server to boot.'))
            return web.Response()

        app = web.Application()
        app.add_routes(routes)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 80)
        await site.start()
        self.logger.info('Site now running')
