import discord
from discord.ext import commands
import json
class help(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("config.json", "r") as f:
            self.cabin_channel = json.load(f)["cabin_channel"]

    @commands.command(name="help")
    async def help(self, ctx):
            if ctx.channel.id != self.cabin_channel:
                return
            help_message = discord.Embed(title = "Help")
            help_message.add_field(name=">batchuoc", value = "Cú pháp: `>batchuoc` `<tên channel ở đây>` `<nội dung còn lại>`\nSau đó bạn có thể ghi thêm text hoặc bất cứ attachment nào, bot sẽ tự xử lý và bắt chước phần còn lại.")
            await ctx.reply(embed=help_message)

async def setup(bot):
    await bot.add_cog(help(bot))