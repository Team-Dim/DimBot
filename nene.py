import asyncio
import json
import os
import re

import discord
import openai
from discord.ext import commands

import missile


fine_tune_stop = '\n\n###\n\n'


def qa_to_jsonl_str(uname, question, ans):
    return json.dumps({
        'prompt': f'DimBot: {question}\n{uname}:{fine_tune_stop}',
        'completion': ' ' + ans + fine_tune_stop
    })


class Nene(missile.Cog):

    def __init__(self, bot):
        super().__init__(bot, 'Nene')
        self.no_ai = []
        self.model = 'text-curie-001'

    async def ask(self, prompt:str, model=None, temperature=0.7, max_tokens=250,
                  stop=None, txt_only=False, clean=True):
        if stop is None:
            stop = ['DimBot: ']
        if model is None:
            model = self.model
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
        # if re.match(r'[\n ]*$', r['choices'][0]['text']):
        #     r['choices'][0]['text'] = "⚠️I don't know..."
        if clean:
                r['choices'][0]['text'] = r['choices'][0]['text'].replace('@', '**@**')
        if txt_only:
            return r['choices'][0]['text']
        return r

    #@missile.Cog.listener()
    async def on_ready(self):
        resp = await openai.FineTune.alist()
        self.model = resp.data[-1].fine_tuned_model
        self.logger.info('Set model to ' + self.model)

    @missile.Cog.listener()
    async def on_message(self, msg: discord.Message):
        if msg.content.startswith(self.bot.user.mention) or \
                (msg.reference and msg.reference.cached_message and msg.reference.cached_message.author == self.bot.user
                and msg.reference.cached_message.id not in self.no_ai and not msg.content.startswith(await self.bot.get_prefix(msg))):
            my_name = msg.guild.me.display_name if msg.guild else self.bot.user.name
            ref = msg.reference
            msgs = [msg]
            while ref and ref.cached_message:
                msgs.append(ref.cached_message)
                ref = ref.cached_message.reference
            participants, convo = [], []
            for m in reversed(msgs):
                if m.author != self.bot.user and m.author.display_name not in participants:
                    participants.append(m.author.display_name)
                convo_content = m.clean_content
                if m.content.startswith(self.bot.user.mention):
                    convo_content = m.clean_content[len(my_name)+1:]
                convo.append(f'{m.author.name}: {convo_content}')
            lf = '\n'
            prompt = f"{lf.join(convo)}\nDimBot:"
            # print(prompt)
            response = await self.ask(prompt, stop=[f'DimBot:', f'{participants[0]}:'])
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
            await ctx.reply(await self.ask(prompt, 'text-davinci-003', txt_only=True))
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
        d['Tell me about yourself.'] = para
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
        lf = '\n'
        counter = 0
        while counter < 3:
            try:
                if d:
                    prompt = f"Ask a new question about me. The following are some questions that you asked:\n\n{lf.join(d.keys())}"
                else:
                    prompt = 'Ask a question about me'

                q = await self.ask(
                    prompt
                    , model='text-curie-001', temperature=1, txt_only=True, stop=['?'])
                q = (q + '?').replace('\n', '')
                a = await self.bot.ask_msg(ctx, "__Please don't answer if I am not asking a question.__\n\n" + q, 30)
                if a:
                    d[q] = a
                    counter = 0
                else:
                    counter = 99
            except ValueError:
                counter += 1
        with open(path, 'w') as f:
            json.dump(d, f)
        if counter == 99:
            await ctx.reply('Thanks for answering those questions!')
        else:
            await ctx.reply("Looks like something is wrong, but I've managed to save your answers. "
                            "Thanks for answering those questions!")


    @ai.group(invoke_without_command=True, brief='Controlling models')
    @missile.is_rainbow()
    async def model(self, ctx):
        resp = await openai.Model.alist()
        print(resp)
        msg = ''
        for model in resp.data:
            if model.owned_by.startswith('user'):
                msg += f'{model.id}\n'
        if not msg:
            msg = 'No models'
        await ctx.reply(msg)

    @model.command(brief='Reset model.jsonl from collected data.')
    async def reset(self, ctx):
        lines = 0
        with open('ai_data/model.jsonl', 'w') as model:
            for file in os.listdir('ai_data'):
                if file.endswith('.json'):
                    with open('ai_data/' + file) as f:
                        d = json.load(f)
                    user = self.bot.get_user(int(file.split('.')[0])).name
                    for k, v in d.items():
                        model.write(qa_to_jsonl_str(user, k, v) + '\n')
                        lines += 1
        file = os.path.getsize('ai_data/model.jsonl')
        await ctx.reply(f'Generated model.jsonl with {lines} lines ({file/1000} kB)')

    @model.command(brief='Create an entirely new model')
    async def create(self, ctx):
        msg = await ctx.reply('Uploading model file')
        with open('ai_data/model.jsonl', 'rb') as f:
            upload_resp = await openai.File.acreate(f, 'fine-tune')
        file_id = upload_resp.id
        await missile.append_msg(msg, 'Sending model train request')
        tune_resp = await openai.FineTune.acreate(training_file=file_id, model='babbage')
        async for event in await openai.FineTune.astream_events(tune_resp.id):
            await missile.append_msg(msg, event.message)
        await missile.append_msg(msg, 'Completed. New Model ID: ' + tune_resp.fine_tuned_model)
        self.model = tune_resp.fined_tuned_model

    @model.command()
    async def set(self, ctx, model_id):
        self.model = model_id
        await ctx.reply('Set model as ' + model_id)

    @model.command()
    async def ft(self, ctx):
        resp = await openai.FineTune.alist()
        print(resp)
        msg = ''
        for ft in resp.data:
            msg += f'{ft.id} {ft.status}'
            if ft.fine_tuned_model:
                msg += ' -> ' + ft.fine_tuned_model
            msg += '\n'
        if not msg:
            msg = 'No FT'
        await ctx.reply(msg)

    @model.command(name='clear')
    async def m_clear(self, ctx):
        resp = await openai.FineTune.alist()
        tasks = []
        for task in resp.data:
            if task.fine_tuned_model and task.fine_tuned_model != self.model:
                tasks.append(openai.Model.adelete(task.fine_tuned_model))
        await asyncio.wait(tasks)
        await ctx.reply(f'Deleted {len(tasks)} models.')

    @ai.group(invoke_without_command=True)
    @missile.is_rainbow()
    async def file(self, ctx):
        resp = await openai.File.alist()
        print(resp.data)
        msg = ''
        for file in resp.data:
            msg += f'{file.id} **{file.filename}** {file.purpose} {file.status} {file.bytes/1000}kB\n'
        if not msg:
            msg = 'No files.'
        await ctx.reply(msg)

    @file.command(name='clear')
    async def f_clear(self, ctx):
        resp = await openai.File.alist()
        tasks = map(lambda f: openai.File.adelete(f.id), resp.data)
        await asyncio.wait(tasks)
        await ctx.reply(f'Deleted {len(resp.data)} files.')

    @commands.command(brief='Chat using the ChatGPT model')
    async def gpt(self, ctx, *, msg):

        def role_prefix(m):
            if m.author == self.bot.user:
                return 'assistant', ''
            return 'user', m.author.name + ': '

        ref = ctx.message.reference
        msgs = [
            {"role": 'user', "content": f'{ctx.author.name}: {msg}'}
        ]
        while ref and ref.cached_message:
            role, prefix = role_prefix(ref.cached_message)
            msgs.append({"role": role, "content": prefix + ref.cached_message.content})
            ref = ref.cached_message.reference
        msgs = ({"role": 'system',
                 "content": "You are DimBot, a cute, smart, light-headed and kind girl. You have a nickname 'Nene'"},) \
               + tuple(reversed(msgs))

        resp = await openai.ChatCompletion.acreate(
            model='gpt-3.5-turbo', messages=msgs
        )
        await ctx.reply(resp['choices'][0]['message']['content'])