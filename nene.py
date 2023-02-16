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
            prompt = f"{my_name} is a cute, smart, light-headed and kind girl. She also has a nickname 'Nene'.\n{lf.join(convo)}\n{my_name}:"
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
        if not re.match(r'^[\w\-\s,.]+$', para):
            await ctx.reply('Only alphabets, numbers and `,.-_` allowed.')
            return
        with open(f'ai_data/{ctx.author.id}.txt', 'w') as f:
            f.write(para)
        await ctx.reply('Thanks for telling me!')

