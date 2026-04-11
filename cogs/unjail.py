import discord
from discord import app_commands
from discord.ext import commands
from utils import unjail_user

class unjail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.jail_role = self.bot.config["tu_ngay"]
        self.mod_role = self.bot.config["dep_trai_quyen_luc"]
        self.whitelist = self.bot.config["whitelist"]

    @app_commands.command(name="unjail", description="Cho member ra khỏi tù ngay")
    @app_commands.describe(
        member="Member cần được ra tù ngay",
    )
    async def unjail(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
    ):
        if not any(role_id in self.mod_role for role_id in [role.id for role in interaction.user.roles]):
            return
        if self.jail_role in [role.id for role in member.roles]:
            try:
                await unjail_user(self.bot, interaction.guild.id, member.id, self.jail_role)
                message = f"`@{member.display_name}` vừa được ra tù ngay!"
                await interaction.response.send_message(member.mention, embed=discord.Embed(title=message, color=0xff0000))
            except:
                await interaction.response.send_message(embed=discord.Embed(title=f"Đã có lỗi xảy ra!", color=0xff0000), ephemeral=True)

async def setup(bot):
    await bot.add_cog(unjail(bot))