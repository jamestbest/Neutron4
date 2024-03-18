import io

import discord
from discord.ext import commands

import SharedFunctions as sf

connections = {}


class StringCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.code = 0

    @commands.slash_command(name="stoprec")
    async def stop_recording(self, ctx):
        if ctx.guild.id in connections:  # Check if the guild is in the cache.
            vc = connections[ctx.guild.id]
            vc.stop_recording()  # Stop recording, and call the callback (once_done).
            del connections[ctx.guild.id]  # Remove the guild from the cache.
            await ctx.delete()  # And delete.
        else:
            await ctx.respond("I am currently not recording here.")  # Respond with this if we aren't recording.

    async def once_done(self, sink: discord.sinks, channel: discord.TextChannel,
                        *args):  # Our voice client already passes these in.
        recorded_users = [  # A list of recorded users
            f"<@{user_id}>"
            for user_id, audio in sink.audio_data.items()
        ]
        await sink.vc.disconnect()  # Disconnect from the voice channel.

        files = []
        for user_id, audio in sink.audio_data.items():
            files.append(discord.File(audio.file, f"{self.code}.wav"))

            with open(f"TEMP_REC/{self.code}{self.bot.get_user(user_id).display_name}.wav", "wb") as f:
                audio.file: io.BytesIO

                f.write(audio.file.getbuffer())
            self.code += 1

        await channel.send(files=files)

    @commands.slash_command(name="rec")
    async def record(self, ctx):  # If you're using commands.Bot, this will also work.
        voice = ctx.author.voice

        if not voice:
            await ctx.respond("You aren't in a voice channel!")

        vc: discord.VoiceClient = await voice.channel.connect()  # Connect to the voice channel the author is in.
        connections.update({ctx.guild.id: vc})  # Updating the cache with the guild and channel.

        vc.start_recording(
            discord.sinks.WaveSink(),  # The sink type to use.
            self.once_done,  # What to do once done.
            ctx.channel  # The channel to disconnect from.
        )
        await ctx.respond("Started recording!")
