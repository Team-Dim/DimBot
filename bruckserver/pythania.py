import binascii

import digitalocean
from aiohttp import web

import dimsecret
import missile


class Albon:
    """HTTP server
    Version 1.8"""

    def __init__(self, bot):
        self._channels = []
        self.bot = bot
        self.online = []
        self.logger = missile.get_logger('Albon')
        self.mgr = digitalocean.Manager(token=dimsecret.digital_ocean)
        self.path = ''
        self.github_webhook = None

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
            self.online = []
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
            droplets = filter(lambda d: d.name == 'mcser', self.mgr.get_all_droplets())
            for droplet in droplets:
                droplet.destroy()
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
            self.online = []

        @routes.post('/exit')
        async def exit_code(request: web.Request):
            self.online = []
            code = await request.text()
            msg = 'Minecraft server exited with code ' + code
            if code == '137':
                msg += '\n💥 Server crashed due to not enough RAM.'
            for channel in self._channels:
                self.bot.loop.create_task(channel.send(msg))
            return web.Response()

        @routes.post('/boot')
        async def boot(request):
            for channel in self._channels:
                self.bot.loop.create_task(channel.send('Linux 🤝 DimBot. Please wait for Minecraft server to boot.'))
            return web.Response(body=self.path)

        @routes.get('/b64d')
        async def base64decode(request):
            if 's' in request.rel_url.query:
                try:
                    decoded = missile.decode(request.rel_url.query['s'])
                except (UnicodeDecodeError, binascii.Error):
                    raise web.HTTPBadRequest(reason='Malformed base64 string')
                if missile.is_url(decoded):
                    raise web.HTTPFound(decoded)
                return web.Response(body=decoded)
            raise web.HTTPBadRequest(reason='Missing base64-encoded parameter')

        @routes.post('/ghub-webhook')
        async def github_webhook(request: web.Request):
            payload = await request.json()
            if not payload['repository']['private']:
                async with self.bot.session.post(self.github_webhook, json=payload) as r:
                    self.logger.info(f'Relayed GitHub webhook. Response: {r.status}')
                raise web.Response

        app = web.Application()
        app.add_routes(routes)
        runner = web.AppRunner(app)
        await runner.setup()
        site = web.TCPSite(runner, '0.0.0.0', 80)
        await site.start()
        self.logger.info('Site now running')

        # Fetches the webhook for #job
        await self.bot.wait_until_ready()
        for webhook in await self.bot.get_channel(435009339632123904).webhooks():
            if webhook.id == 476326171655667722:
                self.github_webhook = webhook.url
                break
