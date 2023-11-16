import discord
import asyncio

from discord.ext import commands
from abc import ABC

from TOKENS_DIR import TOKENS

descr = """
Neutron is a discord bot; used to help manage the ATOM server
"""

intents = discord.Intents.all()  # ᕦ(ò_óˇ)ᕤ


class Neutron(commands.Bot, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

DISCORD_API_KEY = TOKENS.DISCORD_API_KEY
DBG_GUILD_IDS = TOKENS.DBG_GUILD_IDS

bot = Neutron(
    command_prefix=commands.when_mentioned_or("*"),
    description=descr,
    intents=intents,
    activity=discord.Game(name="Farm Frenzy 3"),
    debug_guilds=DBG_GUILD_IDS,
)

if __name__ == "__main__":
    print("Hello world!")
