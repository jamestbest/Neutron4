import datetime

import discord
from discord.ext import commands, tasks

import SharedFunctions as sf

upvote_emoji = '⬆️'
downvote_emoji = '⬇️'
valid_reactions = [upvote_emoji, downvote_emoji]


class Voter:
    def __init__(self, user_id: discord.User.id, vote_option: bool):
        self.user_id = user_id
        self.choice = vote_option


class Vote:
    vote_cog = None

    def __init__(self, description: str, start_time: datetime.datetime, duration: int, min_to_pass: int,
                 creator: discord.User,
                 bot: discord.Bot):
        self.bot = bot
        self.creator = creator

        self.description = description

        self.start_time = start_time
        self.end_time = start_time + datetime.timedelta(seconds=duration * 60)

        self.duration = duration

        self.voters: list[Voter] = []

        self.min_to_pass = min_to_pass

        self.updating_seconds: bool = False

        self.message_id: discord.Message.id = None
        self.message: discord.Message | None = None

        self.is_open = True

    async def start_vote(self, ctx: discord.ApplicationContext):
        message = await ctx.respond(content=f"Vote: {self.description}\n"
                                            f"Time remaining: {self.duration} minutes")

        for reaction in valid_reactions:
            await message.add_reaction(reaction)

        self.message = message
        self.message_id = message.id

        self.vote_update.start()

    async def close_vote(self):
        self.is_open = False
        self.vote_update.stop()

        vote_for = 0
        vote_against = 0

        for_list = ""
        against_list = ""

        for voter in self.voters:
            user = await sf.find_user(voter.user_id, self.bot)

            if not user:
                mention = f"{voter.user_id}"
            else:
                mention = f"{user.mention}"

            if voter.choice:
                vote_for += 1
                for_list += f"{mention}\n"
            else:
                vote_against += 1
                against_list += f"{mention}\n"

        result = vote_for - vote_against

        if result < self.min_to_pass:
            result = "Failed"
        else:
            result = "Passed"

        embed = discord.Embed(title=f"Vote {result} {vote_for}:{vote_against}")
        embed.description = f"Created by {self.creator.mention}\nDescription: {self.description}"
        embed.add_field(name="For", value=for_list)
        embed.add_field(name="Against", value=against_list)

        now = datetime.datetime.now()
        time = f"{self.start_time.strftime('%d/%m/%Y %H:%M:%S')}"

        day_diff = now.day != self.start_time.day
        month_diff = now.month != self.start_time.month
        year_diff = now.year != self.start_time.year

        time += f"{f'{now.year}/' if year_diff else ''}"
        time += f"{f'{now.month}/' if year_diff or month_diff else ''}"
        time += f"{f'{now.day} ' if year_diff or month_diff or day_diff else ''}"

        time += f"- {now.strftime('%H:%M:%S')}"

        diff = now - self.start_time
        duration = f"{int(diff.total_seconds() // 60)} / {self.duration}"
        embed.set_footer(text=f"{time} ({duration} minute{'s' if self.duration > 1 else ''})")

        await self.message.edit(content="", embed=embed)

        Vote.vote_cog.remove_vote(self)

    @tasks.loop(minutes=1)
    async def vote_update(self):
        if not self.is_open:
            return

        dt = self.end_time - datetime.datetime.now()

        if dt <= datetime.timedelta(days=0, seconds=0, microseconds=0):
            await self.close_vote()

        if self.updating_seconds and dt.seconds <= 5:
            self.vote_update.change_interval(seconds=1, minutes=0)
        elif not self.updating_seconds and dt.seconds <= 60:
            self.vote_update.change_interval(seconds=5, minutes=0)
            self.updating_seconds = True

        mins: int = int(dt.total_seconds() // 60)
        secs: int = int(dt.total_seconds() % 60)

        await self.message.edit(content=f"Vote: {self.description}\n"
                                        f"Time remaining: {f'{mins} mins' if mins != 0 else ''}"
                                        f" {f'{secs} seconds' if (secs != 0 and self.updating_seconds) else ''}"
                                        f" {f'Vote Complete' if (mins == 0 and secs == 0) else ''}")


class VoteCog(commands.Cog):
    vote_group = discord.SlashCommandGroup("votes", "collection of commands for managing votes")

    def __init__(self, bot):
        self.bot = bot
        Vote.vote_cog = self

        self.votes: list[Vote] = []  ## active votes that are running

    def remove_vote(self, vote: Vote):
        self.votes.remove(vote)

    @commands.slash_command(name="vote", description="Create a vote")
    @discord.option(name="description", type=str, description="The description of the vote")
    @discord.option(name="duration", type=int, description="The duration of the vote in minutes. ADMIN ONLY")
    @discord.option(name="min2pass", type=int, description="The minimum overall value for the vote to pass. ADMIN ONLY")
    async def vote(self, ctx: discord.ApplicationContext, vote_description: str, duration: int = 24 * 60,
                   min2pass: int = 6):
        if not await sf.verify_command(ctx.guild_id, ctx, allow_spam=False, allow_general=False, allow_log=True,
                                       allow_court=True):
            return

        if (duration != 24 * 60 or min2pass != 6) and not ctx.user.guild_permissions.administrator:
            await ctx.respond("Unable to create a vote with modified settings as you do are not an admin")
            return

        await ctx.defer()

        v: Vote = Vote(description=vote_description, start_time=datetime.datetime.now(), duration=duration,
                       min_to_pass=min2pass, creator=ctx.user, bot=self.bot)

        await v.start_vote(ctx)
        self.votes.append(v)

    @vote_group.command(name="close", description="Close a vote early")
    @discord.option(name="messageid", description="Enter the message id of the vote")
    async def voteclose(self, ctx: discord.ApplicationContext, vote_message_id):
        if not ctx.user.guild_permissions.administrator:
            await ctx.respond("unable to close a vote without admin")
            return

        try:
            int(vote_message_id)
        except ValueError:
            await ctx.respond("Vote message id must be an int")
            return

        v: Vote | None = None

        for vote in self.votes:
            if vote.message_id == int(vote_message_id):
                v = vote
                break

        if v is None:
            await ctx.respond(f"Cannot find a vote with id {vote_message_id}")
            return

        await ctx.respond(f"Closed vote with description {v.description}")

        await v.close_vote()

    async def get_user_and_vote(self, payload: discord.RawReactionActionEvent) -> tuple[
        discord.User | None, Vote | None]:
        vote: Vote | None = None

        if self.bot.user.id == payload.user_id:
            return None, None

        for v in self.votes:
            if v.message_id == payload.message_id:
                vote = v
                break

        user: discord.User = self.bot.get_user(payload.user_id)

        if user is None:
            await self.bot.fetch_user(payload.user_id)

        return user, vote

    async def send_votes(self, channel: discord.TextChannel):
        message = "---------VOTES----------\n"

        for vote in self.votes:
            message += f"VOTE: {vote.description}\n"
            for voter in vote.voters:
                user = await sf.find_user(voter.user_id, self.bot)

                if user is None:
                    continue

                message += f"VOTER: {user.mention} {'FOR' if voter.choice else 'AGAINST'}\n"
            message += "\n"

        message += "-------VOTES END-------\n\n"

        await channel.send(content=message, allowed_mentions=discord.AllowedMentions.none())

    @commands.Cog.listener()
    async def on_raw_reaction_remove(self, payload: discord.RawReactionActionEvent):
        user, vote = await self.get_user_and_vote(payload)

        if user is None or vote is None:
            return

        v: Voter | None = None
        for voter in vote.voters:
            if voter.user_id == user.id:
                v = voter
                break

        self.bot: discord.Bot
        message: discord.Message = self.bot.get_message(payload.message_id)

        if message is None:
            return

        reactions = message.reactions

        new_value = None
        for reaction in reactions:
            if reaction.emoji in valid_reactions:
                users = await reaction.users().flatten()

                for user in users:
                    if user.id == payload.user_id:
                        new_value = reaction.emoji == upvote_emoji

        if new_value is None:
            vote.voters.remove(v)
        else:
            v.choice = new_value

        channel: discord.TextChannel = self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id)
        await self.send_votes(channel)

    @commands.Cog.listener()
    async def on_raw_reaction_add(self, payload: discord.RawReactionActionEvent):
        user, vote = await self.get_user_and_vote(payload)

        if user is None or vote is None:
            return

        if payload.emoji.name not in valid_reactions:
            await vote.message.remove_reaction(payload.emoji, user)
            return

        voters: list[Voter] = vote.voters

        for voter in voters:
            if voter.user_id == user.id:
                await vote.message.remove_reaction(upvote_emoji if voter.choice else downvote_emoji, user)
                voter.choice = (payload.emoji.name == upvote_emoji)
                return

        voter: Voter = Voter(payload.user_id, payload.emoji.name == upvote_emoji)
        voters.append(voter)

        channel: discord.TextChannel = self.bot.get_guild(payload.guild_id).get_channel(payload.channel_id)
        await self.send_votes(channel)
