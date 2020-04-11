import boto3
from discord.ext import commands

import dimsecret
from missile import Missile


class Vireg(commands.Cog):

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Vireg')
        self.region_id = 'eu-north-1' if dimsecret.debug else 'ap-southeast-1'
        self.logger.debug('Connecting to AWS session')
        session = boto3.session.Session(
            region_name=self.region_id,
            aws_access_key_id=dimsecret.aws_access_key,
            aws_secret_access_key=dimsecret.aws_secret_key
        )
        self.ec2 = session.resource('ec2')
        self.ssm = session.client('ssm')
        self.logger.debug('Fetching SSM parameter')
        response = self.ssm.get_parameter(Name=f'/aws/service/global-infrastructure/regions/{self.region_id}/longName')
        self.region_name = response['Parameter']['Value']

    @commands.command()
    async def start(self, ctx):
        instance_id = 'i-0684c778f22b3980b' if dimsecret.debug else 'i-0429c83bc78edcbae'
        msg = await ctx.send(f'Checking if instance *{instance_id}* is already running...')
        instance = self.ec2.Instance(instance_id)
        if instance.state['Code'] != 80:
            await Missile.append_message(msg, 'Instance is already running')
        else:
            msg = await ctx.send('Starting instance...')
            instance.start()
            await Missile.append_message(msg, "Start request has been sent. Waiting for the instance to be booted...")
            instance.wait_until_running()
            await Missile.append_message(msg, 'Instance has successfully started')
        await Missile.append_message(
            msg,
            f'in {self.region_id} **"{self.region_name}"**. IP address: **{instance.public_ip_address}** ',
            delimiter=' '
        )
