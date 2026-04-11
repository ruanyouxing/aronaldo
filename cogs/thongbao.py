import discord
from discord import app_commands
from discord.ext import commands
from utils import create_embed, get_embed_data

class thongbao(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.cabin_channel = self.bot.config["cabin_channel"]
        self.announ_channel = self.bot.config["announ_channel"]
        self.sech_thu = self.bot.config["sech_thu"]

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

        sech_thu = f'<@&{self.sech_thu}>'

        if mention and not sech_thu in caption:
            caption = f"{sech_thu} {caption}"

        if channel is None:
            channel = interaction.guild.get_channel(self.announ_channel)

        emb = create_embed(title, description, links, archive, archive_file)
        img = await cover.to_file() if cover else None
        
        sent_message = await channel.send(caption, embed=emb, file=img)
        if archive_file:
            await channel.send(file=await archive_file.to_file())

        await interaction.followup.send(embed=discord.Embed(title=f"Đã gửi thành công thông báo tại {sent_message.jump_url}!", color=0x2E8B57))


async def setup(bot):
    await bot.add_cog(thongbao(bot))
