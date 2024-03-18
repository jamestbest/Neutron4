import discord
from discord.ext import commands


class LevelCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot: discord.Bot = bot
