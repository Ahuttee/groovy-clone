import discord
from discord.ext import commands
from utils import player, queue
from stuff import player_info

class Effects(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['v'])
    async def volume(self, ctx, n):
        if await queue.check_user_vc(self.bot, ctx):
            return

        ffmpeg_options = self.bot.global_queue[ctx.author.voice.channel.id]['ffmpeg_options']
        if n == "reset":
            if not 'volume' in ffmpeg_options:
                return
            del ffmpeg_options['volume']
            player.restart(self, ctx)
            return

        n = int(n)
        ffmpeg_options['volume'] = f'volume={n/100}'
        player.restart(self,ctx)
        await ctx.send(embed=discord.Embed(description=f"Volume set to {n}%", color=player_info.green))

    @commands.command()
    async def speed(self, ctx, n):
        if await queue.check_user_vc(self.bot, ctx):
            return
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        if n == 'clear':
            if not 'speed' in local_queue['ffmpeg_options']:
                return

            del local_queue['ffmpeg_options']['speed']
            player.restart(self, ctx)
            return

        n = int(n)
        if n < 50 or n > 200:
            return await ctx.send(embed=discord.Embed(description=f"Speed is only limited between 50% and 200%", color=player_info.green))

        local_queue['ffmpeg_options']['speed'] = f"atempo={n/100}"
        player.restart(self, ctx)
        await ctx.send(embed=discord.Embed(description=f"Speed set to {n}%", color=player_info.green))


    @commands.command(aliases=['ffopt'])
    async def ffopts(self, ctx, *, ffopts):
        """Replays song with specified ffmpeg options"""

        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        local_queue['vc_obj'].stop()
        try:
            timestamp = local_queue['time_elapsed']
            local_queue['vc_obj'].play(discord.FFmpegPCMAudio(source=local_queue['song_list'][local_queue['current']]['url'], options=ffopts + f" -vn -ss {timestamp}"))
        except Exception as e:
            await ctx.send("There was an exception: " + str(e))

    @commands.command()
    async def seek(self, ctx, n: int):
        """Skips to specified timestamp (in seconds)"""
        if await queue.check_user_vc(self.bot, ctx):
            return
        # Check if a song is actually playing in the vc
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        if not local_queue['vc_obj'].is_playing():
            return await ctx.send("The song is not currently playing in this vc")
        options = player.parse_options(local_queue['ffmpeg_options'])
        local_queue['time_elapsed'] = n
        player.restart(self, ctx)

    @commands.command(aliases=['ff'])
    async def fastfoward(self, ctx, n: int):
        """Fast fowards (in seconds), use negative numbers to rewind"""
        if await queue.check_user_vc(self.bot, ctx):
            return
        new_timestamp = self.bot.global_queue[ctx.author.voice.channel.id]['time_elapsed'] + n
        await self.seek(ctx, new_timestamp)
        await ctx.send(embed=discord.Embed(description=f"Fast fowarded {n} seconds", color=player_info.green))

    @commands.command()
    async def reset(self,ctx):
        if await queue.check_user_vc(self.bot, ctx):
            return

        self.bot.global_queue[ctx.author.voice.channel.id]['ffmpeg_options'] = {}
        player.restart(self, ctx)
        await ctx.send(embed=discord.Embed(description="All effects has been cleared", color=player_info.green))




    @commands.command()
    async def bass(self, ctx, n):
        if await queue.check_user_vc(self.bot, ctx):
            return
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        if n == 'clear':
            if not 'bass' in local_queue['ffmpeg_options']:
                return

            del local_queue['ffmpeg_options']['bass']
            player.restart(self, ctx)
            return

        n = int(n)
        local_queue['ffmpeg_options']['bass'] = f"bass=g={n}"
        player.restart(self, ctx)
        await ctx.send(embed=discord.Embed(description=f"Bass set to {n}", color=player_info.green))




    @commands.command()
    async def pitch(self, ctx, n):
        if await queue.check_user_vc(self.bot, ctx):
            return
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        if n == 'reset':
            if not 'pitch' in local_queue['ffmpeg_options']:
                return

            del local_queue['ffmpeg_options']['pitch']
            player.restart(self, ctx)
            return

        n = int(n)
        local_queue['ffmpeg_options']['pitch'] = f"asetrate={n + 44100}"
        player.restart(self, ctx)
        await ctx.send(embed=discord.Embed(description=f"Pitch has been offset to {n}", color=player_info.green))


def setup(bot):
    bot.add_cog(Effects(bot))
