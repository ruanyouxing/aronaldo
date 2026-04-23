import discord
import asyncio
import json
import os
import re

async def save_jail():
    async with lock:
        with open(file_path, 'w') as f:
            json.dump(jail_list, f, indent=4)

def load_jail():
    try:
        with open(file_path, 'r') as f:
            return json.load(f)
    except:
        return {}

def convert_time(time_str):
    pattern = r'(\d+)([smhd])'
    matches = re.findall(pattern, time_str.lower())

    total_seconds = 0

    for value, unit in matches:
        value = int(value)

        if unit == 's':
            total_seconds += value
        elif unit == 'm':
            total_seconds += value * 60
        elif unit == 'h':
            total_seconds += value * 3600
        elif unit == 'd':
            total_seconds += value * 86400
    return total_seconds

async def jail_user(interaction, member, time_now, jail_time, jail_role):
    guild = interaction.guild

    roles = [role for role in member.roles if role.id != guild.id]
    jail_role = guild.get_role(jail_role)

    await member.remove_roles(*roles)
    await member.add_roles(jail_role)

    jail_list[str(guild.id)] = jail_list.get(str(guild.id), {}) | {str(member.id): {"time": time_now + jail_time, "roles": [role.id for role in roles]}}
    await save_jail()

async def unjail_user(bot, guild_id, id, jail_role):
    try:
        guild = bot.get_guild(int(guild_id))
        member = guild.get_member(id)
        roles = [guild.get_role(rid) for rid in jail_list[str(guild_id)][str(id)]["roles"] if guild.get_role(rid)]
        jail_role = guild.get_role(jail_role)
        if jail_role in member.roles:
            await member.remove_roles(jail_role)
        await member.add_roles(*roles)
    finally:
        del jail_list[str(guild_id)][str(id)]
        await save_jail()

async def check_unjail(bot, time_now, jail_role):
    for guild in jail_list:
        for id, v in jail_list[guild].copy().items():
            if v["time"] < time_now:
                asyncio.create_task(unjail_user(bot, guild, int(id), jail_role))

# file_path = './storage'
# os.makedirs(file_path, exist_ok=True)
# file_path = os.path.join(file_path, "jail.txt")

file_path = os.path.expanduser("~/.local/state/aronaldo")
os.makedirs(file_path, exist_ok=True)
file_path = os.path.join(file_path, "jail.txt")

jail_list = load_jail()
lock = asyncio.Lock()