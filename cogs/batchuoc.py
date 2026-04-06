import discord
from discord.ext import commands
import io
import json
from utils import split_message

class batchuoc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("./config_and_storage/config.json", "r") as f:
            self.cabin_channel = json.load(f)["cabin_channel"]

    @commands.command(name="batchuoc")
    async def batchuoc(self, ctx, target: discord.TextChannel, *, content: str = ""):
        if ctx.channel.id != self.cabin_channel:
            return

        files = []
        for att in ctx.message.attachments:
            file_bytes = await att.read()
            if att.filename == "message.txt":
                content = file_bytes.decode("utf-8")
            else:
                files.append(discord.File(io.BytesIO(file_bytes), filename=att.filename))

        parts = split_message(content)
        if not parts: return

        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                await target.send(part, files=files)
            else:
                await target.send(part)

async def setup(bot):
    await bot.add_cog(batchuoc(bot))
