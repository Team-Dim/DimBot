from aiohttp import web

import dimsecret


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
        logger.info(request.protocol)
        logger.info('Received Lokeon hook')
        await channel.send("Lokeon has connected to DimBot. This is as amazing as Neil Armstrong landed on the 🌕!")
        return web.Response()

    @routes.post('/join')
    async def player_join(request: web.Request):
        logger.info('Received PlayerJoinEvent')
        data = await request.text()
        await channel.send(f'{data} has joined the server.')
        return web.Response()

    await _setup_server(routes, logger)
