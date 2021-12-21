import re
from tempfile import TemporaryFile

import discord
import psutil
import pytube.exceptions
from discord.ext import commands
from pytube import Search, YouTube

import missile


class VoiceMeta:

    def __init__(self, vc, s_y, buffer):
        self.vc = vc
        self.loop = False
        self.loopq = False
        self.buffer = buffer
        self.queue = [s_y]
        self.progress = True


class SkyBow(commands.Cog):
    """Audio streaming
    Version: 1.2"""

    def __init__(self, bot):
        self.bot = bot
        self.vcs = {}

    def clear(self, vm: VoiceMeta):
        process = psutil.Process()
        with process.oneshot():
            print(f'b4 clear: {process.memory_info()[0] / 1024 ** 2:.1f}')
        vm.buffer.close()
        with process.oneshot():
            print(f'Closed buffer: {process.memory_info()[0] / 1024 ** 2:.1f}')
        del vm.queue
        with process.oneshot():
            print(f'Done queue: {process.memory_info()[0] / 1024 ** 2:.1f}')
        self.bot.loop.create_task(vm.vc.disconnect())
        del self.vcs[vm.vc.channel.id]
        with process.oneshot():
            print(f'Deleted dict: {process.memory_info()[0] / 1024 ** 2:.1f}')

    def init_play(self, vm: VoiceMeta, kbps):
        def play(e):
            if vm.vc.is_connected():
                kbps = vm.vc.channel.bitrate // 1000
                if vm.loop:
                    vm.buffer.seek(0)
                    vm.vc.play(discord.FFmpegOpusAudio(vm.buffer, bitrate=kbps, pipe=True), after=play)
                else:
                    if vm.loopq:
                        vm.queue.append(vm.queue[0])
                    if vm.loopq or len(vm.queue) > 1:
                        del vm.queue[0]
                        vm.buffer.seek(0)
                        vm.progress = True

                        @vm.queue[0][1].register_on_progress_callback
                        def on_progress(s, c, remain):
                            if vm.progress:
                                process = psutil.Process()
                                with process.oneshot():
                                    print(f'on_progress: {process.memory_info()[0] / 1024 ** 2:.1f}')
                                print('Start playing', vm.queue)
                                vm.progress = False
                                vm.buffer.seek(0)
                                vm.vc.play(discord.FFmpegOpusAudio(vm.buffer, bitrate=kbps, pipe=True), after=play)

                        vm.queue[0][0].stream_to_buffer(vm.buffer)
                    else:
                        self.clear(vm)
        if len(vm.vc.channel.members) > 1:
            vm.buffer.seek(0)
            vm.vc.play(discord.FFmpegOpusAudio(vm.buffer, bitrate=kbps, pipe=True), after=play)
        elif vm.vc.is_connected():
            self.clear(vm)

    @commands.Cog.listener()
    async def on_voice_state_update(self, m, before, after: discord.VoiceState):
        channel = before.channel or after.channel
        if (len(channel.members) == 1 and channel.members[0] == channel.guild.me
                or (m == channel.guild.me and not after.channel))\
                and channel.id in self.vcs:
            self.clear(self.vcs[channel.id])

    @missile.vc_only()
    @commands.command(aliases=('yt',), brief='Streams a YouTube audio')
    async def youtube(self, ctx: commands.Context, *, query: str):
        channel = ctx.author.voice.channel  # So that it can continue even if the user dc
        kbps = channel.bitrate // 1000
        process = psutil.Process()
        with process.oneshot():
            print(f'Before tempfile: {process.memory_info()[0] / 1024 ** 2:.1f}')
        buffer = TemporaryFile()

        # Based on https://regexr.com/3dj5t
        if re.search(
                r"^((?:https?:)?//)?((?:www|m)\.)?(youtube\.com|youtu.be)(/(?:[\w\-]+\?v=|embed/|v/)?)([\w\-]+)(\S+)?$",
                query, re.IGNORECASE):
            yt = YouTube(query)
        else:
            yt = Search(query).results
            with process.oneshot():
                print(f'A lot of result: {process.memory_info()[0] / 1024 ** 2:.1f}')
            if yt:
                yt = Search(query).results[0]
            else:
                await ctx.reply('Wtf no results from YouTube <:what:885927400691605536>')
                return

        with process.oneshot():
            print(f'Result: {process.memory_info()[0] / 1024 ** 2:.1f}')
        try:
            audios = yt.streams.filter(only_audio=True, audio_codec='opus').order_by('abr')
        except pytube.exceptions.LiveStreamError:
            await ctx.reply('I cannot play live streams! <:chloedown:916051244135620709>')
            return
        except pytube.exceptions.VideoPrivate:
            await ctx.reply('This video is private! <:luigi:826479031012163624>')
            return
        stream = audios[-1]
        with process.oneshot():
            print(f'Got stream: {process.memory_info()[0] / 1024 ** 2:.1f}')
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

        # Add VM b4 first await to prevent a glitch where adding 2 songs at the same time will error
        self.vcs[channel.id] = VoiceMeta(None, (stream, yt), buffer)
        await ctx.reply(f'Playing `{yt.title}` src{stream.abr}')
        vc = await channel.connect()
        vm = self.vcs[channel.id]
        vm.vc = vc

        @yt.register_on_progress_callback
        def on_progress(s, c, remain):
            if vm.progress:
                with process.oneshot():
                    print(f'on_progress: {process.memory_info()[0] / 1024 ** 2:.1f}')
                print('Start playing', vm.queue)
                vm.progress = False
                self.init_play(vm, kbps)

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
    @commands.command(aliases=('loopq',), brief='Toggles queue looping for the voice client')
    async def loopqueue(self, ctx: commands.Context):
        if ctx.author.voice.channel.id in self.vcs:
            loo = self.vcs[ctx.author.voice.channel.id].loopq
            loo = not loo
            self.vcs[ctx.author.voice.channel.id].loopq = loo
            await ctx.reply(f"I will no{'w' if loo else ' longer'} loop the entire queue!")
        else:
            await ctx.reply('I am not playing anything!')

    @missile.vc_only()
    @commands.command(aliases=('que',), brief='Shows the queue of the voice client')
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
                    vm.buffer.seek(0)
                    kbps = channel.bitrate // 1000
                    vm.progress = True

                    @vm.queue[0][1].register_on_progress_callback
                    def on_progress(s, c, remain):
                        if vm.progress:
                            print('Start playing', vm.queue)
                            vm.progress = False
                            self.init_play(vm, kbps)

                    vm.queue[0][0].stream_to_buffer(vm.buffer)
                else:
                    self.clear(vm)
            await ctx.reply('Skipped!')
        else:
            await ctx.reply('There is nothing to skip or your provided number is invalid!')
