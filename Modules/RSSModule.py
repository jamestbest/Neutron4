import datetime

import discord
import feedparser as fp
from discord.ext import commands
from discord.ext.tasks import loop

from TOKENS_DIR.TOKENS import GITLAB_FEED_TOKEN


class RSSCog(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot

        self.url = "https://projects.cs.nott.ac.uk/comp1003-2324-teams/team_55/coursework.atom?feed_token=" + GITLAB_FEED_TOKEN

        self.last_update: datetime = datetime.datetime.now(datetime.timezone.utc)

        self.check_rss.start()

    @loop(minutes=1)
    async def check_rss(self):
        feed = fp.parse(self.url)

        print("STARTING RSS CHECK")

        count = 0
        channel = await self.bot.fetch_channel(704092265869607003)

        for i in range(len(feed.entries) - 1, -1, -1):
            cmp_date = datetime.datetime.fromisoformat(feed.entries[i].updated)
            if cmp_date <= self.last_update:
                continue

            count += 1

            if not channel:
                print("error")
                break

            await channel.send(content=feed.entries[i].title)

        if count != 0:
            await channel.send(content=f"<@416977433754075146> Updated! {count} new entries")

        print(f"UPDATED {count} entries")
        self.last_update = datetime.datetime.now(datetime.timezone.utc)
