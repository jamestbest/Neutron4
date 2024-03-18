import io
import os
import random
import string

import discord
from discord.ext import commands

import SharedFunctions as sf
import re
import requests

from PIL import Image, GifImagePlugin, ImageSequence  #

import matplotlib.pyplot as plt

# TODO For red day 2
#  - support images
#  - initially have the messages the same but then have a command to switch it to the actual author

def refify(image: Image):
    red_image = Image.new('RGBA', image.size, (0, 125, 0, 100))

    frames = []
    for frame in ImageSequence.Iterator(image):
        n_frame = Image.alpha_composite(frame.convert('RGBA'), red_image)

        frames.append(n_frame.copy())

    output_gif_bytes = io.BytesIO()
    frames[0].save(output_gif_bytes, format='GIF', save_all=True, append_images=frames[1:], loop=0)

    return output_gif_bytes


def redify(message: str):
    message = re.sub(r"\[[0-9;]*m", "", message)
    message = re.sub(r"\'", "", message)

    return f"```ansi\n[2;32m{message}[0m\n```"


def is_message_red(message: str):
    if not message.startswith("```ansi\n[2;32m"):
        return False

    locs = re.findall("", message)

    if not message.endswith("[0m```") and not message.endswith("[0m\n```"):
        return len(locs) == 1

    if len(locs) == 2:
        return True

    m_split = message.split("")

    needs_red: bool = False

    for i in range(2, len(m_split) - 1):
        part = m_split[i]

        if part.startswith("[2;32m"):
            needs_red = False
            continue

        if needs_red:
            return False

        if part.startswith("[0m"):
            if len(part) != len("[0m"):
                return False
            else:
                needs_red = True
        else:
            return False

    return True


class RedDayCog(commands.Cog):
    def __init__(self, bot):
        self.bot: discord.Bot = bot

    @commands.Cog.listener()
    async def on_message(self, message: discord.Message):
        if message.author == self.bot.user:
            return

        if message.channel.name == "log-access-lvl-2":
            return

        if (loc := message.content.find("http")) != -1:
            url = message.content[loc::]
            url = url.split(None)[0]

            mess = message.content[:loc:] + message.content[loc + len(url)::]

            print(os.getcwd())

            await message.delete()

            content = str(requests.get(url).content)
            urls = re.findall(r"https://media1\.tenor\.com.*?\.gif", content)

            if urls:
                url = urls[0]

            arr = io.BytesIO(requests.get(url).content)
            arr.seek(0)

            img: Image = Image.open(arr)

            my_bytes: io.BytesIO = refify(img)
            my_bytes.seek(0)
            file = discord.File(fp=my_bytes, filename=url.split('/')[-1])

            if mess and mess != "":
                output = redify(f"{message.author.display_name} said: {mess}")
            else:
                output = redify(f"{message.author.display_name} sent:")

            await message.channel.send(content=output, files=[file])
            return

        if not is_message_red(message.content):
            await message.delete()
            await message.channel.send(redify(f"{message.author.display_name} said:\n {message.content}"))

    @commands.Cog.listener()
    async def on_message_edit(self, before, after: discord.Message):
        if before.author == self.bot.user:
            return

        if not is_message_red(after.content):
            await after.delete()
            await after.channel.send(redify(f"{after.author.display_name} said:\n {after.content}"))
