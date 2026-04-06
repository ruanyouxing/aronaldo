'''dev by caophihung'''

import discord
from discord import app_commands
from discord.ext import commands, tasks
from utils import ban
from utils import *
import asyncio
import io
import os

intents = discord.Intents.default()
intents.message_content = True
intents.members = True
bot = commands.Bot(command_prefix="!", intents=intents)

with open("./config_and_storage/config.json", "r") as f:
    data = json.load(f)
cabin_channel, announ_channel, bait_channel, sech_thu, whitelist, temp_ban_time = (
    data["cabin_channel"],
    data["announ_channel"],
    data["bait_channel"],
    data["sech_thu"],
    data["whitelist"],
    data["temp_ban_time"]
)
unban_checking = False
ban.bot = bot

@tasks.loop(seconds=10)
async def check_loop():
    await check_unban(get_time(), temp_ban_time)

@bot.event
async def on_ready():
    global unban_checking
    await bot.tree.sync()
    print(f'Bot đã đăng nhập với tên {bot.user}')
    if not unban_checking:
        unban_checking = True
        check_loop.start()

@bot.event
async def on_message(message):
    member = message.author
    if member == bot.user:
        return

    if message.channel.id == bait_channel:
        if not (member.id in whitelist or member.top_role >= message.guild.me.top_role):
            await ban_user(message.guild, member, get_time())

    if message.content.startswith(">batchuoc"):
        try:
            if message.channel.id != cabin_channel:
                return
            if not message.channel_mentions:
                return

            target = message.channel_mentions[0]
            content = ' '.join(message.content.split(' ')[2:])
            files = []
            
            for att in message.attachments:
                file = await att.read()
                if att.filename == "message.txt":
                    content = file.decode("utf-8")
                else:
                    files.append(discord.File(io.BytesIO(file), filename=att.filename))

            parts = split_message(content)
            for i, part in enumerate(parts):
                if i == len(parts) - 1:
                    await target.send(part, files=files)
                else:
                    await target.send(part)

        except Exception as e:
            print(e)

    await bot.process_commands(message)

@bot.tree.command(name="thongbao", description="Gửi thông báo")
@app_commands.describe(
    channel="Kênh gửi",
    caption="Caption",
    mention='Có auto thêm mention @Sếch Thủ không',
    title="Tiêu đề",
    description="Mô tả",
    links='Link của các trang, phần cách bằng dấu cách',
    cover="Ảnh bìa",
    archive="Link archive",
    archive_file="File archive"
)
async def thongbao(
    interaction: discord.Interaction,
    channel: discord.TextChannel = None,
    caption: str = '',
    mention: bool = True,
    title: str = '',
    description: str = '',
    links: str = '',
    cover: discord.Attachment = None,
    archive: str = '',
    archive_file: discord.Attachment = None
):
    if interaction.channel_id != cabin_channel: return
    await interaction.response.defer()

    if mention and not str(sech_thu) in caption:
        caption = f'<@&{sech_thu}> {caption}'

    if channel is None:
        channel = interaction.guild.get_channel(announ_channel)

    emb = create_embed(title, description, links, archive, archive_file)
    img = await cover.to_file() if cover else None

    await channel.send(caption, embed=emb, file=img)
    await channel.send(file=await archive_file.to_file()) if archive_file else None
    await interaction.followup.send(embed=discord.Embed(title="Đã gửi thông báo thành công vào channel " + channel.mention, color=0x00ff00))

@bot.tree.command(name="edit", description="Chỉnh sửa thông báo")
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
    interaction: discord.Interaction,
    message_link: str,
    caption: str = None,
    mention: bool = True,
    title: str = None,
    description: str = None,
    links: str = None,
    archive: str = None,
):
    if interaction.channel_id != cabin_channel: return
    edit_check = {
        'title': title,
        'description': description,
        'links': links,
        'archive': archive
    }
    parts = message_link.split("/")
    guild_id = int(parts[-3])
    channel_id = int(parts[-2])
    message_id = int(parts[-1])

    channel = bot.get_channel(channel_id)
    if channel is None:
        channel = await bot.fetch_channel(channel_id)

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
        content = message.content

    emb = create_embed(*data.values())

    await message.edit(content=content, embed=emb)
    await interaction.response.send_message(embed=discord.Embed(title="Đã chỉnh sửa thành công!", color=0x00ff00))

bot.run(os.getenv('TOKEN'))

'''dev by caophihung'''