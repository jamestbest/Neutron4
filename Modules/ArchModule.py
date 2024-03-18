from asyncio import sleep

import discord
from discord.ext import commands

import SharedFunctions as sf

import rsa


class Status:
    def __init__(self, public_key_data, name, status=False):
        self.public_key = public_key_data
        self.angel_status = status
        self.armageddon_status = status
        self.name = name


class ArchAngelEmbed(discord.Embed):
    def __init__(self, creds, cog):
        super().__init__()
        self.active_status = False
        self.creds = creds
        self.cog = cog

    def large_status_symbol(self, status: bool) -> str:
        return "🔴" if not status else "🟢"

    def status_symbol(self, status: bool) -> str:
        return "✖" if not status else "✓"

    def gen_description(self) -> str:
        output: str = f"Credentials:\n"

        largest_name = ""
        for cred in self.creds.values():
            if len(cred.name) > len(largest_name):
                largest_name = cred.name

        i: int = 0

        for key, status in self.creds.items():
            i += 1
            output += f"᲼{status.name}{f'᲼' * (len(largest_name) - len(status.name) + 2)}{' ' if i >= 3 else ''}{self.status_symbol(status.angel_status)}\n"

        return output

    def setup(self):
        self.set_author(name="ASS: Archangel")
        print("UPDATING")
        self.title = f"Archangel Status:   {self.large_status_symbol(self.cog.archangel_status)}"
        self.description = self.gen_description()


class ArmageddonEmbed(discord.Embed):
    def __init__(self, creds, cog):
        super().__init__()
        self.active_status = False
        self.creds = creds
        self.cog = cog

    def large_status_symbol(self, status: bool) -> str:
        return "🔴" if not status else "🟢"

    def status_symbol(self, status: bool) -> str:
        return "✖" if not status else "✓"

    def gen_description(self) -> str:
        output: str = f"Credentials:\n"

        largest_name = ""
        for cred in self.creds.values():
            if len(cred.name) > len(largest_name):
                largest_name = cred.name

        i: int = 0

        for key, status in self.creds.items():
            i += 1
            output += f"᲼{status.name}{f'᲼' * (len(largest_name) - len(status.name) + 2)}{' ' if i >= 3 else ''}{self.status_symbol(status.armageddon_status)}\n"

        return output

    def setup(self):
        self.set_author(name="ASS: Armageddon")
        self.title = f"Armageddon Status:   {self.large_status_symbol(self.cog.armageddon_status)}"
        self.description = self.gen_description()


class ArchAngelView(discord.ui.View):
    def __init__(self, creds, bot, cog):
        super().__init__(timeout=None)

        self.creds = creds
        self.bot: discord.Bot = bot
        self.cog = cog

        self.embed = ArchAngelEmbed(creds, cog)
        self.embed.setup()

        self.message: discord.Message | None = None

    def add_message_link(self, message: discord.Message):
        self.message = message

    @discord.ui.button(label="Credentials", style=discord.ButtonStyle.primary)
    async def creds_callback(self, button, interaction: discord.Interaction):
        ids = [id for id in self.creds.keys()]

        if interaction.user.id not in ids:
            await interaction.response.send_message("You are not authorised to upload credentials", ephemeral=True)
            return

        await interaction.response.send_modal(modal=AssModal(title="ARCHANGEL KEY CREDENTIALS", view=self))

    @discord.ui.button(label="Revoke", style=discord.ButtonStyle.primary)
    async def revoke_callback(self, button, interaction: discord.Interaction):
        ids = [id for id in self.creds.keys()]

        if interaction.user.id not in ids:
            await interaction.response.send_message("You are not authorised to revoke credentials", ephemeral=True)
            return

        cred: Status = self.creds[interaction.user.id]

        cred.angel_status = False

        await self.update()
        await interaction.response.send_message(f"Revoked authorization", ephemeral=True)

    @discord.ui.button(label="Activate", style=discord.ButtonStyle.danger, disabled=True, custom_id="ActivateButton")
    async def activate_callback(self, button, interaction: discord.Interaction):
        ids = [id for id in self.creds.keys()]

        if interaction.user.id not in ids:
            await interaction.response.send_message("You are not authorised to update archangel status", ephemeral=True)
            return

        private_quotes = self.bot.get_channel(1219375427626340523)

        newstat = not self.cog.archangel_status

        print(f"CHANGING TO {'visible' if newstat else 'invis'}")

        perms = private_quotes.overwrites_for(interaction.guild.default_role)
        perms.update(send_messages=newstat, view_channel=newstat, read_messages=newstat, read_message_history=newstat)
        await private_quotes.set_permissions(interaction.guild.default_role, overwrite=perms)

        quotes = self.bot.get_channel(1069355725840724028)

        self.cog.archangel_status = newstat

        newstat = not newstat
        perms = quotes.overwrites_for(interaction.guild.default_role)
        perms.update(send_messages=newstat, view_channel=newstat, read_messages=newstat, read_message_history=newstat)

        await self.update()
        await interaction.response.send_message(f"ARCHANGEL {'ACTIVE' if self.cog.archangel_status else 'DISABLED'}",
                                                ephemeral=True)

    def update_main_status(self):
        newStatus = False

        for cred in self.creds.values():
            if cred.angel_status:
                newStatus = True

        self.embed.active_status = newStatus

    def update_activate_button(self):
        for child in self.children:
            if type(child) != discord.ui.Button:
                continue

            child: discord.ui.Button

            if child.custom_id == "ActivateButton":
                child.disabled = not self.embed.active_status

    async def update(self):
        self.update_main_status()
        self.update_activate_button()
        self.embed.setup()
        await self.message.edit(embed=self.embed, view=self)


class ArmageddonView(discord.ui.View):
    def __init__(self, creds, bot, cog):
        super().__init__(timeout=None)

        self.creds = creds
        self.bot: discord.Bot = bot
        self.cog = cog

        self.embed = ArmageddonEmbed(creds, cog)
        self.embed.setup()

        self.message: discord.Message | None = None

    def add_message_link(self, message: discord.Message):
        self.message = message

    @discord.ui.button(label="Credentials", style=discord.ButtonStyle.primary)
    async def creds_callback(self, button, interaction: discord.Interaction):
        ids = [id for id in self.creds.keys()]

        if interaction.user.id not in ids:
            await interaction.response.send_message("You are not authorised to upload credentials", ephemeral=True)
            return

        await interaction.response.send_modal(modal=ArmageddonModal(title="ARCHANGEL KEY CREDENTIALS", view=self))

    @discord.ui.button(label="Revoke", style=discord.ButtonStyle.primary)
    async def revoke_callback(self, button, interaction: discord.Interaction):
        ids = [id for id in self.creds.keys()]

        if interaction.user.id not in ids:
            await interaction.response.send_message("You are not authorised to revoke credentials", ephemeral=True)
            return

        cred: Status = self.creds[interaction.user.id]

        cred.armageddon_status = False

        await self.update()
        await interaction.response.send_message(f"Revoked authorization", ephemeral=True)

    @discord.ui.button(label="Activate", style=discord.ButtonStyle.danger, disabled=True, custom_id="ActivateButton")
    async def activate_callback(self, button, interaction: discord.Interaction):
        ids = [id for id in self.creds.keys()]

        if interaction.user.id not in ids:
            await interaction.response.send_message("You are not authorised to update armageddon status",
                                                    ephemeral=True)
            return

        private_quotes = self.bot.get_channel(1219375427626340523)

        newstat = not self.cog.armageddon_status

        print(f"CHANGING TO {'visible' if newstat else 'invis'}")

        await private_quotes.delete()

        self.cog.armageddon_status = newstat

        await self.update()
        await interaction.response.send_message(f"ARMAGEDDON {'ACTIVE' if self.cog.archangel_status else 'DISABLED'}",
                                                ephemeral=True)

    def update_main_status(self):
        newStatus = False
        count = 0

        for cred in self.creds.values():
            if cred.armageddon_status:
                count += 1

        newStatus = count >= 3

        self.embed.active_status = newStatus

    def update_activate_button(self):
        for child in self.children:
            if type(child) != discord.ui.Button:
                continue

            child: discord.ui.Button

            if child.custom_id == "ActivateButton":
                child.disabled = not self.embed.active_status

    async def update(self):
        self.update_main_status()
        self.update_activate_button()
        self.embed.setup()
        await self.message.edit(embed=self.embed, view=self)


class AssModal(discord.ui.Modal):
    def __init__(self, view: ArchAngelView, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.view: ArchAngelView = view

        self.add_item(discord.ui.InputText(label="ASSKEY"))

    async def callback(self, interaction: discord.Interaction) -> (str, discord.Interaction):
        data = self.children[0].value

        cred: Status = self.view.creds[interaction.user.id]

        with open(f"Ass_public_keys/Ass_archkey_{cred.public_key}_pub.pem", "rb") as f:
            pub_key_data = f.read()
            pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(pub_key_data)

            dummy_data: bytes = str.encode("Dummy")

            try:
                private_key: rsa.PrivateKey = rsa.PrivateKey.load_pkcs1(
                    str.encode(data.replace('- ', '-\n').replace(' -', '\n-')), format="PEM")
            except (ValueError, Exception) as error:
                await interaction.response.send_message("General failure when authenticating key", ephemeral=True)
                return

            encrypted = rsa.encrypt(dummy_data, pub_key)
            try:
                decrypted = rsa.decrypt(encrypted, private_key)
            except rsa.DecryptionError:
                await interaction.response.send_message("Failed to authenticate key", ephemeral=True)
                return
            except Exception | ValueError:
                await interaction.response.send_message("General failure when authenticating key", ephemeral=True)
                return

            if decrypted == dummy_data:
                print("AWESOME")
            else:
                print("NOT AWESOME")

        cred.angel_status = True
        await self.view.update()

        await interaction.response.send_message(f"Authorized", ephemeral=True)


class ArmageddonModal(discord.ui.Modal):
    def __init__(self, view: ArmageddonView, *args, **kwargs) -> None:
        super().__init__(*args, **kwargs)

        self.view: ArmageddonView = view

        self.add_item(discord.ui.InputText(label="ASSKEY"))

    async def callback(self, interaction: discord.Interaction) -> (str, discord.Interaction):
        data = self.children[0].value

        cred: Status = self.view.creds[interaction.user.id]

        with open(f"Ass_public_keys/Ass_archkey_{cred.public_key}_pub.pem", "rb") as f:
            pub_key_data = f.read()
            pub_key = rsa.PublicKey.load_pkcs1_openssl_pem(pub_key_data)

            dummy_data: bytes = str.encode("Dummy")

            try:
                private_key: rsa.PrivateKey = rsa.PrivateKey.load_pkcs1(
                    str.encode(data.replace('- ', '-\n').replace(' -', '\n-')), format="PEM")
            except (ValueError, Exception) as error:
                await interaction.response.send_message("General failure when authenticating key", ephemeral=True)
                return

            encrypted = rsa.encrypt(dummy_data, pub_key)
            try:
                decrypted = rsa.decrypt(encrypted, private_key)
            except rsa.DecryptionError:
                await interaction.response.send_message("Failed to authenticate key", ephemeral=True)
                return
            except Exception | ValueError:
                await interaction.response.send_message("General failure when authenticating key", ephemeral=True)
                return

            if decrypted == dummy_data:
                print("AWESOME")
            else:
                print("NOT AWESOME")

        cred.armageddon_status = True
        await self.view.update()

        await interaction.response.send_message(f"Authorized", ephemeral=True)


class ArchCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot = bot

        self.creds = {
            416977433754075146: Status(1, "James"),
            448871628336791562: Status(2, "Red"),
            416976228809965568: Status(3, "Bruno"),
            275343721606676481: Status(4, "Grandad")
        }

        self.archangel_status = False
        self.armageddon_status = False

    @commands.Cog.listener()
    async def on_ready(self):
        self.get_current_arch_status()

    def get_current_arch_status(self):
        channel = self.bot.get_channel(1219363254208561285)
        perms = channel.permissions_for(channel.guild.default_role)

        status = perms.view_channel

        self.archangel_status = status
        print(f"STARTING STATUS: {self.archangel_status}")

    @commands.slash_command(name="archangel", description="Nothing to see here")
    async def archangel(self, ctx: discord.ApplicationContext):
        view = ArchAngelView(self.creds, self.bot, self)

        message = await ctx.send(view=view, embed=view.embed)
        view.add_message_link(message)

    @commands.slash_command(name="armageddon", description="Less to see here")
    async def armageddon(self, ctx: discord.ApplicationContext):
        view = ArmageddonView(self.creds, self.bot, self)

        message = await ctx.send(view=view, embed=view.embed)
        view.add_message_link(message)
