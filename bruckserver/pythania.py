from aiohttp import web

_address, _port = '0.0.0.0', 80


async def _setup_server(routes, logger):
    app = web.Application()
    app.add_routes(routes)
    runner = web.AppRunner(app)
    logger.debug('Setup runner...')
    await runner.setup()
    logger.debug('Runner has been set up.')
    site = web.TCPSite(runner, _address, _port)
    logger.debug('Starting website...')
    await site.start()
    logger.info('Site now running.')


async def run_server(logger, bot):
    routes = web.RouteTableDef()
    channel = bot.missile.bottyland  # if dimsecret.debug else bot.missile.bruck_ch

    @routes.get('/hook')
    async def root(request: web.Request):
        logger.info(f'{request.scheme} {request.version}')
        logger.info(request.headers)
        await channel.send("Lokeon has connected to DimBot. This is as amazing as Neil Armstrong landed on the 🌕!")
        return web.Response(text="Test")

    await _setup_server(routes, logger)
