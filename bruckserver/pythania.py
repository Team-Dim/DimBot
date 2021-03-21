import asyncio

from aiohttp import web


class Albon:
    """HTTP server sub-project used by Verstapen
    Version 1.2.3"""

    def __init__(self, logger):
        self._channels = []
        self.logger = logger

    @property
    def channels(self):
        return self._channels

    def add_channel(self, channel):
        if channel not in self._channels:
            self._channels.append(channel)

    async def _setup_server(self, routes):
        app = web.Application()
        app.add_routes(routes)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 80)
        await site.start()
        self.logger.info('Site now running')

    async def run_server(self):
        routes = web.RouteTableDef()

        @routes.get('/hook')
        async def hook(request: web.Request):
            self.logger.debug('Received Lokeon hook')
            for channel in self.channels:
                asyncio.get_running_loop().create_task(channel.send("Minecraft server :handshake: DimBot"))
            return web.Response()

        @routes.post('/join')
        async def join(request: web.Request):
            self.logger.debug('Received PlayerJoinEvent')
            data = await request.text()
            for channel in self.channels:
                asyncio.get_running_loop().create_task(channel.send(f'**{data}** :handshake: Minecraft server'))
            return web.Response()

        @routes.post('/quit')
        async def player_quit(request: web.Request):
            self.logger.debug('Received PlayerQuitEvent')
            data = await request.text()
            for channel in self.channels:
                asyncio.get_running_loop().create_task(channel.send(f'**{data}** :wave: Minecraft server'))
            return web.Response()

        @routes.get('/shutdown')
        async def shutdown(request: web.Request):
            name = request.rel_url.query['name']
            if name == '':
                for channel in self.channels:
                    asyncio.get_running_loop().create_task(channel.send(
                        ':angry: Minecraft server has been idle for 15 minutes. '
                        '**Please /stop in Minecraft when you are done!!!**'))
            self.logger.debug('mcser is shutting down')
            for channel in self._channels:
                asyncio.get_running_loop().create_task(channel.send(f'**{name}** :axe: Minecraft server'))
            self._channels = []
            return web.Response()

        @routes.get('/exitcode')
        async def exit_code(request: web.Request):
            code = request.rel_url.query['code']
            for channel in self._channels:
                asyncio.get_running_loop().create_task(channel.send('server.jar exited with code ' + code))

        await self._setup_server(routes)
