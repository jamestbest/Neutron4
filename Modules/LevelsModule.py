import discord
from discord.ext import commands

import SharedFunctions as sf

class LevelCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot: discord.Bot = bot
