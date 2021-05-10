import asyncio

import boto3
from discord.ext import commands

import dimsecret
import missile
import tribe
from bruckserver.pythania import Albon


class Verstapen(missile.Cog):
    """Connects to AWS and communicates with a minecraft server instance.
    Version 2.0.1"""

    def __init__(self, bot):
        super().__init__(bot, 'Verstapen')
        self.albon = Albon(bot)
        bot.loop.create_task(self.albon.run_server())

    async def boot_instance(self, ctx, region_id: str, level: int):
        msg = await ctx.send('Connecting to Amazon Web Service...')
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
                await missile.append_msg(msg, '⚠No AMI! Please ask Dim for help!')
                return
            ami = ami[0]
            inst_type = 't4g.medium' if level else 't4g.small'
            await missile.append_msg(msg, f"Requesting new **{inst_type}** instance")
            spot_request = ec2.request_spot_instances(
                LaunchSpecification={
                    'SecurityGroups': ['default'],
                    'BlockDeviceMappings': ami['BlockDeviceMappings'],
                    'Placement': {
                        'AvailabilityZone': 'ap-southeast-1a',
                    },
                    'ImageId': ami['ImageId'],
                    'KeyName': 'SG',
                    'InstanceType': inst_type,
                    'EbsOptimized': True,
                    'Monitoring': {'Enabled': True}
                }
            )['SpotInstanceRequests'][0]
            await missile.append_msg(msg, 'Waiting for AWS to provide an instance...')
            spot_info = {"State": ""}
            while spot_info['State'] != 'active':
                await asyncio.sleep(5)
                spot_info = ec2.describe_spot_instance_requests(
                    SpotInstanceRequestIds=[spot_request['SpotInstanceRequestId']]
                )
                spot_info = spot_info['SpotInstanceRequests'][0]
            await missile.append_msg(
                msg, 'AWS has fulfilled our request in '
                     f'*{spot_request["LaunchSpecification"]["Placement"]["AvailabilityZone"]}*')
            instance_id = spot_info['InstanceId']
            ec2.create_tags(Resources=[instance_id], Tags=[{'Key': 'Name', 'Value': 'bruck3 Spot'}])
            instance = ec2.describe_instances(InstanceIds=[instance_id])
        instance = instance['Reservations'][0]['Instances'][0]
        await missile.append_msg(msg, f'IP: **{instance["PublicIpAddress"]}**')

    @commands.command()
    @missile.in_guilds(tribe.guild_id, 686397146290979003)
    async def start(self, ctx, level: int = 0):
        if level == 0 or level == 1:
            self.bot.loop.create_task(self.boot_instance(ctx, 'ap-southeast-1', level))
        else:
            await ctx.send('Activating Albon')
        self.albon.add_channel(ctx.channel)

    @commands.command()
    @missile.is_rainbow()
    async def post(self, ctx, path: str):
        async with self.bot.session.post('http://localhost/' + path) as r:
            await ctx.reply(f"{r.status}: {await r.text()}")

    @commands.command()
    async def players(self, ctx: commands.Context):
        msg = f"There are **{len(self.albon.online)}** players online:\n"
        msg += '\n'.join(self.albon.online)
        await ctx.reply(msg)
