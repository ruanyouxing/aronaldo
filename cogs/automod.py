import discord
from discord.ext import commands, tasks
import json
import asyncio
from utils import ban, get_time, save_temp_ban, unban
from discord.ext import commands, tasks
class automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        with open("config.json", "r") as f:
            data = json.load(f)
        self.bait_channel = data["bait_channel"]
        self.whitelist = data["whitelist"]
        self.temp_ban_time = data["temp_ban_time"]

        if hasattr(self.bot, 'temp_ban'):
            ban.temp_ban = self.bot.temp_ban
        ban.bot = self.bot

        self.check_loop.start()

    def cog_unload(self):
        self.check_loop.cancel()

    @tasks.loop(seconds=10)
    async def check_loop(self):
        await ban.check_unban(self.bot, get_time(), self.temp_ban_time)

    @check_loop.before_loop
    async def before_check_loop(self):
        await self.bot.wait_until_ready()

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if message.channel.id == self.bait_channel:
            member = message.author
            if not (member.id in self.whitelist or member.top_role >= message.guild.me.top_role):
                await ban.ban_user(message.guild, member, get_time())

async def setup(bot):
    await bot.add_cog(automod(bot))