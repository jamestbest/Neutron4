import discord
import asyncio

from discord.ext import commands
from abc import ABC

from TOKENS_DIR import TOKENS

descr = """
Neutron is a discord bot; used to help manage the ATOM server
"""

intents = discord.Intents.all()  # ᕦ(ò_óˇ)ᕤ

class GuildInfo():
    def __init__(self, guild_id: int, general_id: int, log_id: int, botspam_id: int):
        self.id = guild_id
        self.general = general_id
        self.log = log_id
        self.botspam = botspam_id

    def __str__(self):
        return (f"Guild info for guild: {self.id}"
                f"  General: {self.general}"
                f"  Log: {self.log}"
                f"  BotSpam: {self.botspam}")

    def __repr__(self):
        return self.__str__()


class Neutron(commands.Bot, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.guild_info: hash[int:GuildInfo] = {}

        self.load_guild_info()

    def load_guild_info(self):
        with open("Info/Guild_info.txt", "r") as info:
            line = info.readline()
            while line is not None:
                # expect format as:
                ##          <guild_id> <general_id> <log_id> <bot_spam_id>

                line_s: list[str] = line.split(" ")

                assert len(line_s) == 4

                guild_id = int(line_s[0])
                ginfo: GuildInfo = GuildInfo(guild_id, int(line_s[1]), int(line_s[2]), int(line_s[3]))

                if self.guild_info.get(guild_id) is not None:
                    print(f"Warning found multiple entries for guild with id: {guild_id}. Overwriting current info: {self.guild_info.get(guild_id)}")

                self.guild_info[guild_id] = ginfo

                line = info.readline()

    @commands.has_guild_permissions(administrator=True)
    async def setup_guild_info(self, guild_id: int, ctx: discord.ApplicationContext) -> GuildInfo | None:
        await ctx.send("Neutron requires information about the server in order to properly run. Please fill in the ")

        pass

    @setup_guild_info.error
    async def setup_guild_info_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.MissingPermissions):
            await ctx.send("Setup of the guild information requires administrator privilege ")
        else:
            raise error

    async def get_guild_info(self, guild_id: int) -> GuildInfo | None:
        info = self.guild_info.get(guild_id)
        if info is not None:
            return info

        info = await self.setup_guild_info(guild_id)

        if info is None:
            print(f"Error: Creation of guild info failed for guild with id: {guild_id}")
            return None
        return info


DISCORD_API_KEY = TOKENS.DISCORD_API_KEY
DBG_GUILD_IDS = TOKENS.DBG_GUILD_IDS

bot = Neutron(
    command_prefix=commands.when_mentioned_or("*"),
    description=descr,
    intents=intents,
    activity=discord.Game(name="Farm Frenzy 3"),
    debug_guilds=DBG_GUILD_IDS,
)


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("-------------------------------------------------")

    results = await bot.sync_commands(guild_ids=DBG_GUILD_IDS)

    print(results)
    print("Setup complete. All commands synced")

from Modules import BasicCog

bot.add_cog(BasicCog.BasicCog(bot))

bot.run(DISCORD_API_KEY)
print("DONE")