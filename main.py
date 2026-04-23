'''dev by caophihung'''

import discord
from discord.ext import commands
import os
import json
from dotenv import load_dotenv
from utils import load_cogs

class Aronaldo(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        super().__init__(command_prefix=">", intents=intents)
        with open("config.json", "r") as f:
            self.config = json.load(f)

    async def setup_hook(self):
        self.remove_command("help")

        await load_cogs(self)
        print("Đã đồng bộ Slash Commands.")

    async def on_ready(self):
        print(f'Bot đã đăng nhập với tên {self.user}')

load_dotenv()
bot = Aronaldo()
bot.run(os.getenv('TOKEN'))
'''dev by caophihung'''
