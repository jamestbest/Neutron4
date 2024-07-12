import re

import discord
import datetime

from discord.ext import commands, pages as Pages, tasks

from DataStore import birthday_set, guild_info_set

import SharedFunctions as sf
from TOKENS_DIR import TOKENS

bi_f_path = "Info/Birthday_info.txt"
bi_f_preamble = "¬ <UserId:int>          <birthday:data>          <shouldName:bool>        <silent:bool>\n"
bi_regex = "^([0-9]+) ([0-9]+)/([0-9]+)/([0-9]+) (True|False) (True|False)$"


class Birthday_Info:
    def __init__(self, userId: discord.User.id, birthday: datetime.datetime, shouldName: bool = False,
                 silent: bool = False):
        self.id: discord.User.id = userId
        self.date: datetime.datetime = birthday

        self.shouldName: bool = shouldName
        self.silent: bool = silent

    def __str__(self):
        return (f"Birthday for user: {self.id} is {self.date}\n"
                f"Metadata (ShouldName: {self.shouldName}) (Silent: {self.silent})")

    def __repr__(self):
        return self.__str__()

    def to_Embed_start(self, ctx: discord.ApplicationContext, bot: discord.Bot, prefix: str) -> (discord.User, str):
        user = ctx.guild.get_member(self.id)

        if user is None:
            user = bot.get_user(self.id)

        if user is None:
            return None, "None"

        mention = f'{prefix} {(user.name if user is not None else f"id: {self.id}")}\'s birthday information'

        return user, mention

    def to_formatted_Embed(self, ctx: discord.ApplicationContext, bot: discord.Bot, prefix: str) -> discord.Embed:
        user, mention = self.to_Embed_start(ctx, bot, prefix)

        if user is None:
            return discord.Embed(title="Invalid user found, no discord user found")

        embed = discord.Embed(title=mention, description=f"{self.date.strftime('%d/%m/%Y')}")

        embed.set_thumbnail(url=user.avatar.url)

        embed.add_field(name="silent", value=f"{self.silent}", inline=True)
        embed.add_field(name="use name", value=f"{self.shouldName}", inline=True)
        return embed

    def to_diff_formatted_Embed(self, ctx: discord.ApplicationContext, bot: discord.Bot, prev,
                                prefix: str) -> discord.Embed:
        user, mention = self.to_Embed_start(ctx, bot, prefix)

        if user is None:
            return discord.Embed(title="Invalid user found, no discord user found")

        birthday_diff = f"{prev.date.strftime('%d/%m/%Y')} -> {self.date.strftime('%d/%m/%Y')}" if self.date != prev.date else f"{self.date.strftime('%d/%m/%Y')}"
        embed = discord.Embed(title=mention, description=birthday_diff)

        embed.set_thumbnail(url=user.avatar.url)

        silent_diff = f"{prev.silent} -> {self.silent}" if self.silent != prev.silent else f"{self.silent}"
        embed.add_field(name="silent", value=silent_diff, inline=True)
        should_name_diff = f"{prev.shouldName} -> {self.shouldName}" if self.shouldName != prev.shouldName else f"{self.shouldName}"
        embed.add_field(name="use name", value=should_name_diff, inline=True)
        return embed


def load_bi_file():
    birthday_set.clear()

    with open(bi_f_path, "r") as bi_f:
        line = bi_f.readline()

        while line is not None and line != "":
            if line.startswith("¬"):
                line = bi_f.readline()
                continue

            groups = re.search(bi_regex, line)

            if groups is None:
                line = bi_f.readline()
                print(f"BI: Found an invalid line: {line}")
                continue

            uid = int(groups.group(1))

            bi = Birthday_Info(uid,
                               get_datetime_from_split(int(groups.group(2)), int(groups.group(3)),
                                                       int(groups.group(4))),
                               groups.group(5) == "True",
                               groups.group(6) == "True")

            birthday_set[uid] = bi

            line = bi_f.readline()


def update_bi_file():
    with open(bi_f_path, "w") as bi_f:
        bi_f.write(bi_f_preamble)

        for key, bi in birthday_set.items():
            bi: Birthday_Info

            bi_f.write(f"{bi.id} {bi.date.strftime('%d/%m/%Y')} {bi.shouldName} {bi.silent}\n")


async def verify_date(date: datetime.datetime, ctx: discord.ApplicationContext) -> bool:
    now = datetime.datetime.now()
    if date.year < 1950 or date.year > now.year - 16:
        await ctx.respond(f"Invalid year given must be between 1950-{now.year - 16}", ephemeral=True)
        return False

    return True


def get_datetime_from_split(day: int, month: int, year: int) -> datetime.datetime | None:
    return datetime.datetime(year, month, day)


class BirthdayCog(commands.Cog):
    birthday_group = discord.SlashCommandGroup("birthday", "collection of commands for managing birthdays")

    def __init__(self, bot):
        self.bot: discord.Bot = bot

        load_bi_file()

    @birthday_group.command(name="add", description="Add a birthday")
    @discord.option(name="day", type=int, description="The day of the birthday (1-31)", required=True)
    @discord.option(name="month", type=int, description="The month of the birthday (1-12)", required=True)
    @discord.option(name="year", type=int, description="The year of the birthday (1900-present)", required=True)
    @discord.option(name="user", type=discord.User,
                    description="The user for which the birthday is for. Requires admin for users other than self. (self by default)",
                    required=False)
    @discord.option(name="usename", type=bool,
                    description="Should your name be displayed when announcing the birthday? (off by default)",
                    required=False)
    @discord.option(name="silent", type=bool,
                    description="If silent then Neutron will not send a message on your birthday. (Not silent by default)",
                    required=False)
    async def birthday_add(self, ctx: discord.ApplicationContext, day: int, month: int, year: int, user: discord.User,
                           usename: bool = False, silent: bool = False):
        if not await sf.verify_command(ctx.guild_id, ctx):
            return

        userTarget = ctx.user

        if user is not None and user.id != ctx.user.id:
            if not ctx.user.guild_permissions.administrator:
                await ctx.respond("In order to add the birthday of a user other than yourself you must be an admin",
                                  ephemeral=True)
                return

            userTarget = user

        if userTarget is None:
            await ctx.respond("Error: user is None from calling", ephemeral=True)
            return

        userId = userTarget.id

        date = get_datetime_from_split(day, month, year)

        if date is None:
            await ctx.respond("Invalid date given, unable to make datetime object", ephemeral=True)
            return

        if not await verify_date(date, ctx):
            return

        birthday = Birthday_Info(userId=userId, birthday=date, shouldName=usename, silent=silent)

        existing: Birthday_Info = birthday_set.get(userId)

        if existing is not None:
            birthday_set[userId] = birthday
            await ctx.respond(embed=birthday.to_diff_formatted_Embed(ctx, self.bot, existing, "Updated"))
        else:
            birthday_set[userId] = birthday
            await ctx.respond(embed=birthday.to_formatted_Embed(ctx, self.bot,
                                                                "Created"))  # want to be able to @people but without pinging them

        update_bi_file()

    # todo this function would remove birthdays across servers, in fact so does `birthday remove`, so this needs some revamp
    # todo could instead use a overall birthday that all servers would share and then opt in to the server being able to use it
    @birthday_group.command(name="massremove", description="Remove all birthdays for users in the server")
    @commands.has_permissions(administrator=True)
    async def birthday_mass_remove(self, ctx: discord.ApplicationContext):
        if not await sf.verify_command(ctx.guild_id, ctx):
            return

        count = 0
        to_remove = []
        for id, bi in birthday_set.items():
            if ctx.guild.get_member(id) is not None:
                to_remove.append(id)
                count += 1

        for remove_me in to_remove:
            birthday_set.pop(remove_me)

        await ctx.respond(f"Removed {count} birthdays")

    @birthday_group.command(name="remove", description="Remove a birthday")
    @discord.option(name="user", type=discord.User,
                    description="The user for which the birthday is for. Requires admin for users other than self. (self by default)",
                    required=False)
    async def birthday_remove(self, ctx: discord.ApplicationContext, user: discord.User):
        if not await sf.verify_command(ctx.guild_id, ctx):
            return

        targetUser = ctx.user

        if user is not None and user.id != ctx.user.id:
            if not ctx.user.guild_permissions.administrator:
                await ctx.respond("In order to remove the birthday of a user other than yourself you must be an admin",
                                  ephemeral=True)
                return

            targetUser = user

        userId = targetUser.id

        bi: Birthday_Info = birthday_set.get(userId)

        if bi is None:
            await ctx.respond(f"No birthday information is stored for {targetUser.mention}",
                              allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
            return

        birthday_set.pop(userId)

        await ctx.respond(f"Removed birthday information for {targetUser.mention}",
                          allowed_mentions=discord.AllowedMentions.none())

        update_bi_file()

    @birthday_group.command(name="options", description="Change the options for how your birthday is displayed")
    @discord.option(name="user", type=discord.User,
                    description="The user for which the birthday is for. Requires admin for users other than self. (self by default)",
                    required=False)
    @discord.option(name="usename", type=bool,
                    description="Should your name be displayed when announcing the birthday? (off by default)",
                    required=False)
    @discord.option(name="silent", type=bool,
                    description="If silent then Neutron will not send a message on your birthday. (Not silent by default)",
                    required=False)
    async def birthday_options(self, ctx: discord.ApplicationContext, user: discord.User = None, usename: bool = None,
                               silent: bool = None):
        if not await sf.verify_command(ctx.guild_id, ctx):
            return

        targetUser = ctx.user

        if user is not None and user.id != ctx.user.id:
            if not ctx.user.guild_permissions.administrator:
                await ctx.respond(
                    "In order to change the birthday options of a user other than yourself you must be an admin",
                    ephemeral=True)
                return

            targetUser = user

        userId = targetUser.id

        old_bi: Birthday_Info = birthday_set.get(userId)

        if old_bi is None:
            await ctx.respond(f"No birthday is set for {targetUser.mention}. Use birthday add to create a birthday.",
                              allowed_mentions=discord.AllowedMentions.none(), ephemeral=True)
            return

        new_bi = Birthday_Info(userId, old_bi.date)

        if usename is not None:
            new_bi.shouldName = usename

        if silent is not None:
            new_bi.silent = silent

        await ctx.respond(embed=new_bi.to_diff_formatted_Embed(ctx, self.bot, old_bi, "Updated"))

        birthday_set[userId] = new_bi

        update_bi_file()

    def get_birthdays_by_day(self, birthdays: list[tuple[discord.User.id, Birthday_Info]]) -> list[
        list[tuple[discord.User.id, Birthday_Info]]]:
        ##groups the birthdays by the day and month

        output: list[list[tuple[discord.User.id, Birthday_Info]]] = []
        current_day: list[tuple[discord.User.id, Birthday_Info]] = []
        current_date: datetime.datetime | None = None

        for i in range(len(birthdays)):
            c_b: tuple[discord.User.id, Birthday_Info] = birthdays[i]
            c_b_i: Birthday_Info = c_b[1]

            if current_date is None:
                current_date = c_b_i.date

            if current_date.day != c_b_i.date.day or current_date.month != c_b_i.date.month:
                output.append(current_day)
                current_day = []

                current_date = c_b_i.date
            current_day.append(c_b)

        output.append(current_day)
        return output

    def sort_birthdays(self, ctx: discord.ApplicationContext, descending=False, requireInGuild=True) -> list[
        tuple[discord.User.id, Birthday_Info]]:
        items = birthday_set.items()

        birthdays = []

        for item in items:
            if ctx.guild.get_member(item[0]) is not None or not requireInGuild:
                birthdays.append(item)

        now = datetime.datetime.now()
        bs = sorted(birthdays, key=lambda bs_info: now - datetime.datetime(year=now.year, month=bs_info[1].date.month,
                                                                           day=bs_info[1].date.day), reverse=descending)
        return bs

    @birthday_group.command(name="list", description="View the birthdays stored by the server")
    @discord.option(name="Descending", type=bool, description="View the birthdays in descending order", required=False)
    async def birthday_list(self, ctx: discord.ApplicationContext, descending=False):
        if not await sf.verify_command(ctx.guild_id, ctx):
            return

        pages = []

        items_per_page: int = 10

        bs: list[tuple[discord.User.id, Birthday_Info]] = self.sort_birthdays(ctx, descending)
        bss: list[list[tuple[discord.User.id, Birthday_Info]]] = self.get_birthdays_by_day(bs)

        page_count: int = (len(bss) // (items_per_page + 1)) + 1

        birthdays_pos: int = 0
        for i in range(page_count):
            page = discord.Embed(title="Birthdays".center(45, '-'))

            min_date: datetime.datetime = datetime.datetime.max
            max_date: datetime.datetime = datetime.datetime.min

            max_birthdays = min(10, len(bss) - (10 * i))
            for j in range(max_birthdays):
                birthdays: list[tuple[discord.User.id, Birthday_Info]] = bss[birthdays_pos]

                if len(birthdays) == 0:
                    birthdays_pos += 1
                    continue

                init_birthday = birthdays[0][1].date

                if init_birthday < min_date:
                    min_date = init_birthday
                if init_birthday > max_date:
                    max_date = init_birthday

                should_use_same_year = True

                for bi_pos in range(len(birthdays)):
                    bi = birthdays[bi_pos][1]
                    if bi.date != init_birthday:
                        should_use_same_year = False

                value = ""
                for bi_pos in range(len(birthdays)):
                    bi = birthdays[bi_pos][1]

                    user = self.bot.get_user(bi.id)

                    user_mention: str
                    if not user:
                        try:
                            user = await self.bot.fetch_user(bi.id)
                            user_mention = user.mention
                        except discord.NotFound:
                            user_mention = f"{bi.id} (User NF)"
                        except discord.HTTPException:
                            user_mention = f"{bi.id} (HTTP EX)"
                    else:
                        user_mention = user.mention

                    if should_use_same_year:
                        value += f"{user_mention}\n"
                    else:
                        value += f"{user_mention} ({bi.date.year})\n"

                page.add_field(
                    name=f"{bi.date.strftime('%d/%m/%Y') if should_use_same_year else bi.date.strftime('%d/%m')}",
                    value=value, inline=False)

                page.title = f"{min_date.strftime('%d/%m')} - {max_date.strftime('%d/%m')}".center(45, '-')

                birthdays_pos += 1

            pages.append(page)

        paginator = Pages.Paginator(pages=pages)
        await paginator.respond(ctx.interaction, ephemeral=False)

    @birthday_group.command(name="next", description="View the next birthday")
    async def birthday_next(self, ctx: discord.ApplicationContext):
        if not await sf.verify_command(ctx.guild_id, ctx):
            return

        bs = self.sort_birthdays(ctx)
        bss = self.get_birthdays_by_day(bs)

        if (len(bss) == 0):
            await ctx.respond("No birthdays found")
            return

        next_birthdays = bss[0]

        if (len(next_birthdays) == 0):
            await ctx.respond("DEVERR birthday list with size 0")
            return

        bi = next_birthdays[0][1]
        if len(next_birthdays) == 1:
            user: discord.User = await sf.find_user(bi.id, self.bot)
            await ctx.respond(f"{user.mention if user is not None else f'{bi.id} (User NF)'}'s"
                              f" birthday is next on {bi.date.strftime('%d/%m')}"
                              f" they will be {(datetime.datetime.now().year - bi.date.year - (0 if datetime.datetime.now() < datetime.datetime(year=datetime.datetime.now().year, month=bi.date.month, day=bi.date.day) else 1))}"
                              , allowed_mentions=discord.AllowedMentions.none())
            return

        output = f"Multiple people have a birthday on {bi.date.strftime('%d/%m')}\n"
        for bi_pos in range(len(next_birthdays)):
            bi = next_birthdays[bi_pos][1]

            user: discord.User = await sf.find_user(bi.id, self.bot)

            age = (datetime.datetime.now().year - bi.date.year - (
                0 if datetime.datetime.now() < datetime.datetime(year=datetime.datetime.now().year, month=bi.date.month,
                                                                 day=bi.date.day) else 1))
            output += f"{user.mention if user is not None else f'{bi.id} (User NF)'} ({age})\n"

        await ctx.respond(output, allowed_mentions=discord.AllowedMentions.none())

    @birthday_group.command(name="check")
    async def birthday_check(self, ctx: discord.ApplicationContext):
        await self.check_all_birthdays()
        await ctx.respond("Sent request")

    @tasks.loop(time=datetime.time(hour=8))
    async def check_all_birthdays(self):
        for gi in guild_info_set.values():
            await self.check_birthdays(gi)

    async def reveal_birthday(self, gi: sf.GuildInfo, bi: Birthday_Info):
        channel = self.bot.get_channel(gi.general)

        await channel.send("🎂")

        user = channel.guild.get_member(bi.id)
        role = channel.guild.get_role(TOKENS.ATOM_BIRTHDAY_ROLE_ID)
        await user.add_roles(role)

    async def assure_no_birthday(self, gi: sf.GuildInfo, user: discord.Member | discord.User):
        guild = self.bot.get_guild(gi.id)

        u = guild.get_member(user.id)
        role = u.get_role(TOKENS.ATOM_BIRTHDAY_ROLE_ID)
        if role is not None:
            await u.remove_roles(role)


    async def check_birthdays(self, gi: sf.GuildInfo):
        guild = self.bot.get_guild(gi.id)

        for user in guild.members:
            if birthday_set.get(user.id) is None:
                continue

            bi: Birthday_Info = birthday_set.get(user.id)

            if bi.date.month == datetime.datetime.now().month and bi.date.day == datetime.datetime.now().day:
                await self.reveal_birthday(gi, bi)
            else:
                await self.assure_no_birthday(gi, user)

