from typing import Optional

import discord

from DataStore import guild_info_set, levels_set
import re

int_re = "([0-9]*)"

id_at_re = f"<@{int_re}>"
id_hash_re = f"<#{int_re}>"

level_store_re = f"{int_re}, {int_re}, {int_re}"
ginfo_store_re = f"{int_re}, {int_re}, {int_re}, {int_re}, {int_re}"

ginfo_file = "Info/Guild_info.txt"
levels_file = "Info/Levels.txt"


class GuildInfo:
    def __init__(self, guild_id: int, general_id: int, log_id: int, botspam_id: int, courtroom: int):
        self.id = guild_id

        self.general = general_id
        self.log = log_id
        self.botspam = botspam_id
        self.courtroom = courtroom

    def __str__(self):
        return (f"Guild info for guild: {self.id}\n"
                f"|-General: {self.general}\n"
                f"|-Log: {self.log}\n"
                f"|-BotSpam: {self.botspam}\n"
                f"`-Courtroom: {self.courtroom}\n")

    def __repr__(self):
        return self.__str__()

    def file_str(self):
        return f"{self.id}, {self.general}, {self.log}, {self.botspam}, {self.courtroom}\n"

    def ginfo_embed(self, guild: discord.Guild) -> discord.Embed:
        assert guild.id == self.id

        if not verify_g_info(self):
            return discord.Embed(title="Guild information not setup",
                                 description="Please have an admin setup guild info with /setup")

        embed = discord.Embed(
            title=f"Guild Information",
            description=f"Information held on {guild.name} by Neutron",
            color=discord.Color.blurple()
        )

        embed.add_field(name="General  ", value=guild.get_channel(self.general).mention, inline=True)
        embed.add_field(name="Log      ", value=guild.get_channel(self.log).mention, inline=True)
        embed.add_field(name="BotSpam  ", value=guild.get_channel(self.botspam).mention, inline=True)
        embed.add_field(name="Courtroom", value=guild.get_channel(self.courtroom).mention, inline=True)

        return embed


def verify_at_re(string: str) -> int | None:
    return verify_re(string, id_at_re)


def verify_hash_re(string: str) -> int | None:
    return verify_re(string, id_hash_re)


def verify_re(string: str, regex: str) -> int | None:
    groups = re.search(regex, string)

    if groups is None:
        return None

    return int(groups.group(1))


def load_guild_info():
    with open(ginfo_file, "r") as info:
        line = info.readline()
        while line is not None and line != "":
            # expect format as:
            ##          <guild_id> <general_id> <log_id> <bot_spam_id>

            if line.startswith("¬"):
                line = info.readline()
                continue

            groups = re.search(ginfo_store_re, line)

            if groups is None or len(groups.groups()) != 5:
                print(f"Found invalid line: {line}")
                line = info.readline()
                continue

            guild_id = int(groups.group(1))
            ginfo: GuildInfo = GuildInfo(guild_id, int(groups.group(2)), int(groups.group(3)), int(groups.group(4)),
                                         int(groups.group(5)))

            if guild_info_set.get(guild_id) is not None:
                print(
                    f"Warning found multiple entries for guild with id: {guild_id}. Overwriting current info: {guild_info_set.get(guild_id)}")

            guild_info_set[guild_id] = ginfo

            line = info.readline()


async def log_error(ctx: discord.ApplicationContext, error: str):
    ginfo = get_guild_info(ctx.guild_id)

    if not verify_g_info(ginfo):
        return

    log_channel = ctx.guild.get_channel(ginfo.log)

    if log_channel is None:
        return

    await log_channel.send(f"error: {error}")  # todo change to embed


def get_guild_info(guild_id: int) -> GuildInfo | None:
    info = guild_info_set.get(guild_id)
    if info is not None:
        return info
    return None


def set_guild_info(guild_id: int, ginfo: GuildInfo) -> None:
    oldinfo = guild_info_set.get(guild_id)

    guild_info_set[guild_id] = ginfo

    update_g_info_file(ginfo=ginfo, is_new=oldinfo is None)


def remove_guild_info(guild_id: discord.Guild.id) -> bool:
    gi = get_guild_info(guild_id)

    if not gi:
        return False

    guild_info_set.pop(guild_id)

    return True


def update_g_info_file(ginfo: GuildInfo, is_new: bool) -> None:
    if is_new:
        with open(file=ginfo_file, mode="a") as f:
            f.write(ginfo.file_str())
        return
    else:
        buff = ""
        with open(file=ginfo_file, mode="r") as f:
            line = f.readline()
            while not line.startswith(str(ginfo.id)):
                buff += line

                line = f.readline()

            buff += ginfo.file_str()

            for line in f.readlines():
                buff += line

        with open(file=ginfo_file, mode="w") as f:
            f.write(buff)


def verify_g_info(ginfo: GuildInfo) -> bool:
    if ginfo is None:
        return False

    if ginfo.botspam is None: return False
    if ginfo.general is None: return False
    if ginfo.log is None: return False
    if ginfo.courtroom is None: return False

    return True


def get_allowed_str(guild: discord.Guild,
                    ginfo: GuildInfo,
                    allow_spam: bool = True,
                    allow_general: bool = False,
                    allow_log: bool = False,
                    allow_court: bool = False) -> str:
    output = "This command can be used in:\n"

    if allow_spam:
        output += f"{guild.get_channel(ginfo.botspam).mention}\n"

    if allow_general:
        output += f"{guild.get_channel(ginfo.general).mention}\n"

    if allow_log:
        output += f"{guild.get_channel(ginfo.log).mention}\n"

    if allow_court:
        output += f"{guild.get_channel(ginfo.courtroom).mention}\n"

    return output


async def verify_command(guild_id: int, ctx: discord.ApplicationContext,
                         allow_spam: bool = True,
                         allow_general: bool = False,
                         allow_log: bool = False,
                         allow_court: bool = False) -> bool:
    ginfo: GuildInfo | None = get_guild_info(guild_id)

    if not verify_g_info(ginfo):
        await ctx.respond(
            f"Error: Guild info not setup for guild ({guild_id}). Please have an admin setup guild info with `/setup`",
            ephemeral=True)
        return False

    is_admin = ctx.user.guild_permissions.administrator

    if is_admin:
        return True

    if allow_spam and ginfo.botspam == ctx.channel_id:
        return True

    if allow_log and ginfo.log == ctx.channel_id:
        return True

    if allow_general and ginfo.general == ctx.channel_id:
        return True

    if allow_court and ginfo.courtroom == ctx.channel_id:
        return True

    await ctx.respond(get_allowed_str(ctx.guild, ginfo, allow_spam, allow_general, allow_log, allow_court),
                      ephemeral=True)


class Level:
    TIMEOUT_CAP: int = 30

    def __init__(self, user_id: int, level: int, exp: int):
        self.user_id: int = user_id

        self.level: int = level
        self.exp: int = exp

        self.timeout_text: int = Level.TIMEOUT_CAP
        self.timeout_voice: int = Level.TIMEOUT_CAP

    def __str__(self):
        return f"user: {self.user_id} level: {self.level} exp: {self.exp}"

    def __repr__(self):
        return self.__str__()

    def str_formatted(self, bot: discord.Bot):
        user_m = bot.get_user(self.user_id).mention

        return f"user: {user_m} level: {self.level} exp: {self.exp}"


def load_levels(bot: discord.Bot):
    with open(levels_file, "r") as f:
        line = f.readline()

        while line is not None and line != '':
            groups = re.search(level_store_re, line)

            uid = int(groups.group(1))
            level = int(groups.group(2))
            exp = int(groups.group(3))

            if uid is None or level is None or exp is None:
                continue

            new_level = Level(uid, level, exp)

            existing_level: Level = levels_set.get(uid)

            if existing_level is not None:
                print(
                    f"Error: overwriting level value {existing_level.str_formatted(bot)} with new values {new_level.str_formatted(bot)}")

            levels_set[uid] = new_level

            line = f.readline()


async def find_user(user_id: discord.User.id, bot: discord.Bot) -> discord.User | None:
    if (user := bot.get_user(user_id)) is not None:
        return user

    try:
        user = await bot.fetch_user(user_id)
        return user
    except discord.NotFound:
        return None
    except discord.HTTPException:
        return None
