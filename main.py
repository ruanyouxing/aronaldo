'''dev by caophihung'''

import discord
from discord.ext import commands
import os
from dotenv import load_dotenv

class Aronaldo(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=">", intents=intents)

    async def setup_hook(self):
        await self.load_extension("cogs.thongbao")
        await self.load_extension("cogs.batchuoc")
        await self.load_extension("cogs.automod")
        await self.load_extension("cogs.edit")

        await self.tree.sync()
        print("Đã đồng bộ Slash Commands.")

    async def on_ready(self):
        print(f'Bot đã đăng nhập với tên {self.user}')

load_dotenv()
bot = Aronaldo()
bot.run(os.getenv('TOKEN'))
'''dev by caophihung'''
