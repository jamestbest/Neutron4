import discord
from discord.ext import commands

import SharedFunctions as sf

import re

class BasicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_member_join(self, member: discord.Member):
        guild = member.guild
        ginfo: sf.GuildInfo | None = sf.get_guild_info(guild.id)

        verified = sf.verify_g_info(ginfo=ginfo)

        if not verified:
            return

        channel = guild.get_channel(ginfo.general)

        file = discord.File("Images/obama.jpeg", filename="monke.jpeg")
        embed = discord.Embed()
        embed.add_field(name="Welcome",
                        value=f"Welcome {member.display_name} to ATOM, may your steam sales be fruitful",
                        inline=True)
        embed.set_image(url="attachment://monke.jpeg")

        await channel.send(embed=embed, file=file)

    @commands.has_permissions(administrator=True)
    @commands.slash_command(name="memberjoined", description="use if bot was offline")
    async def memberjoined(self, ctx: discord.ApplicationContext, memberid: str):
        if not await sf.verify_command(guild_id=ctx.guild_id, ctx=ctx):
            return

        memberid = sf.verify_at_re(memberid)

        if memberid is None:
            return

        member: discord.Member = ctx.guild.get_member(memberid)
        await self.on_member_join(member)

        ginfo = sf.get_guild_info(ctx.guild_id)

        await ctx.respond(f"Command complete! Join message should be found in General: {ctx.guild.get_channel(ginfo.general).mention}")

    @memberjoined.error
    async def member_joined_error(self, ctx: discord.ApplicationContext, error: discord.DiscordException):
        if isinstance(error, commands.MissingPermissions):
            await ctx.respond("memberjoined command requires administrator privilege", ephemeral=True)
            await sf.log_error(ctx, f"{ctx.user.mention} tried to run `/memberjoin` with insufficient permissions")

        else:
            raise error
