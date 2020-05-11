from aiohttp import web


async def _setup_server(routes, logger):
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    logger.debug('Setup runner...')
    await runner.setup()
    logger.debug('Runner has been set up.')
    site = web.TCPSite(runner, '0.0.0.0', 80)
    logger.debug('Starting website...')
    await site.start()
    logger.info('Site now running')


async def run_server(logger, channel):
    routes = web.RouteTableDef()

    @routes.get('/hook')
    async def hook(request: web.Request):
        logger.info('Received Lokeon hook')
        await channel.send("Minecraft server :handshake: DimBot")
        return web.Response()

    @routes.post('/join')
    async def join(request: web.Request):
        logger.info('Received PlayerJoinEvent')
        data = await request.text()
        await channel.send(f'**{data}** :handshake: Minecraft server.')
        return web.Response()

    @routes.post('/quit')
    async def player_quit(request: web.Request):
        logger.info('Received PlayerQuitEvent')
        data = await request.text()
        await channel.send(f'**{data}** :wave: Minecraft server.')
        return web.Response()

    @routes.get('/shutdown')
    async def shutdown(request: web.Request):
        if 'idle' in request.rel_url.query:
            await channel.send(':angry: Minecraft server has been idle for 15 minutes. YOU SHOULD /STOP BY YOURSELF!!!1')
        logger.info('mcser is shutting down')
        await channel.send('Instance is shutting down.')
        return web.Response()

    await _setup_server(routes, logger)
