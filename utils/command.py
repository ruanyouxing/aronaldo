import os

async def load_cogs(bot):
    for cmd in os.listdir("./cogs"):
        if cmd.endswith(".py"):
            await bot.load_extension(f"cogs.{cmd[:-3]}")
    await bot.tree.sync()

async def reload_cogs(bot):
    for cmd in os.listdir("./cogs"):
        if cmd.endswith(".py"):
            await bot.reload_extension(f"cogs.{cmd[:-3]}")
    await bot.tree.sync()