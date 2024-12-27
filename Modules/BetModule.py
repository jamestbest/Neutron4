import datetime

import discord
from discord.ext import commands, tasks

import SharedFunctions as sf

class Bet:
    def __init__(self, title: str, desc: str, end_time: datetime.datetime, icon: str, choices: list[str]):
        self.title: str = title
        self.desc: str = desc

        self.icon_url = icon

        self.end_time: datetime.datetime = end_time
        self.choices: list[str] = choices

        self.message_id: discord.Message.id = None
        self.message: discord.Message | None = None

    async def start_bet(self, ctx: discord.ApplicationContext):
        embed = discord.Embed(title=self.title, description=self.desc)
        embed.set_thumbnail(
            url=self.icon_url
        )

        for choice in self.choices:
            embed.add_field(name=choice, value="", inline=False)

        self.message = await ctx.send(embed=embed)
        self.message_id = self.message.id

        await ctx.send(embed=embed)
        await ctx.respond("Created bet")

class Vote:
    def __init__(self, user: discord.User, choice: int):
        self.user: discord.User = user
        self.choice: int = choice

class BetCog(commands.Cog):
    vote_group = discord.SlashCommandGroup("bets", "collection of commands for managing bets")

    def __init__(self, bot: discord.Bot):
        self.bot: discord.Bot = bot

        self.bets: list[Bet] = []

    @commands.slash_command(name="bet", description="Create a bet")
    @discord.option(name="title", type=str, description="The title of the bet")
    @discord.option(name="description", type=str, description="The description of the bet")
    @discord.option(name="end time", type=str, description="Format dd-mm-yy:hh-mm")
    @discord.option(name="icon", type=str, description="Icon url", optional=True)
    async def vote(self, ctx: discord.ApplicationContext, vote_description: str, duration: int = 24 * 60,
                   min2pass: int = 6):
        ...
