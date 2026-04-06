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
        # Đổi prefix thành '>' để lệnh batchuoc hoạt động chuẩn
        super().__init__(command_prefix=">", intents=intents)

    async def setup_hook(self):
        # Load tất cả các cogs
        await self.load_extension("cogs.thongbao")
        await self.load_extension("cogs.batchuoc")
        await self.load_extension("cogs.automod")
        
        # Sync slash commands một lần duy nhất khi khởi động
        await self.tree.sync()
        print("Đã đồng bộ Slash Commands.")

    async def on_ready(self):
        print(f'Bot đã đăng nhập với tên {self.user}')

load_dotenv()
bot = Aronaldo()
bot.run(os.getenv('TOKEN'))
'''dev by caophihung'''
