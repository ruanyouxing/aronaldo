import asyncio
import json

bot = None
temp_ban = None
lock = asyncio.Lock()

async def save_temp_ban():
    async with lock:
        with open('./config_and_storage/temp_ban.json', 'w') as f:
            json.dump(temp_ban, f, indent=4)

def load_temp_ban():
    try:
        with open('./config_and_storage/temp_ban.json', 'r') as f:
            return json.load(f)
    except:
        return {}

async def unban(guild_id, id, t):
    try:
        guild = bot.get_guild(int(guild_id))
        user = discord.Object(id=id)
        await guild.unban(user)
    finally:
        temp_ban[guild_id].remove([id, t])
        await save_temp_ban()