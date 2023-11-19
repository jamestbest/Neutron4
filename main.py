from abc import ABC

import discord
from discord import option
from discord.ext import commands

import SharedFunctions as sf
from TOKENS_DIR import TOKENS

descr = """
Neutron is a discord bot; used to help manage the ATOM server
"""

intents = discord.Intents.all()  # ᕦ(ò_óˇ)ᕤ


class Neutron(commands.Bot, ABC):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        sf.load_guild_info()


DISCORD_API_KEY = TOKENS.DISCORD_API_KEY
DBG_GUILD_IDS = TOKENS.DBG_GUILD_IDS

bot = Neutron(
    command_prefix=commands.when_mentioned_or("*"),
    description=descr,
    intents=intents,
    activity=discord.Game(name="Farm Frenzy 3"),
    debug_guilds=DBG_GUILD_IDS,
)



@bot.slash_command(name="setup", description="Initial setup for Neutron.")
@option(name="GeneralChannel", type=discord.TextChannel, optional=False)
@option(name="LogChannel", type=discord.TextChannel, optional=False)
@option(name="BotSpamChannel", type=discord.TextChannel, optional=False)
@commands.has_guild_permissions(administrator=True)
async def setup(ctx: discord.ApplicationContext, gc: discord.TextChannel, lc: discord.TextChannel, bsc: discord.TextChannel):
    ginfo = sf.GuildInfo(guild_id=ctx.guild_id, general_id=gc.id, log_id=lc.id, botspam_id=bsc.id)

    sf.set_guild_info(ctx.guild_id, ginfo)

    await ctx.respond("Successfully updated guilds information displayed below.", embed=ginfo.ginfo_embed(ctx.guild))

@setup.error
async def setup_guild_info_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("Setup of the guild information requires administrator privilege", ephemeral=True)
        await sf.log_error(ctx, f"{ctx.user.mention} tried to run `/setup` with insufficient permissions")
    else:
        raise error


async def send_dbg_info():
    for guild_id in DBG_GUILD_IDS:
        guild = bot.get_guild(guild_id)

        if guild is None:
            continue

        ginfo = sf.get_guild_info(guild_id)

        if not sf.verify_g_info(ginfo):
            continue

        log_channel = guild.get_channel(ginfo.log)

        if log_channel is None:
            continue

        await log_channel.send(content=f"Neutron has just launched. All commands synced. This guild ({guild.name}) is listed as a debug guild", embed=ginfo.ginfo_embed(guild))


@bot.slash_command(name="getinfo", description="View information stored by Neutron on the current guild")
async def getinfo(ctx: discord.ApplicationContext):
    if not await sf.verify_command(ctx.guild_id, ctx):
        return

    guild_id = ctx.guild_id

    ginfo = sf.get_guild_info(guild_id)

    if ginfo is None:
        return

    await ctx.respond(embed=ginfo.ginfo_embed(ctx.guild))


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("-------------------------------------------------")

    results = await bot.sync_commands(guild_ids=DBG_GUILD_IDS)

    await send_dbg_info()

    print(results)
    print("Setup complete. All commands synced")


from Modules import BasicModule, MusicModule

bot.add_cog(BasicModule.BasicCog(bot))
bot.add_cog(MusicModule.MusicCog(bot))

bot.run(DISCORD_API_KEY)
print("DONE")
