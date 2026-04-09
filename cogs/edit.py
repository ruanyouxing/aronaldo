import discord
import json
from discord import app_commands
from discord.ext import commands
from utils import get_embed_data, create_embed

class EditCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        with open("./config.json", "r") as f:
            data = json.load(f)
        self.cabin_channel = data['cabin_channel']
        self.sech_thu = data['sech_thu']
    @app_commands.command(name="edit", description="Chỉnh sửa thông báo")
    @app_commands.describe(
        message_link='Link dẫn đến tin nhắn cần chỉnh sửa',
        caption='Caption',
        mention='Có auto thêm mention @Sếch Thủ không',
        title="Tiêu đề",
        description="Mô tả",
        links='Link của các trang, phần cách bằng dấu cách',
        cover="Ảnh bìa",
        archive="Link archive",
        has_cover="Có ảnh cover không"
    )
    async def edit(
            self,
            interaction: discord.Interaction,
            message_link: str,
            caption: str = None,
            mention: bool = True,
            title: str = None,
            description: str = None,
            links: str = None,
            cover: discord.Attachment = None,
            archive: str = None,
            has_cover: bool = True
    ):
        if interaction.channel_id != self.cabin_channel:
            return
        await interaction.response.defer()

        edit_check = {
            'title': title,
            'description': description,
            'links': links,
            'archive': archive
        }

        parts = message_link.split("/")
        channel_id = int(parts[-2])
        message_id = int(parts[-1])

        channel = self.bot.get_channel(channel_id)
        if channel is None:
            channel = await self.bot.fetch_channel(channel_id)

        message = await channel.fetch_message(message_id)
        data = get_embed_data(message.embeds[0])

        for k in edit_check:
            if edit_check[k] == '.':
                data[k] = ''
            elif edit_check[k]:
                data[k] = edit_check[k]

        sech_thu = f'<@&{self.sech_thu}>'
        if caption == '.':
            caption = ''

        if caption is None:
            content = message.content
        else:
            content = caption

        if mention and not sech_thu in content:
            content = f"{sech_thu} {content}"
        elif content.startswith(sech_thu) and not mention:
            content = content[len(sech_thu):]

        emb = create_embed(*data.values())

        if cover is None and has_cover:
            cover = message.attachments
        elif not has_cover:
            cover = []
        else:
            cover = [await cover.to_file()]    
        await message.edit(content=content, embed=emb, attachments=cover)
        await interaction.followup.send(embed=discord.Embed(title=f"Đã chỉnh sửa thành công tin nhắn tại {message_link}!", color=0x2E8B57))


async def setup(bot):
    await bot.add_cog(EditCog(bot))