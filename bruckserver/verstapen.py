import boto3
from discord.ext import commands

import dimsecret
from bruckserver.albon import Albon
from missile import Missile


__version__ = '1.3.1'


class Verstapen(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Verstapen')
        self.http_not_started = True  # Whether Albon has been started
        self.albon = Albon(bot.missile.get_logger('Albon'))

    @commands.Cog.listener()
    async def on_ready(self):
        self.logger.debug('on_ready')

    async def boot_instance(self, ctx, instance_id: str, region_id: str):
        """Booting the AWS instance"""
        msg = await ctx.send('Connecting to Amazon Web Service...')
        self.logger.info('Connecting to AWS')
        session = boto3.session.Session(  # Initialises session to AWS via boto3
            region_name=region_id,
            aws_access_key_id=dimsecret.aws_access_key,
            aws_secret_access_key=dimsecret.aws_secret_key
        )
        ec2 = session.resource('ec2')  # Elastic Compute Cloud
        ssm = session.client('ssm')  # Systems Manager
        self.logger.debug('Fetching SSM parameter')
        # Fetches the region name of the Minecraft server instance
        response = ssm.get_parameter(Name=f'/aws/service/global-infrastructure/regions/{region_id}/longName')
        region_name = response['Parameter']['Value']
        await Missile.append_message(msg, f'Checking if instance *{instance_id}* is already running...')
        instance = ec2.Instance(instance_id)  # Fetches details of the remote instance
        if instance.state['Code'] != 80:  # Code 80 means Stopped. Don't send start request if instance is running.
            await Missile.append_message(msg, 'Instance is already running')
        else:
            msg = await ctx.send('Sending start request...')
            instance.start()  # Sends an instance start request to AWS
            await Missile.append_message(msg, "Waiting for the instance to be booted...")
            instance.wait_until_running()  # Waits until AWS responses that the instance has successfully started
            await Missile.append_message(msg, 'Instance has successfully started')
        await Missile.append_message(
            msg,
            f'in {region_id} **"{region_name}"**. IP address: **{instance.public_ip_address}** ',
            delimiter=' '
        )  # Reports the IP address of the instance; The IP address is dynamic if the server shut down completely
        # Adds the Discord channel to the list of channels to receive Lokeon events.
        self.albon.add_channel(ctx.channel)
        if self.http_not_started:
            await self.albon.run_server()  # Start Albon if its not running
            self.http_not_started = False

    @commands.command()
    @Missile.is_rainbow_cmd_check()
    async def start(self, ctx):
        """Launches the bruckserver Minecraft server"""
        if dimsecret.debug:
            await ctx.send('⚠DimBot is currently in **DEBUG** mode.'
                           ' I cannot receive messages from Lokeon, also things may not work as expected!⚠\n')
        await self.boot_instance(ctx, dimsecret.bruck_instance_id, 'ap-southeast-1')
