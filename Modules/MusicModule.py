import asyncio
import typing

import discord
from discord.ext import commands

import SharedFunctions as sf

import yt_dlp

yt_dlp_options = {
    "format": "bestaudio/best",
    "outtmpl": "MusicDownloaded/%(extractor)s-%(id)s-%(title)s.%(ext)s",
    "restrictfilenames": True,
    "nocheckcertificate": True,
    "ignoreerrors": True,
    "logtostderr": True,
    "quiet": True,
    "no_warnings": True,
    # "extract_flat": "in_playlist",   ##these are removed because they broke non-playlist songs, find which
    'geo_bypass': True,
    # "lazy_playlist": True,
    # "playlistend": 50,
    "default_search": "auto",
    "source_address": (
        "0.0.0.0"
    ),
    "verbose": True,
    "username": "ATOM.Neutronbot@gmail.com",
}

ffmpeg_options = {'before_options': '-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5', 'options': '-vn'}


class Song:
    def __init__(self, data: dict, requester: discord.User):
        self.data = data

        self.name = data["title"]
        self.url = data["url"]
        self.requester = requester


class Source(discord.PCMVolumeTransformer):
    def __init__(self, source: discord.AudioSource, *, data: dict, volume: float = 0.5):
        super().__init__(source, volume)

        self.data = data

    @classmethod
    async def get_source(cls, song: Song):
        return cls(discord.FFmpegPCMAudio(song.url, **ffmpeg_options), data=song.data)


class SongWSource(Song):
    def __init__(self, data: dict, requester: discord.User, source: Source):
        super().__init__(data, requester)

        self.source: Source = source

    @classmethod
    def fromSong(cls, song: Song, source):
        return cls(song.data, song.requester, source)

    @classmethod
    def fromRaw(cls, data: dict, requester: discord.User, source: Source):
        return cls(data, requester, source)


class MusicQueue:
    def __init__(self):
        self.queue: list[Song] = []

    def is_empty(self):
        return len(self.queue) == 0

    def pop(self) -> Song | None:
        if self.is_empty():
            return None

        return self.queue[0]

    def add(self, song: Song):
        self.queue.append(song)

    def get_last_pos(self) -> int:
        return len(self.queue)


class MusicException(Exception):
    pass


class QueueEmptyException(MusicException):
    pass


class YTDLPException(MusicException):
    pass


class MusicCog(commands.Cog):
    def __init__(self, bot: discord.Bot):
        self.bot: discord.Bot = bot

        self.vc: discord.VoiceClient | None = None

        self.music_queue: MusicQueue = MusicQueue()

        self.ytdlOptions = yt_dlp_options
        self.ytdlp: yt_dlp.YoutubeDL = yt_dlp.YoutubeDL(self.ytdlOptions)

    async def goto_channel(self, channel: discord.VoiceChannel, ctx: discord.ApplicationContext):
        if self.vc is None:
            vc: discord.VoiceChannel | None = discord.utils.get(ctx.bot.voice_clients, guild=ctx.guild)
            if vc is not None and vc.is_connected():
                self.vc = vc
                await self.vc.move_to(channel)
            else:
                self.vc = await channel.connect()
        else:
            await self.vc.move_to(channel)

        await channel.guild.change_voice_state(channel=channel, self_deaf=True)

    def get_url_data(self, url: str):
        data = self.ytdlp.extract_info(url, download=False)

        return data

    async def process_song(self, song: Song) -> SongWSource:
        source: Source = await Source.get_source(song)

        return SongWSource.fromSong(song, source)

    async def play_next(self) -> bool:
        next_song: Song = self.music_queue.pop()

        if next_song is None:
            return False

        try:
            await self.play_song(next_song)
        except MusicException as me:
            ##todo have debug log here
            return False

        return True

    async def play_song(self, song: Song) -> MusicException | None:
        if song is None:
            raise QueueEmptyException("Song queue is empty. Loc<MusicModule/MusicCog/play()>")

        if not isinstance(song, SongWSource):
            song: SongWSource = await self.process_song(song)

        if song is None:
            raise YTDLPException("Error getting ytdlp to play song. Loc<MusicModule/MusicCog/play()>")

        self.vc.play(song.source, after=self.after_play())

        return None

    def after_play(self):
        coro = self.play_next()
        asyncio.run_coroutine_threadsafe(coro, self.bot.loop)

    async def add_song(self, song: Song) -> bool:
        should_play = self.music_queue.is_empty() and self.verify_state()

        self.music_queue.add(song)

        if should_play:
            return await self.play_next()
        else:
            return True

    def is_yt_url(self, inp: str) -> bool:
        return True

    def search(self, inp: str) -> str:
        return "https://www.youtube.com/watch?v=dQw4w9WgXcQ&pp=ygUJcmljayByb2xs"

    def verify_state(self) -> bool:
        if self.vc is None: return False


        return True

    async def play_single_song(self, song: Song, ctx: discord.ApplicationContext) -> bool:
        song: SongWSource = await self.process_song(song)

        if song is None:
            return False

        if await self.add_song(song):
            await ctx.respond(
                f"Added {song.name} to the queue at position {self.music_queue.get_last_pos()}")  # todo update to embed
            return True
        else:
            return False

    async def play_playlist(self, data, requester: discord.User, ctx: discord.ApplicationContext) -> bool:
        for entry in data['entries']:
            # data = self.get_url_data(entry['url'])

            song: Song = Song(entry, requester)
            await self.add_song(song)

        await ctx.respond(f"added playlist {data['title']}")

        return True

    @commands.slash_command(name="play",
                            description="Play a song. Either by url or a string that Neutron will search youtube with")
    @discord.option(name="input", description="Url or search term", required=True)
    async def play(self, ctx: discord.ApplicationContext, inp: str):
        if not await sf.verify_command(ctx.guild_id, ctx):
            return

        if not self.is_yt_url(inp):
            url = self.search(inp)
        else:
            url = inp

        if url is None:
            await ctx.respond(f"Unable to search for `{inp}` no results found")
            return

        data = self.get_url_data(url)

        if data is None:
            await ctx.respond(f"Unable to search for `{inp}` no results found")
            return

        if ctx.user.voice is None or not isinstance(ctx.user.voice.channel, discord.VoiceChannel):
            if not self.verify_state():
                await ctx.respond(
                    "Failed to join your channel, and current vc is None. Please consider joining a vc or using /join")
                return
        else:
            await self.goto_channel(ctx.user.voice.channel, ctx)

        is_playlist = data.get('_type') is not None and data['_type'] == 'playlist'

        if is_playlist:
            res = await self.play_playlist(data, ctx.user, ctx)
        else:
            song_to_add: Song = Song(data, ctx.user)
            res = await self.play_single_song(song_to_add, ctx)

        if not res:
            await ctx.respond(f"Failed to add song/playlist to queue")

    @commands.slash_command(name="join", description="Join a voice channel")
    @discord.option(name="channel", description="# of the channel to join", required=False)
    async def join(self, ctx: discord.ApplicationContext, channel: discord.VoiceChannel):
        if not await sf.verify_command(ctx.guild_id, ctx):
            return

        if channel is None:
            channel = ctx.user.voice.channel

            if channel is None or not isinstance(channel, discord.VoiceChannel):
                await ctx.respond(
                    "Can only join users in a voice channel. Alternatively enter the voice channel to join in the options")
                return

        await self.goto_channel(channel, ctx)
        await ctx.respond(f"Successfully joined {channel.mention}")

    @commands.slash_command(name="leave", description="Leave the current vc")
    async def leave(self, ctx: discord.ApplicationContext):
        if not await sf.verify_command(ctx.guild_id, ctx):
            return

        c_channel = self.vc.channel
        uv = ctx.user.voice

        if uv is None:
            u_channel = None
        else:
            u_channel = ctx.user.voice.channel

        is_admin = ctx.user.guild_permissions.administrator

        if u_channel is None or c_channel.id != u_channel.id:
            if not is_admin:
                await ctx.respond("Unable to skip song while you are not a) In the voice channel b) An admin")
                return

        await self.vc.disconnect()
        await ctx.respond("Neutron has disconnected upon request")
