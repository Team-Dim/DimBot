import boto3
from discord.ext import commands

import dimsecret
from bruckserver.albon import Albon
from missile import Missile


def is_rainbow(ctx):
    return ctx.author.id == 264756129916125184


__version__ = '1.3'


class Verstapen(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Vireg')
        self.http_not_started = True
        self.albon = Albon(bot.missile.get_logger('Albon'))

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')

    async def boot_instance(self, ctx, instance_id: str, region_id: str):
        msg = await ctx.send('Connecting to Amazon Web Service...')
        self.logger.info('Connecting to AWS')
        session = boto3.session.Session(
            region_name=region_id,
            aws_access_key_id=dimsecret.aws_access_key,
            aws_secret_access_key=dimsecret.aws_secret_key
        )
        ec2 = session.resource('ec2')
        ssm = session.client('ssm')
        self.logger.debug('Fetching SSM parameter')
        response = ssm.get_parameter(Name=f'/aws/service/global-infrastructure/regions/{region_id}/longName')
        region_name = response['Parameter']['Value']
        await Missile.append_message(msg, f'Checking if instance *{instance_id}* is already running...')
        instance = ec2.Instance(instance_id)
        if instance.state['Code'] != 80:
            await Missile.append_message(msg, 'Instance is already running')
        else:
            msg = await ctx.send('Sending start request...')
            instance.start()
            await Missile.append_message(msg, "Waiting for the instance to be booted...")
            instance.wait_until_running()
            await Missile.append_message(msg, 'Instance has successfully started')
        await Missile.append_message(
            msg,
            f'in {region_id} **"{region_name}"**. IP address: **{instance.public_ip_address}** ',
            delimiter=' '
        )
        self.albon.add_channel(ctx.channel)
        if self.http_not_started:
            await self.albon.run_server()
            self.http_not_started = False

    @commands.command()
    @commands.check(is_rainbow)
    async def eu(self, ctx):
        await self.boot_instance(ctx, dimsecret.eu_instance_id, 'eu-north-1')

    @commands.command()
    async def start(self, ctx):
        # Remove this check when Lokeon has finished rewriting.
        if not is_rainbow(ctx):
            await ctx.send(':construction: Sorry, this feature is currently not available, please ask ChingDim in Discord to help you!')
            return
        if dimsecret.debug:
            await ctx.send('⚠DimBot is currently in **DEBUG** mode. I cannot receive messages from Lokeon, also things may not work as expected!⚠\n')
        await self.boot_instance(ctx, dimsecret.bruck_instance_id, 'ap-southeast-1')
