from typing import Optional, Union

import discord
from discord.ext import commands

import missile


class Dimond(commands.Cog):
    """Named by <@98591077975465984>
    Report users/channels/servers details. Literally CIA
    Version: 1.3"""

    def __init__(self, bot):
        self.bot: missile.Bot = bot

    @commands.group(invoke_without_command=True)
    async def info(self, ctx):
        """Commands for showing info of various objects"""
        await self.bot.get_command('help info')()

    @info.command(aliases=('u',), brief='Shows user info')
    async def user(self, ctx, u: discord.User = None):
        """`info user [user]`"""
        # https://discordpy.readthedocs.io/en/latest/api.html#discord.User
        u = u if u else ctx.author
        desc = f"Send `{self.bot.default_prefix}info f [user]` for flag details,\n`{self.bot.default_prefix}info p " \
               "[user|channel] [channel]` for permission details"
        emb = missile.Embed(str(u), desc, thumbnail=u.avatar_url)
        if u.avatar:
            emb.set_footer(text='Avatar hash: ' + u.avatar)
        emb.add_field(name='❄ ID', value=u.id)
        emb.add_field(name='Is bot?', value=u.bot)
        emb.add_field(name='Public flags', value=u.public_flags.value)
        emb.add_field(name='Created at', value=u.created_at)
        member: Optional[discord.Member] = None
        # A hacky way to try getting data that can only be accessed as a Member
        for g in u.mutual_guilds:
            m = g.get_member(u.id)
            if m:
                member = m
                if m.voice:  # Searches whether the 'member' is in a VC
                    break  # A user can only be in 1 VC
        if member:  # Data that can only be accessed as a Member
            emb.add_field(name='Number of activities', value=str(len(member.activities)) if member.activities else '0')
            stat = str(member.status)
            if member.desktop_status != discord.Status.offline:
                stat += ' 💻'
            if member.mobile_status != discord.Status.offline:
                stat += ' 📱'
            if member.web_status != discord.Status.offline:
                stat += ' 🌐'
            emb.add_field(name='Status', value=stat)
            if member.voice:
                v_state = str(member.voice.channel.id)
                if member.voice.self_mute:
                    v_state += ' **Muted**'
                if member.voice.self_deaf:
                    v_state += ' **Deaf**'
                if member.voice.self_stream:
                    v_state += ' **Streaming**'
                emb.add_field(name='Voice channel ❄ ID', value=v_state)
        # Guild specific data
        if ctx.guild:
            member = ctx.guild.get_member(u.id)
            if member:
                emb.add_field(name='Joined at', value=member.joined_at)
                emb.add_field(name='Pending member?', value=member.pending)
                emb.add_field(name='Nitro boosting server since', value=member.premium_since)
                if len(member.roles) > 1:
                    emb.add_field(name='Roles', value=' '.join([role.mention for role in member.roles[1:]][::-1]))
                emb.colour = member.color
        emb.set_author(name=member.display_name if member else u.name, icon_url=u.default_avatar_url)
        await ctx.reply(embed=emb)

    @info.command(aliases=('f',), brief='Display the public flags of a user')
    async def flags(self, ctx, u: discord.User = None):
        """`info flags [u]`
        u: The user to inspect. Defaults to the command sender."""
        # https://discordpy.readthedocs.io/en/latest/api.html#discord.PublicUserFlags
        u = u if u else ctx.author
        bin_value = f'{u.public_flags.value:b}'
        hex_value = f'{u.public_flags.value:X}'
        emb = missile.Embed(u.name + "'s public flags",
                            f"{u.public_flags.value}, 0b{bin_value.zfill(18)}, 0x{hex_value.zfill(5)}")
        emb.add_field(name='Verified bot developer', value=u.public_flags.verified_bot_developer)  # 2^17
        emb.add_field(name='Verified bot', value=u.public_flags.verified_bot)  # 2^16
        if u.public_flags.bug_hunter_level_2:
            emb.add_field(name='Bug hunter', value='**Level 2**')  # 2^14
        else:
            emb.add_field(name='Bug hunter', value=u.public_flags.bug_hunter)  # 2^3
        emb.add_field(name='Discord system', value=u.public_flags.system)  # 2^12
        emb.add_field(name='Team User', value=u.public_flags.team_user)  # 2^10
        emb.add_field(name='Early supporter', value=u.public_flags.early_supporter)  # 2^9
        if u.public_flags.hypesquad_balance:
            emb.add_field(name='HypeSquad', value='Balance')  # 2^8
        elif u.public_flags.hypesquad_brilliance:
            emb.add_field(name='HypeSquad', value='Brilliance')  # 2^7
        elif u.public_flags.hypesquad_bravery:
            emb.add_field(name='HypeSquad', value='Bravery')  # 2^6
        else:
            emb.add_field(name='HypeSquad', value=u.public_flags.hypesquad)  # 2^2
        emb.add_field(name='Discord partner', value=u.public_flags.partner)  # 2^1
        emb.add_field(name='Discord employee', value=u.public_flags.staff)  # 2^0
        await ctx.reply(embed=emb)

    @info.command(aliases=('p',), brief="Shows a user's permission server/channel wise")
    @missile.guild_only()
    async def permissions(
            self, ctx,
            arg1: Union[discord.Member, discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel,
                        discord.StageChannel, None] = None,
            arg2: Union[discord.TextChannel, discord.VoiceChannel, discord.CategoryChannel,
                        discord.StageChannel, None] = None):
        """`info permissions [arg1] [arg2]`
        arg1 can be either a Member or a Channel
        arg2 can only be a Channel.
        You can have the following combinations:
        ```info p Member
        info p Channel
        info p Member Channel```
        *Note:* Channel can only be TextChannel, VoiceChannel, Category or StageChannel."""
        if arg1:
            if type(arg1) == discord.Member:
                mem = arg1
                if arg2:
                    channel = arg2
                else:
                    channel = None
            else:
                channel = arg1
                mem = ctx.author
        else:
            mem = ctx.author
            channel = None
        if channel:  # If no channel specified, then  check permission server-wise
            perm = channel.permissions_for(mem)
            title = channel.name
        else:  # Check permission of the member in that channel
            perm = mem.guild_permissions
            title = 'the server'

        # https://discordpy.readthedocs.io/en/latest/api.html#discord.Permissions
        bin_value = f'{perm.value:b}'
        hex_value = f'{perm.value:X}'
        emb = missile.Embed(f'Permissions for {mem.name} in {title}',
                            f"{perm.value}, 0b{bin_value.zfill(30)}, 0x{hex_value.zfill(8)}")
        emb.add_field(name='Manage webhooks', value=perm.manage_webhooks)  # 2^29
        emb.add_field(name='Manage permissions and roles', value=perm.manage_permissions)  # 2^28
        emb.add_field(name='Manage nicknames', value=perm.manage_nicknames)  # 2^27
        emb.add_field(name='Change nickname', value=perm.change_nickname)  # 2^26
        emb.add_field(name='Use voice activation', value=perm.use_voice_activation)  # 2^25
        emb.add_field(name='Move members to voice channels', value=perm.move_members)  # 2^24
        emb.add_field(name='Deaf members', value=perm.deafen_members)  # 2^23
        emb.add_field(name='Mute members', value=perm.mute_members)  # 2^22
        emb.add_field(name='Speak', value=perm.speak)  # 2^21
        emb.add_field(name='Connect to voice channels', value=perm.connect)  # 2^20
        emb.add_field(name='View server insights', value=perm.view_guild_insights)  # 2^19
        emb.add_field(name='Use external emojis', value=perm.external_emojis)  # 2^18
        emb.add_field(name='Mention everyone', value=perm.mention_everyone)  # 2^17
        emb.add_field(name='Read message history', value=perm.read_message_history)  # 2^16
        emb.add_field(name='Attach files', value=perm.attach_files)  # 2^15
        emb.add_field(name='Embed links', value=perm.embed_links)  # 2^14
        emb.add_field(name='Manage messages', value=perm.manage_messages)  # 2^13
        emb.add_field(name='Send Text-to-Speech', value=perm.send_tts_messages)  # 2^12
        emb.add_field(name='Send messages', value=perm.send_messages)  # 2^11
        emb.add_field(name='View channel and read messages', value=perm.read_messages)  # 2^10
        emb.add_field(name='Stream', value=perm.stream)  # 2^9
        emb.add_field(name='Priority speaker', value=perm.priority_speaker)  # 2^8
        emb.add_field(name='View audit log', value=perm.view_audit_log)  # 2^7
        emb.add_field(name='Add reactions', value=perm.add_reactions)  # 2^6
        await ctx.reply(content=f"Manage server: **{perm.manage_guild}** "  # 2^5
                                f"Manage channels: **{perm.manage_channels}** "  # 2^4
                                f"Administrator: **{perm.administrator}** "  # 2^3
                                f"Ban members: **{perm.ban_members}** "  # 2^2
                                f"Kick members: **{perm.kick_members}** "  # 2^1
                                f"Create invites: **{perm.create_instant_invite}**", embed=emb)  # 2^0

    @info.command(aliases=('r',), brief='Shows role info')
    @missile.guild_only()
    async def role(self, ctx: commands.Context, r: discord.Role):
        """info role <r>"""
        emb = discord.Embed(title=r.name, color=r.color)
        emb.set_author(name=f'Color: #{r.color.value:X}')
        if r.is_bot_managed():
            emb.description = 'Bot role: ' + self.bot.get_user(r.tags.bot_id).mention
        elif r.is_default():
            emb.description = 'Default role'
        elif r.is_integration():
            emb.description = 'Integration role: ❄ID ' + str(r.tags.integration_id)
        elif r.is_premium_subscriber():
            emb.description = 'Nitro Boost role'
        emb.add_field(name='❄ ID', value=r.id)
        # noinspection PyTypeChecker
        emb.add_field(name='Member count', value=len(r.members))
        emb.add_field(name='Displays separately', value=r.hoist)
        emb.add_field(name='Created at', value=r.created_at)
        emb.add_field(name='Permissions', value=f'0x{r.permissions.value:X}')
        emb.add_field(name='Position', value=r.position)
        await ctx.reply(embed=emb)

    @info.command(brief='Shows info about a voice channel')
    async def vc(self, ctx: commands.Context, ch: discord.VoiceChannel):
        """`info vc <voice channel>`
        PM the command if the VC is not in that server."""
        emb = missile.Embed(ch.name)
        if not ctx.guild:
            emb.add_field(name='Server ❄ID', value=ch.guild.id)
        emb.add_field(name='Bit rate (kbps)', value=ch.bitrate // 1000)
        emb.add_field(name='Created at', value=ch.created_at)
        await ctx.reply(embed=emb)

    # noinspection PyTypeChecker
    @info.command(aliases=('s',), brief='Shows info about a server')
    async def server(self, ctx: commands.Context, s: discord.Guild = None):
        """`info server [s]`
        s: The server, usually identified by its ID. Defaults to the server that the command was sent."""
        if not s:
            if ctx.guild:
                s = ctx.guild
            else:
                await ctx.reply('You must specify a server if you are sending this command in PM!')
                return
        emb = missile.Embed(s.name)
        if s.description:
            emb.description = s.description
        emb.add_field(name='❄ ID', value=s.id)
        emb.add_field(name='Owner ID', value=s.owner_id)
        emb.add_field(name='Created at', value=s.created_at)
        emb.add_field(name='Member count', value=s.member_count)
        emb.add_field(name='Region', value=s.region)
        if s.features:  # https://discordpy.readthedocs.io/en/latest/api.html#discord.Guild.features
            emb.add_field(name='Features', value=',\n'.join(s.features))
        emb.add_field(name='Max members', value=s.max_members)
        emb.add_field(name='Max presences', value=s.max_presences)
        if s.me.guild_permissions.manage_webhooks:
            emb.add_field(name='Webhooks', value=len(await s.webhooks()))
        if s.me.guild_permissions.manage_guild:
            emb.add_field(name='Integrations', value=len(await s.integrations()))
            emb.add_field(name='Invites', value=len(await s.invites()))
        emb.set_thumbnail(url=s.icon_url)
        await ctx.reply(embed=emb)

    @info.command(aliases=('e',), brief='Shows info about a custom (non-Unicode) emoji')
    async def emoji(self, ctx: commands.Context, e: Union[discord.Emoji, discord.PartialEmoji]):
        """`info emoji <emoji>`
        The emoji can be from other servers."""
        emb = missile.Embed(e.name)
        # noinspection PyTypeChecker
        emb.set_author(name=e)
        emb.set_thumbnail(url=e.url)
        emb.add_field(name='❄ ID', value=e.id)
        emb.add_field(name='Created at', value=e.created_at)
        if isinstance(e, discord.Emoji):
            emb.add_field(name='Server ID', value=e.guild_id)
            if e.user:
                emb.add_field(name='Creator', value=e.user)
            if e.roles:
                emb.add_field(name='Usable roles', value=''.join(r.mention for r in e.roles))
        await ctx.reply(embed=emb)

    @emoji.error
    async def emoji_error(self, ctx, error):
        if isinstance(error, commands.errors.BadUnionArgument):
            await ctx.reply('Unknown emoji. This command currently does not support Unicode emojis.')

    @info.command(aliases=('w',), brief='Shows info about a webhook')
    @missile.guild_only()
    @commands.bot_has_guild_permissions(manage_webhooks=True)
    async def webhook(self, ctx: commands.Context, name, channel: discord.TextChannel = None):
        """`info webhook <name> [channel]`
        name: The webhook's name
        In some cases you will encounter duplicate webhook names in different channels.
        Specify `channel` to filter it."""
        for webhook in await ctx.guild.webhooks():
            if webhook.name == name and (channel is None or webhook.channel == channel):
                emb = missile.Embed(f'❄ ID: {webhook.id}')
                emb.add_field(name='Created at', value=webhook.created_at)
                emb.add_field(name='Channel', value=webhook.channel.mention)
                emb.add_field(name='Type', value=webhook.type)
                await ctx.reply(embed=emb)
                return
        await ctx.reply(f"Webhook user '{name}' not found.")

    @info.command(aliases=('sinv',))
    @missile.guild_only()
    @commands.bot_has_guild_permissions(manage_guild=True)
    async def server_invite(self, ctx: commands.Context):
        """Lists invite codes of a server"""
        emb = missile.Embed(description='')
        for inv in await ctx.guild.invites():
            to_be_added = f"[{inv.code}]({inv.url}) "
            if len(emb.description + to_be_added) < 2045:
                emb.description += to_be_added
            else:
                emb.title = 'So many invites lmfao'
                emb.description += '...'
                break
        await ctx.reply(embed=emb)

    @info.command(aliases=('inv',), brief='Shows info about an invite')
    async def invite(self, ctx: commands.Context, inv: discord.Invite):
        """`info invite <inv>`
        `inv` is usually the invite code or the invite link."""
        emb = missile.Embed(inv.code, url=inv.url)
        emb.add_field(name='Server ID', value=inv.guild.id)
        emb.add_field(name='Channel', value=inv.channel.mention)
        if inv.guild in self.bot.guilds and inv.guild.me.guild_permissions.manage_guild:
            for i in await inv.guild.invites():
                if i.code == inv.code:
                    emb.add_field(name='Uses', value=i.uses)
                    emb.add_field(name='Created at', value=i.created_at)
                    if inv.inviter:
                        emb.add_field(name='Inviter', value=i.inviter.mention)
                    emb.add_field(name='Expires in', value=i.max_age)
                    emb.add_field(name='Max uses', value=i.max_uses)
                    emb.add_field(name='Revoked', value=i.revoked)
                    emb.add_field(name='Only grants temporary membership', value=i.temporary)
        await ctx.reply(embed=emb)

    @info.command(aliases=('sint',))
    @missile.guild_only()
    @commands.bot_has_guild_permissions(manage_guild=True)
    async def server_integrations(self, ctx: commands.Context):
        """Lists server integrations"""
        m = 'Please note that this command is currently for testing purposes only!\n'
        for i in await ctx.guild.integrations():
            m += str(i) + '\n'
        await ctx.reply(m)

    @info.command(aliases=('int',))
    @missile.guild_only()
    @commands.bot_has_guild_permissions(manage_guild=True)
    async def integration(self, ctx: commands.Context):
        """Shows info of an integration"""
        await ctx.reply('Coming soon!')
