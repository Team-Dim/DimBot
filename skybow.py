from tempfile import TemporaryFile

import discord
from discord.ext import commands
from pytube import Search

import missile


class VoiceMeta:

    def __init__(self, vc, s_y, buffer):
        self.vc = vc
        self.loop = False
        self.buffer = buffer
        self.queue = [s_y]
        self.progress = True


class SkyBow(commands.Cog):
    """Audio streaming
    Version: 1.0"""

    def __init__(self, bot):
        self.bot = bot
        self.vcs = {}

    def init_play(self, vm: VoiceMeta, kbps):
        def play(e):
            if vm.vc.is_connected():
                kbps = vm.vc.channel.bitrate // 1000
                if vm.loop:
                    vm.buffer.seek(0)
                    vm.vc.play(discord.FFmpegOpusAudio(vm.buffer, bitrate=kbps, pipe=True), after=play)
                elif len(vm.queue) > 1:
                    del vm.queue[0]
                    vm.buffer.close()
                    vm.buffer = TemporaryFile()
                    vm.progress = True

                    @vm.queue[0][1].register_on_progress_callback
                    def on_progress(s, c, remain):
                        if vm.progress:
                            print('Start playing', vm.queue)
                            vm.buffer.seek(0)
                            vm.vc.play(discord.FFmpegOpusAudio(vm.buffer, bitrate=kbps, pipe=True), after=play)
                            vm.progress = False

                    vm.queue[0][0].stream_to_buffer(vm.buffer)
                else:
                    del self.vcs[vm.vc.channel.id]
                    self.bot.loop.create_task(vm.vc.disconnect())
        if len(vm.vc.channel.members) > 1:
            vm.buffer.seek(0)
            vm.vc.play(discord.FFmpegOpusAudio(vm.buffer, bitrate=kbps, pipe=True), after=play)
        elif vm.vc.is_connected():
            self.bot.loop.create_task(vm.vc.disconnect())

    @commands.Cog.listener()
    async def on_voice_state_update(self, m, before, after: discord.VoiceState):
        channel = before.channel or after.channel
        if (len(channel.members) == 1 and channel.members[0] == channel.guild.me)\
                or (m == channel.guild.me and not after.channel)\
                and channel.id in self.vcs:
            self.bot.loop.create_task(self.vcs[channel.id].vc.disconnect())
            self.vcs.pop(channel.id)

    @missile.vc_only()
    @commands.command(aliases=('yt',), brief='Streams a YouTube audio')
    async def youtube(self, ctx: commands.Context, *, query: str):
        channel = ctx.author.voice.channel  # So that it can continue even if the user dc
        kbps = channel.bitrate // 1000
        buffer = TemporaryFile()
        yt = Search(query).results
        if yt:
            yt = Search(query).results[0]
        else:
            await ctx.reply('Wtf no results from YouTube <:what:885927400691605536>')
            return
        audios = yt.streams.filter(only_audio=True, audio_codec='opus').order_by('abr')
        stream = audios[-1]
        for audio in audios:
            if int(audio.abr[:-4]) >= kbps:
                stream = audio
                break
        if channel.id in self.vcs:
            self.vcs[channel.id].queue.append((stream, yt))
            await ctx.reply(f'Added `{yt.title}` to the queue!')
            return
        if not len(channel.members):
            return
        await ctx.reply(f'Playing `{yt.title}` src{stream.abr}')
        vc = await channel.connect()
        self.vcs[channel.id] = VoiceMeta(vc, (stream, yt), buffer)
        vm = self.vcs[channel.id]

        @yt.register_on_progress_callback
        def on_progress(s, c, remain):
            if vm.progress:
                print('Start playing', vm.queue)
                self.init_play(vm, kbps)
                vm.progress = False

        stream.stream_to_buffer(buffer)

    @missile.vc_only()
    @commands.command(brief='Toggles looping for the voice client')
    async def loop(self, ctx: commands.Context):
        if ctx.author.voice.channel.id in self.vcs:
            loo = self.vcs[ctx.author.voice.channel.id].loop
            loo = not loo
            self.vcs[ctx.author.voice.channel.id].loop = loo
            await ctx.reply(f"I will no{'w' if loo else ' longer'} loop the current sound track!")
        else:
            await ctx.reply('I am not playing anything!')

    @missile.vc_only()
    @commands.command(brief='Shows the queue of the voice client')
    async def queue(self, ctx: commands.Context):
        channel = ctx.author.voice.channel
        if channel.id in self.vcs:
            msg = ''
            for i, s_y in enumerate(self.vcs[ctx.author.voice.channel.id].queue):
                to_add = f'**{i}.** `{s_y[1].title}`\n'
                if len(msg + to_add) > 2000:
                    break
                msg += to_add
            await ctx.reply(msg)
        else:
            await ctx.reply('There is nothing in the queue!')

    @missile.vc_only()
    @commands.command(brief='Skips the nth sound track')
    async def skip(self, ctx: commands.Context, n: int = 0):
        """`skip [n]`
        n: The index of the sound track in the queue to be skipped. Defaults to 0. Should be at least 0 and smaller than
        length of the queue"""
        channel = ctx.author.voice.channel
        if channel.id in self.vcs and 0 <= n < len(self.vcs[channel.id].queue):
            vm = self.vcs[channel.id]
            del vm.queue[n]
            if not n:
                vm.vc.pause()
                if vm.queue:
                    vm.buffer.close()
                    vm.buffer = TemporaryFile()
                    vm.progress = True
                    kbps = channel.bitrate // 1000

                    @vm.queue[0][1].register_on_progress_callback
                    def on_progress(s, c, remain):
                        if vm.progress:
                            print('Start playing', vm.queue)
                            self.init_play(vm, kbps)
                            vm.progress = False

                    vm.queue[0][0].stream_to_buffer(vm.buffer)
                else:
                    self.vcs.pop(channel.id)
                    await vm.vc.disconnect()
            await ctx.reply('Skipped!')
        else:
            await ctx.reply('There is nothing to skip or your provided number is invalid!')
