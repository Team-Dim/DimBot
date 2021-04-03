import asyncio

import boto3
from discord.ext import commands

import dimsecret
import tribe
from bruckserver.pythania import Albon
from missile import Missile


class Verstapen(commands.Cog):
    """Connects to AWS and communicates with a minecraft server instance.
    Version 2.0"""

    def __init__(self, bot):
        self.bot = bot
        self.logger = bot.missile.get_logger('Verstapen')
        self.http_not_started = True
        self.albon = Albon(bot)

    async def boot_instance(self, ctx, region_id: str, level: int):
        msg = await ctx.send('Tips: If server tps always below 10, `d.start 2`\nConnecting to Amazon Web Service...')
        self.logger.info('Connecting to AWS')
        session = boto3.session.Session(
            region_name=region_id,
            aws_access_key_id=dimsecret.aws_access_key,
            aws_secret_access_key=dimsecret.aws_secret_key
        )
        ec2 = session.client('ec2')
        instance = ec2.describe_instances(
            Filters=[
                {
                    'Name': 'instance-state-name',
                    'Values': ['running']
                },
                {
                    'Name': 'tag:Name',
                    'Values': ['bruck3 Spot']
                }
            ]
        )
        if not instance['Reservations']:  # There are no active bruck servers
            ami = ec2.describe_images(
                Filters=[{
                    'Name': 'name',
                    'Values': ['bruck3 SPOT']
                }],
                Owners=['self']
            )['Images']
            if not ami:
                await Missile.append_message(msg, '⚠No AMI! Please ask Dim for help!')
                return
            ami = ami[0]
            inst_type = {0: 't4g.small', 1: 't4g.medium', 2: 'c6g.large'}
            await Missile.append_message(msg, f"Requesting new **{inst_type[level]}** instance")
            spot_request = ec2.request_spot_instances(
                LaunchSpecification={
                    'SecurityGroups': ['default'],
                    'BlockDeviceMappings': ami['BlockDeviceMappings'],
                    'Placement': {
                        'AvailabilityZone': 'ap-southeast-1a',
                    },
                    'ImageId': ami['ImageId'],
                    'KeyName': 'SG',
                    'InstanceType': inst_type[level],
                    'EbsOptimized': True,
                    'Monitoring': {'Enabled': True}
                }
            )['SpotInstanceRequests'][0]
            await Missile.append_message(msg, 'Waiting for AWS to provide an instance...')
            spot_info = {"State": ""}
            while spot_info['State'] != 'active':
                await asyncio.sleep(5)
                spot_info = ec2.describe_spot_instance_requests(SpotInstanceRequestIds=
                                                                [spot_request['SpotInstanceRequestId']])
                spot_info = spot_info['SpotInstanceRequests'][0]
            await Missile.append_message(
                msg, 'AWS has fulfilled our request in '
                     f'*{spot_request["LaunchSpecification"]["Placement"]["AvailabilityZone"]}*')
            instance_id = spot_info['InstanceId']
            ec2.create_tags(Resources=[instance_id], Tags=[{'Key': 'Name', 'Value': 'bruck3 Spot'}])
            instance = ec2.describe_instances(InstanceIds=[instance_id])
        instance = instance['Reservations'][0]['Instances'][0]
        await Missile.append_message(msg, f'IP: **{instance["PublicIpAddress"]}**')

    @commands.command()
    @Missile.is_guild_cmd_check(tribe.guild_id, 686397146290979003)
    async def start(self, ctx, level: int = 0):
        self.albon.add_channel(ctx.channel)
        if self.http_not_started:
            self.http_not_started = False
            self.bot.loop.create_task(self.albon.run_server())
        if level < 0:
            await ctx.send('Albon activated.')
        elif level < 3:
            await self.boot_instance(ctx, 'ap-southeast-1', level)

    @commands.command()
    @Missile.is_rainbow_cmd_check()
    async def post(self, ctx, path: str):
        async with self.bot.missile.session.post('http://localhost/' + path) as r:
            await ctx.reply(f"{r.status}: {await r.text()}")
