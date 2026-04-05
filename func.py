import discord
import asyncio
import json
import re

lock = asyncio.Lock()

async def save_temp_ban(temp_ban):
    async with lock:
        with open('temp_ban.json', 'w') as f:
            json.dump(temp_ban, f, indent=4)

async def unban(temp_ban, bot, guild_id, id, t):
    try:
        guild = bot.get_guild(int(guild_id))
        user = discord.Object(id=id)
        await guild.unban(user)
    finally:
        temp_ban[guild_id].remove([id, t])
        await save_temp_ban(temp_ban)

def load_temp_ban():
    try:
        with open('temp_ban.json', 'r') as f:
            return json.load(f)
    except:
        return {}

def split_message(text, limit=2000):
    parts = []
    while len(text) > limit:
        split_at = text.rfind(" ", 0, limit)
        if split_at == -1:
            split_at = limit
        parts.append(text[:split_at])
        text = text[split_at:].lstrip()
    parts.append(text)
    return parts

def create_embed(title, description, links, archive, archive_file):
    urls = ''
    web = ['vi-h', 'mimi', 'vina']
    for link in links.split():
        for w in web:
            if w in link:
                urls += f'🔗 [{w}]({link})\n'

    emb = discord.Embed(
        title = title,
        description = description,
        color = 0xba30ff,
        timestamp=datetime.datetime.now(datetime.timezone.utc)
        )
    if urls:
        emb.add_field(name='📎 Link', value=urls, inline=False)
    if archive:
        emb.add_field(name='📦 Archive', value=f'[Xem archive truyện]({archive})', inline=False)
    if archive_file:
        emb.add_field(name='📦 Archive', value='File ở bên dưới', inline=False)
    emb.add_field(name='📚 Truyện khác', value='[Những truyện khác chúng tôi làm](https://vi-hentai.pro/nhom-dich/eden-of-kivotos)', inline=False)
    emb.add_field(name='👥 Liên hệ', value='[Phan pếch chúng tôi](https://www.facebook.com/EdenOfKivotos7)', inline=False)
    return emb

def get_embed_data(emb):
    data = {
        "title": emb.title,
        "description": emb.description,
        "links": '',
        "archive": '',
        "archive_file": False
    }
    for field in emb.fields:
        name = field.name.strip()
        value = field.value.strip()

        if name == "📎 Link":
            data["links"] = ' '.join(re.findall(r'\((.*?)\)', value))
        elif name == "📦 Archive" and "http" in value:
            data["archive"] = re.findall(r'\((.*?)\)', value)[0]
        elif name == "📦 Archive" and value == "File ở bên dưới":
            data["archive_file"] = True
    return data