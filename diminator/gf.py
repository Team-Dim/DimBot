from random import choice

from discord.ext import commands

import missile
from diminator.obj import GF


class GirlfriendCog(commands.Cog):

    def __init__(self, bot):
        self.bot: missile.Bot = bot

    @commands.command(brief='Chinese New Year special event!!!!')
    async def gf(self, ctx: commands.Context):
        gf = self.bot.get_user_store(ctx.author.id).gf
        emoji = choice(tuple(e for e in self.bot.get_cog('Hamilton').guild.emojis
                             if e.name.startswith('sayu') or e.name.startswith('chloe')))
        n = 4 if emoji.name.startswith('sayu') else 5
        emb = missile.Embed('Your girlfriend', f'Energy: {gf.energy}', thumbnail=emoji.url)
        f = ''
        for k, v in gf.food.items():
            f += f'{v}x {gf.food_names[k].capitalize()}, '
        f = f if f else 'None'
        emb.add_field('Food', f)
        f = ''
        for k, v in gf.ingredients.items():
            f += f'{v}x {gf.ingredients_table[k]}, '
        f = f if f else 'None'
        emb.add_field('Ingredients', f)
        emb.set_footer(text='Mood: ' + emoji.name[n:])
        await ctx.reply(embed=emb)

    @commands.command(brief='Cook for your gf!')
    async def cook(self, ctx: commands.Context, *, food: str):
        if food.lower() in GF.food_names:
            i = GF.food_names.index(food.lower())
            if i > 6:
                await ctx.reply("You can't cook this!")
                return
            recipe = GF.recipe[i]
            missing_i = []
            gf = self.bot.get_user_store(ctx.author.id).gf
            for ingri_i in recipe:
                if ingri_i not in gf.ingredients:
                    missing_i.append(gf.ingredients_table[ingri_i])
            if missing_i:
                await ctx.reply(f"You are missing {', '.join(missing_i)}.")
            else:
                for ingri_i in recipe:
                    ingri_c = gf.ingredients[ingri_i]
                    if ingri_c > 1:
                        gf.ingredients[ingri_i] -= 1
                    else:
                        gf.ingredients.pop(ingri_i)
                gf.add_food(i)
                await ctx.reply(f"You cooked {food}!")
        else:
            await ctx.reply("I don't know what food is that. Are you trying to poison her? <:zencry:836049292769624084>")

    @commands.command(brief='Feed your gf')
    async def feed(self, ctx: commands.Context, *, food: str):
        if food.lower() in GF.food_names:
            gf = self.bot.get_user_store(ctx.author.id).gf
            i = GF.food_names.index(food.lower())
            if i in gf.food:
                if gf.food[i] > 1:
                    gf.food[i] -= 1
                else:
                    del gf.food[i]
                gf.energy += GF.food_energy[i]
                await ctx.reply(f"She ate 1x {food}!")
            else:
                await ctx.reply(f"You don't have {food}!")
        else:
            await ctx.reply("I don't know what food is that.")

