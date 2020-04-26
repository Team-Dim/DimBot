from aiohttp import web

import dimsecret


async def _setup_server(routes, logger):
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    logger.debug('Setup runner...')
    await runner.setup()
    logger.debug('Runner has been set up.')
    address = '0.0.0.0'
    site = web.TCPSite(runner, address, dimsecret.port)
    logger.debug('Starting website...')
    await site.start()
    logger.info(f'Site now running on {address}:{dimsecret.port}')


async def run_server(logger, bot):
    routes = web.RouteTableDef()
    channel = bot.missile.bottyland if dimsecret.debug else bot.missile.bruck_ch

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
