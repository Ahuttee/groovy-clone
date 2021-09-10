import discord
from discord.ext import commands

class Test(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command()
    async def listqueue(self, ctx):
        await ctx.send(str(self.bot.global_queue))


def setup(bot):
    bot.add_cog(Test(bot))
