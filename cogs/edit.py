import discord
from discord import app_commands
from discord.ext import commands
from utils import get_embed_data, create_embed


class EditCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @app_commands.command(name="edit", description="Chỉnh sửa thông báo")
    @app_commands.describe(
        message_link='Link dẫn đến tin nhắn cần chỉnh sửa',
        caption='Caption',
        mention='Có auto thêm mention @Sếch Thủ không',
        title="Tiêu đề",
        description="Mô tả",
        links='Link của các trang, phần cách bằng dấu cách',
        archive="Link archive"
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
            archive: str = None,
    ):
        cabin_channel = self.bot.config["cabin_channel"]
        sech_thu = self.bot.config["sech_thu"]

        if interaction.channel_id != cabin_channel:
            return

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

        if caption == '.':
            content = ''
        elif caption:
            if mention and not str(sech_thu) in caption:
                content = f'<@&{sech_thu}> {caption}'
            else:
                content = caption
        else:
            content = message.content

        emb = create_embed(*data.values())

        await message.edit(content=content, embed=emb)
        await interaction.response.send_message(embed=discord.Embed(title=f"Đã chỉnh sửa thành công tin nhắn tại {message_link}!", color=0x2E8B57))


async def setup(bot):
    await bot.add_cog(EditCog(bot))