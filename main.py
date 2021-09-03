import discord
from discord.ext import commands
import json
import os

with open("config.json", "r") as f:
    config = json.load(f)
bot = commands.Bot(
        command_prefix='-',
        allowed_mentions=discord.AllowedMentions(roles=False, everyone=False, users=True)
    )

@bot.command()
async def reload(ctx, cog):
    for filename in os.listdir("cogs"):
        if filename[:-3] == cog:
            bot.reload_extension(f"cogs.{filename[:-3]}")
            return await ctx.send("Done")
    return await ctx.send("Cog not found")

bot.global_queue = {}
for filename in os.listdir('cogs'):
    if filename.endswith(".py"):
        bot.load_extension(f"cogs.{filename[:-3]}")

bot.run(config["token"])


