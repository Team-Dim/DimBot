import discord

from missile import Missile


class RGBEmbed(discord.Embed):

    def __init__(self, **kwargs):
        super().__init__(**kwargs, color=Missile.random_rgb())
