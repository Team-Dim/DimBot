import asyncio

from aiohttp import web

__version__ = '1.2.1'


class Albon:

    def __init__(self, logger):
        self._channels = []  # List of channels to send messages
        self.logger = logger

    @property
    def get_channels(self):
        return self._channels

    def add_channel(self, channel):
        """Adds a Discord channel to the list"""
        if channel not in self._channels:
            self._channels.append(channel)

    async def _setup_server(self, routes):
        """Initialises an aiohttp server"""
        app = web.Application()
        app.add_routes(routes)
        runner = web.AppRunner(app)
        self.logger.debug('Setup runner...')
        await runner.setup()
        self.logger.debug('Runner has been set up.')
        site = web.TCPSite(runner, '0.0.0.0', 80)
        self.logger.debug('Starting website...')
        await site.start()
        self.logger.info('Site now running')

    async def run_server(self):
        """Adds routes to the HTTP server"""
        routes = web.RouteTableDef()

        @routes.get('/hook')
        async def hook(request: web.Request):
            """When Lokeon connects to DimBot for the first time"""
            self.logger.debug('Received Lokeon hook')
            for channel in self.get_channels:
                asyncio.get_running_loop().create_task(channel.send("Minecraft server :handshake: DimBot"))
            return web.Response()

        @routes.post('/join')
        async def join(request: web.Request):
            """When a player has joined the Minecraft server"""
            self.logger.debug('Received PlayerJoinEvent')
            data = await request.text()
            for channel in self.get_channels:
                await channel.send(f'**{data}** :handshake: Minecraft server')
            return web.Response()

        @routes.post('/quit')
        async def player_quit(request: web.Request):
            """When a player has left the Minecraft server"""
            self.logger.debug('Received PlayerQuitEvent')
            data = await request.text()
            for channel in self.get_channels:
                asyncio.get_running_loop().create_task(channel.send(f'**{data}** :wave: Minecraft server'))
            return web.Response()

        @routes.get('/shutdown')
        async def shutdown(request: web.Request):
            """When the Minecraft server shuts down"""
            name = request.rel_url.query['name']  # Checks who initiated the /stop command in game
            if name == '':
                # No one sent that command. That means the server shuts down due to Lokeon inactivity detector
                for channel in self.get_channels:
                    asyncio.get_running_loop().create_task(channel.send(
                        # "Please remember to send /stop in Minecraft!!!"
                        ':angry: Minecraft server has been idle for 15 minutes. **玩完記得喺MINECRAFT入面/STOP!!!**'))
            self.logger.debug('mcser is shutting down')
            for channel in self._channels:
                asyncio.get_running_loop().create_task(channel.send(f'** {name}** :axe: Minecraft server'))
            self._channels = []
            return web.Response()

        await self._setup_server(routes)
