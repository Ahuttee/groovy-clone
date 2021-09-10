async def check_user_vc(bot, ctx):  #Check if user is in a vc & if that vc contains a queue
    if ctx.author.voice == None:
        await ctx.send("You're not in a vc")
        return True
    if ctx.author.voice.channel.id not in bot.global_queue:
        await ctx.send("This vc does not contain a queue")
        return True


