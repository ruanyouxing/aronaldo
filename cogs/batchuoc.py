import discord
from discord.ext import commands
import io
from utils import split_message

class batchuoc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cabin_channel = self.bot.config["cabin_channel"]

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

        sent_messages = []
        for i, part in enumerate(parts):
            if i == len(parts) - 1:
                msg = await target.send(part, files=files)
            else:
                msg = await target.send(part)
            sent_messages.append(msg.jump_url)

        if sent_messages:
            await ctx.reply(embed=discord.Embed(title = f"Tin nhắn đã được gửi thành công tại {sent_messages[0]}", color = 0x2E8B57))


async def setup(bot):
    await bot.add_cog(batchuoc(bot))
