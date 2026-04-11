import discord
from discord import app_commands
from discord.ext import commands
from utils import jail_user, get_time, convert_time

class jail(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.chay_to = self.bot.config["chay_to"]
        self.jail_role = self.bot.config["tu_ngay"]
        self.mod_role = self.bot.config["dep_trai_quyen_luc"]
        self.whitelist = self.bot.config["whitelist"]

    @app_commands.command(name="jail", description="Cho member tù ngay")
    @app_commands.describe(
        member="Member cần bị tù ngay",
        time="Thời gian bị tù ngay",
        reason="Lý do bị tù ngay"
    )
    async def jail(
        self,
        interaction: discord.Interaction,
        member: discord.Member,
        time: str,
        reason: str = ''
    ):
        if not any(role_id in self.mod_role for role_id in [role.id for role in interaction.user.roles]):
            return
        if not (member.id in self.whitelist or member.top_role >= interaction.guild.me.top_role):
            try:
                jail_time = convert_time(time)
                await jail_user(interaction, member, get_time(), jail_time, self.jail_role)
                channel = interaction.guild.get_channel(self.chay_to)
                reason = f"\nVới lý do: ```{reason}```" if reason else ''
                message = f"`@{member.display_name}` vừa bị tù ngay với thời gian là: `{time}`{reason}\nThời gian ra tù: <t:{int(get_time() + jail_time)}:R>"
                await interaction.response.send_message(embed=discord.Embed(title=message, color=0xff0000))
                await channel.send(member.mention, embed=discord.Embed(title=message, color=0xff0000))
            except:
             await interaction.response.send_message(embed=discord.Embed(title=f"Đã có lỗi xảy ra!", color=0xff0000), ephemeral=True)

async def setup(bot):
    await bot.add_cog(jail(bot))