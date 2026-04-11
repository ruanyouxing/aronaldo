import discord
import asyncio
from utils import ban, get_time, jail
from discord.ext import commands, tasks

class automod(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

        self.bait_channel = self.bot.config["bait_channel"]
        self.whitelist = self.bot.config["whitelist"]
        self.temp_ban_time = self.bot.config["temp_ban_time"]
        self.jail_role = self.bot.config["tu_ngay"]

        self.check_unban_loop.start()
        self.check_unjail_loop.start()

    def cog_unload(self):
        self.check_unban_loop.cancel()
        self.check_unjail_loop.cancel()
        

    @tasks.loop(seconds=10)
    async def check_unban_loop(self):
        await ban.check_unban(self.bot, get_time(), self.temp_ban_time)

    @check_unban_loop.before_loop
    async def before_check_unban_loop(self):
        await self.bot.wait_until_ready()

    @tasks.loop(seconds=10)
    async def check_unjail_loop(self):
        await jail.check_unjail(self.bot, get_time(), self.jail_role)

    @check_unjail_loop.before_loop
    async def before_check_unjail_loop(self):
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