import random
from time import sleep

import discord
from discord import option
from discord.ext import commands
from TOKENS_DIR import TOKENS
from TOKENS_DIR.TOKENS import ATOM_LOG_ID, ATOM_GENERAL_ID


class PurgeCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot: discord.Bot = bot

        self.forgiven: list[int] = []
        self.chat_to_use = ATOM_GENERAL_ID

    @commands.slash_command(name="purge")
    @commands.is_owner()
    async def purge_start(self, ctx: discord.ApplicationContext):
        await self.purge()

    @commands.slash_command(name="purgeremind")
    @commands.is_owner()
    async def purgeremind(self, ctx: discord.ApplicationContext):
        general = self.bot.get_channel(self.chat_to_use)

        await general.send("@everyone The second ATOM Annual purge begins soon, take this time to make peace with Gorp, for he will judge us all")

    @commands.slash_command(name="forgive")
    @option("user", type=discord.SlashCommandOptionType.user, required=True)
    @commands.is_owner()
    async def forgive(self, ctx: discord.ApplicationContext, user: discord.User):
        self.forgiven.append(user.id)
        channel = self.bot.get_channel(self.chat_to_use)
        await channel.send(f"Gorpius has decided to forgive {user.display_name}, consider this act one of tentative kindness. May the sludge cleanse your sins.")

    async def purge(self):
        pfile = open("Info/purgelist.txt", "r+")

        atom = self.bot.get_guild(TOKENS.ATOM_GUILD_ID)
        general = atom.get_channel(self.chat_to_use)

        takelonger = [416976228809965568, 755412315632828516, 316273709239500801, 275343721606676481]

        await general.send(
            "Welcome all, Sludgies and Sludgettes.\nToday we arrive at the forefront of history, today we bare witness to an act that could only be from Gorp himself. \n\nI stand "
            "before you not as a messenger but as a fellow follower, as someone who has been leading their night in prayer for as long as I can remember. I know that some of you"
            " may fear this unknown, but we should not, this is history that will bring us together, history that will be told generations from now. It was Aristotle that once said"
            " \"In Gorp we find not hate, not love, not peace, not war... but a viscous sludge that dost cure any ill\". ")

        sleep(40)
        userids = []

        line = pfile.readline()
        while line != '':
            userids.append(line.strip("\n"))
            line = pfile.readline()

        pfile.close()

        memcpy = atom.members
        memcpy.sort(key=lambda x: len(x.display_name))
        for user in memcpy:
            mess = await general.send(f"Gorpius is judging {user.name}")
            if user.id in takelonger:
                sleep(12)
            else:
                sleep(random.randint(2, 4))

            await mess.delete()

            if str(user.id) in userids:
                if user.id == 416976228809965568:
                    await general.send(
                        content=f"```ansi\n[2;31m[0m[2;31m{user.name}[0m[2;31m[0m has been selected (very funny, please laugh)```")
                else:
                    await general.send(
                        content=f"```ansi\n[2;31m[0m[2;31m{user.name}[0m[2;31m[0m has been selected```")
            else:
                if user.id == 275343721606676481:
                    await general.send(f"{user.display_name} tread lightly, Gorpius does not look kindly on heresy")
                else:
                    await general.send(content=f"```ansi\nGorpius smiles gracefully upon {user.name}```")

            if user.id == 339926969548275722:
                await general.send(
                    "Hold on, let's take into account my music module at least. Oh Gorp, judge this mortal pestilence once more")
                mess = await general.send(f"Gorpius is judging {user.name}")
                sleep(7)

                await mess.delete()
                await general.send(content=f"```ansi\nGorpius smiles gracefully upon {user.name}```")
                await general.send("...")

        await general.send(
            "Bare witness to the might of [gorp](https://tenor.com/view/kick-sparta-leonidas-fall-gif-8139307)")

        for userid in userids:
            user: discord.User | None = self.bot.get_user(int(userid))
            if user and user.id not in self.forgiven:
                # await general.send(f"this is where {user.name} is kicked")
                await atom.kick(user=user, reason="Gorp hast deemed it so")

        await general.send("Gorpius is satiated")

        with open('Images/thatsall.gif', 'rb') as f:
            picture = discord.File(f)
            await general.send(file=picture)

        print(userids)
