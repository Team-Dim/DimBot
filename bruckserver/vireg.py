import boto3
from discord.ext import commands

import dimsecret
from bruckserver.pythania import Albon
from missile import Missile


class Verstapen(commands.Cog):
    """Connects to AWS and communicates with a minecraft server instance.
    Version 1.3.1"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Verstapen')
        self.http_not_started = True
        self.albon = Albon(bot.missile.get_logger('Albon'))

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
    @Missile.is_rainbow_cmd_check(':construction: Sorry, this feature is currently not available, please ask Dim '
                                  'in Discord to help you!')
    async def start(self, ctx):
        # Remove this check when Lokeon has finished rewriting.
        if dimsecret.debug:
            await ctx.send('⚠DimBot is currently in **DEBUG** mode.'
                           ' I cannot receive messages from Lokeon, also things may not work as expected!⚠\n')
        await self.boot_instance(ctx, dimsecret.bruck_instance_id, 'ap-southeast-1')
