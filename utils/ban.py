import discord
import asyncio
import json

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

async def ban_user(guild, member, time_now):
    await member.send("Auto ban, nghịch ngu thì liên hệ admin")
    await guild.ban(
        member,
        reason="Auto ban, nghịch ngu thì liên hệ admin",
        delete_message_seconds=3600
    )
    temp_ban[str(guild.id)] = temp_ban.get(str(guild.id), []) + [(member.id, time_now)]
    await save_temp_ban()

async def unban(guild_id, id, t):
    try:
        guild = bot.get_guild(int(guild_id))
        user = discord.Object(id=id)
        await guild.unban(user)
    finally:
        temp_ban[guild_id].remove((id, t))
        await save_temp_ban()

async def check_unban(time_now, temp_ban_time):
    for guild in temp_ban:
        for id, t in temp_ban[guild].copy():
            if t + temp_ban_time < time_now:
                asyncio.create_task(unban(guild, id, t))

bot = None
temp_ban = load_temp_ban()
lock = asyncio.Lock()