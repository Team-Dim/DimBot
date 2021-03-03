import discord

from missile import Missile


class RGBEmbed(discord.Embed):
    """A shortcut for initialising an Embed with a random color."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs, color=Missile.random_rgb())
