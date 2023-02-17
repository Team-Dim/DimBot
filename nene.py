import json
import re

import discord
import openai
from discord.ext import commands

import missile


fine_tune_stop = '\n\n###\n\n'


async def ask(prompt:str, model='text-curie-001', temperature=0.7, max_tokens=250, stop=None, txt_only=False, clean=True):
    if stop is None:
        stop = ['DimBot:']
    r = await openai.Completion.acreate(
        model=model,
        prompt=prompt,
        temperature=temperature, # 0.9
        max_tokens=max_tokens, # 150
        top_p=1,
        frequency_penalty=0.0,
        presence_penalty=0.6, # 0.6
        stop=stop
    )
    if clean:
        r['choices'][0]['text'] = r['choices'][0]['text'].replace('@', '**@**')
    if txt_only:
        return r['choices'][0]['text']
    return r


class Nene(missile.Cog):

    def __init__(self, bot):
        super().__init__(bot, 'Nene')
        self.no_ai = []

    @missile.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.content.startswith(self.bot.user.mention) or \
                (msg.reference and msg.reference.cached_message and msg.reference.cached_message.author == self.bot.user
                and msg.reference.cached_message.id not in self.no_ai):
            my_name = msg.guild.me.display_name if msg.guild else self.bot.user.name
            # print(msg.clean_content[len(my_name)+1:])
            ref = msg.reference
            msgs = [msg]
            while ref and ref.cached_message:
                msgs.append(ref.cached_message)
                ref = ref.cached_message.reference
            participants, convo = [], []
            for m in reversed(msgs):
                if m.author != self.bot.user and m.author.display_name not in participants:
                    participants.append(m.author.display_name)
                convo.append(f'{m.author.display_name}: {m.clean_content}')
            lf = '\n'
            prompt = f"{my_name} is a cute, smart, light-headed and kind girl. She also has a nickname 'Nene'.\n" \
                     f"The following is a conversation.\n\n{lf.join(convo)}\n{my_name}:"
            response = await ask(prompt, stop=[f'{my_name}:', f'{participants[0]}:'])
            usage = response['usage']
            reason = response['choices'][0]['finish_reason']
            response = response['choices'][0]['text']
            await msg.reply(response)
            await self.bot.get_cog('Hamilton').bot_test.send(embed=missile.Embed(str(usage['total_tokens']), reason))

    @commands.group(invoke_without_command=True)
    async def ai(self, ctx, *, prompt):
        """
        Commands for controlling the behaviour of the AI.
        """
        if await self.bot.is_owner(ctx.author):
            await ctx.reply(await ask(prompt, 'text-davinci-003', txt_only=True))
        else:
            self.bot.help_command.context = ctx
            await self.bot.help_command.send_group_help(ctx.command)

    @ai.command(brief='Sets your self introduction')
    @commands.cooldown(rate=3, per=3600.0, type=commands.BucketType.user)
    async def intro(self, ctx):
        """You can write a self introduction. The bot will learn from it and when there are questions about you, it will
         answer based on your intro."""
        para: str = await self.bot.ask_msg(
            ctx,
            'Tell me about yourself using first-person narrative. Please reply this message in 10 minutes. '
            'You can only change this 3 times per hour.',
            600)
        if not para:
            return
        if fine_tune_stop in para:
            await ctx.reply(f'The sequence ``###`` is not allowed.')
            return
        path = f'ai_data/{ctx.author.id}.json'
        try:
            with open(path, 'r') as f:
                d = json.load(f)
        except FileNotFoundError:
            d = {}
        d['intro'] = para
        with open(path, 'w') as f:
            json.dump(d, f)
        await ctx.reply('Thanks for telling me!')


    @ai.command(brief='Answer random questions to train the AI')
    async def qa(self, ctx):
        """The bot will keep asking random questions about you. Your reply will be studied by the AI.
        You have 30s to answer each question. When time is out, it will stop asking."""
        path = f'ai_data/{ctx.author.id}.json'
        try:
            with open(path, 'r') as f:
                d = json.load(f)
        except FileNotFoundError:
            d = {}
        while True:
            q = await ask('Ask a random question about me.', temperature=1, txt_only=True)
            q = q.replace('\n', '')
            a = await self.bot.ask_msg(ctx, q, 30)
            if a:
                d[q] = a
            else:
                with open(path, 'w') as f:
                    json.dump(d, f)
                await ctx.reply('Thanks for answering those questions!')
                return



