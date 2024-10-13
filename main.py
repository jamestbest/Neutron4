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

activity = discord.Activity(name="Farm Frenzy 3", buttons=[dict(label="button", url="google.com")])

bot = Neutron(
    command_prefix=commands.when_mentioned_or("*"),
    description=descr,
    intents=intents,
    activity=activity,
    debug_guilds=DBG_GUILD_IDS,
)


@bot.slash_command(name="setup", description="Initial setup for Neutron.")
@option(name="GeneralChannel", type=discord.TextChannel, required=True)
@option(name="LogChannel", type=discord.TextChannel, required=True)
@option(name="BotSpamChannel", type=discord.TextChannel, required=True)
@option(name="CourtroomChannel", type=discord.TextChannel, required=True)
@commands.has_guild_permissions(administrator=True)
async def setup(ctx: discord.ApplicationContext, gc: discord.TextChannel, lc: discord.TextChannel,
                bsc: discord.TextChannel, crc: discord.TextChannel):
    ginfo = sf.GuildInfo(guild_id=ctx.guild_id, general_id=gc.id, log_id=lc.id, botspam_id=bsc.id, courtroom=crc.id)

    sf.set_guild_info(ctx.guild_id, ginfo)

    await ctx.respond("Successfully updated guilds information displayed below.", embed=ginfo.ginfo_embed(ctx.guild))


@setup.error
async def setup_guild_info_error(ctx: discord.ApplicationContext, error: discord.DiscordException):
    if isinstance(error, commands.MissingPermissions):
        await ctx.respond("Setup of the guild information requires administrator privilege", ephemeral=True)
        await sf.log_error(ctx, f"{ctx.user.mention} tried to run `/setup` with insufficient permissions")
    else:
        raise error


@bot.slash_command(name="setupclear", description="Remove all guild information held on this server by Neutron")
@commands.has_guild_permissions(administrator=True)
async def clearsetup(ctx: discord.ApplicationContext):
    if not await sf.verify_command(ctx.guild_id, ctx):
        await ctx.respond("Unable to verify command")
        return

    gi = sf.get_guild_info(ctx.guild_id)

    if not gi:
        await ctx.respond(f"Neutron does not store any information on {ctx.guild.name}")
        return

    sf.remove_guild_info(guild_id=ctx.guild_id)

    await ctx.respond(f"Removed all information stored on {ctx.guild.name}")


async def send_no_dbg(guild_id: discord.Guild.id):
    guild = bot.get_guild(guild_id)
    if guild is None:
        return

    if len(guild.text_channels) < 1:
        return

    await guild.text_channels[0].send(
        f"No information is stored on {guild.name}. Please setup the server with /setup")


async def send_dbg_info():
    for guild_id in DBG_GUILD_IDS:
        guild = bot.get_guild(guild_id)

        if guild is None:
            print(f"No information for guild: {guild_id}. listed as DBG guild")
            continue

        ginfo = sf.get_guild_info(guild_id)

        if not sf.verify_g_info(ginfo):
            await send_no_dbg(guild_id)
            continue

        log_channel = guild.get_channel(ginfo.log)

        if log_channel is None:
            await send_no_dbg(guild_id)
            continue

        await log_channel.send(
            content=f"Neutron has just launched. All commands synced. This guild ({guild.name}) is listed as a debug guild",
            embed=ginfo.ginfo_embed(guild))


@bot.slash_command(name="getinfo", description="View information stored by Neutron on the current guild")
async def getinfo(ctx: discord.ApplicationContext):
    if not await sf.verify_command(ctx.guild_id, ctx):
        return

    guild_id = ctx.guild_id

    ginfo = sf.get_guild_info(guild_id)

    if ginfo is None:
        return

    await ctx.respond(embed=ginfo.ginfo_embed(ctx.guild))


from Modules import BasicModule, MusicModule, BirthdayModule, VoteModule, RedDayModule, StringModule, ArchModule, \
    RSSModule, PurgeModule


@bot.event
async def on_ready():
    print(f"Logged in as {bot.user.name} (ID: {bot.user.id})")
    print("------------------------------------------------")

    results = await bot.sync_commands(guild_ids=DBG_GUILD_IDS)

    await send_dbg_info()

    with open('Images/ATOMLOOGO.gif', 'rb') as image:
        await bot.user.edit(avatar=image.read())

    print(results)
    print("Setup complete. All commands synced")

bot.add_cog(BasicModule.BasicCog(bot))
bot.add_cog(MusicModule.MusicCog(bot))
bot.add_cog(BirthdayModule.BirthdayCog(bot))
bot.add_cog(VoteModule.VoteCog(bot))
# bot.add_cog(RedDayModule.RedDayCog(bot))
# bot.add_cog(StringModule.StringCog(bot))
bot.add_cog(ArchModule.ArchCog(bot))
bot.add_cog(RSSModule.RSSCog(bot))
bot.add_cog(PurgeModule.PurgeCog(bot))

bot.run(DISCORD_API_KEY)
print("DONE")
