import discord
from discord import app_commands
from discord.ext import commands
from utils.format_deadline import format_deadline
from spreadsheets import upload_to_spreadsheet
import asyncio
import re

class CommissionCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    commission_group = app_commands.Group(name="commission", description="Quản lý commission")

    def parse_user_input(self, interaction: discord.Interaction, user_input: str):
        match = re.search(r"<@!?(\d+)>", user_input)
        if match:
            user_id = match.group(1)
            member = interaction.guild.get_member(int(user_id))
            name = member.display_name if member else f"User_{user_id}"
            return str(user_id), name
        else:
            return user_input, user_input

    @commission_group.command(name="submit", description="Ghi nhận thông tin commission lên Google Sheets")
    @app_commands.describe(
            name="Tên truyện",
            link="Link truyện",
            customer="Tag KH (@Customer) hoặc nhập tên KH",
            deadline="DD/MM/YYYY",
            price="Giá cả. VD: 300000",
            translator="Tag người dịch (@Trans) hoặc tên",
            editor="Tag editor (@Edit) hoặc tên",
            ratio="Tỷ lệ chia chác (VD: 50/50)",
            surcharge = "Phụ phí riêng cho editor (được tính riêng trước khi chia chác)",
            )


    async def submit(self, interaction: discord.Interaction, name: str, link: str, customer: str, deadline: str, price: str, translator: str, editor: str, ratio: str = "50/50", surcharge: str = ""):
        await interaction.response.defer(ephemeral=False)
        
        cust_id, cust_name = self.parse_user_input(interaction, customer)
        trans_id, trans_name = self.parse_user_input(interaction, translator)
        edit_id, edit_name = self.parse_user_input(interaction, editor)
        deadline = format_deadline(deadline)
        result = await asyncio.to_thread(
            upload_to_spreadsheet, 
            name, link, cust_id, cust_name, deadline, price, surcharge, trans_id, trans_name, edit_id, edit_name, ratio
        )
        
        if result is None:
            await interaction.followup.send("Lỗi Code: Hàm upload trả về None.", ephemeral=True)
            return

        if isinstance(result[0], str) and result[0].startswith("Lỗi"):
            error_embed = discord.Embed(title="Lỗi", description=result[0], color=discord.Color.red())
            await interaction.followup.send(embed=error_embed, ephemeral=True)
            return

        success_embed = discord.Embed(
            title="✅ Xác nhận Commission Thành Công",
            color=discord.Color.green()
        )
        success_embed.add_field(name="Project", value=f"[{name}]({link})" if link.startswith("http") else name, inline=False)
        success_embed.add_field(name="Khách hàng", value=f"<@{cust_id}>", inline=False)
        success_embed.add_field(name="Translator", value=f"<@{trans_id}>", inline=False)
        success_embed.add_field(name="Editor", value = f"<@{edit_id}>", inline=False)

        success_embed.add_field(name="Giá", value=f"{int(price):,} VND", inline=True)
        success_embed.add_field(name="Phụ phí Editor", value=f"{int(surcharge):,} VND", inline=True)
        # success_embed.add_field(
        #     name="Thực nhận sau chia tỷ lệ", 
        #     value=f"**Trans:** `{int(result[0]):,}`\n**Edit:** `{int(result[1]):,}` (Gồm phụ phí)", 
        #     inline=False
        # )
        
        await interaction.followup.send(embed=success_embed)

async def setup(bot):
    await bot.add_cog(CommissionCog(bot))
