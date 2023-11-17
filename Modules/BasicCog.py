import discord
from discord.ext import commands

from TOKENS_DIR import TOKENS

class BasicCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @bot.slash_command(name="memberjoined", description="use if bot was offline")
    async def memberjoined(ctx: discord.ApplicationContext, memberid: str):
        memberid = int(memberid)
        member: discord.Member = ctx.guild.get_member(memberid)
        await on_member_join(member)

    @commands.Cog.listener()
    async def on_member_join(member: discord.Member):
        guild = member.guild
        channel = guild.get_channel(TOKENS.ATOM_GENERAL_CHANNEL_ID)

        file = discord.File("Images/obama.jpeg", filename="monke.jpeg")
        embed = discord.Embed()
        embed.add_field(name="Welcome",
                        value=f"Welcome {member.display_name} to ATOM, may your steam sales be fruitful",
                        inline=True)
        embed.set_image(url="attachment://monke.jpeg")

        await channel.send(embed=embed, file=file)