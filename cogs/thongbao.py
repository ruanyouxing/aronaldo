import discord
from discord import app_commands
from discord.ext import commands
import json
from utils import create_embed, get_embed_data


class thongbao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("config.json", "r") as f:
            data = json.load(f)
        self.cabin_channel = data["cabin_channel"]
        self.announ_channel = data["announ_channel"]
        self.sech_thu = data["sech_thu"]

    @app_commands.command(name="thongbao", description="Gửi thông báo")
    @app_commands.describe(
        channel="Kênh gửi",
        caption="Caption",
        mention="Có auto thêm mention @Sếch Thủ không",
        title="Tiêu đề",
        description="Mô tả",
        links="Link của các trang, phần cách bằng dấu cách",
        cover="Ảnh bìa",
        archive="Link archive",
        archive_file="File archive",
    )
    async def thong_bao(
        self,
        interaction: discord.Interaction,
        channel: discord.TextChannel = None,
        caption: str = "",
        mention: bool = True,
        title: str = "",
        description: str = "",
        links: str = "",
        cover: discord.Attachment = None,
        archive: str = "",
        archive_file: discord.Attachment = None,
    ):
        if interaction.channel_id != self.cabin_channel:
            return
        await interaction.response.defer()

        if mention and not str(self.sech_thu) in caption:
            caption = f"<@&{self.sech_thu}> {caption}"

        if channel is None:
            channel = interaction.guild.get_channel(self.announ_channel)

        emb = create_embed(title, description, links, archive, archive_file)
        img = await cover.to_file() if cover else None
        
        sent_message = await channel.send(caption, embed=emb, file=img)
        if archive_file:
            await channel.send(file=await archive_file.to_file())

        success_embed = discord.Embed(
            title=f"Đã gửi thành công thông báo tại {sent_message.jump_url}!", 
            color=0x2E8B57
        )
        await interaction.followup.send(embed=success_embed)


async def setup(bot):
    await bot.add_cog(thongbao(bot))
