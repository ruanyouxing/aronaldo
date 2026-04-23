import discord
from discord import app_commands
from discord.ext import commands
from utils import reload_cogs

class refresh(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="refresh", description="Làm mới lệnh")
    async def refresh(self, interaction: discord.Interaction):
        await reload_cogs(self.bot)
        await interaction.followup.send(embed=discord.Embed(title=f"Đã làm mới lệnh thành công!", color=0x2E8B57))

async def setup(bot):
    await bot.add_cog(refresh(bot))
