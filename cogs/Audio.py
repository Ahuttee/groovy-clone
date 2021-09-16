import discord
import json
from discord.ext import commands
from utils import player, queue
from stuff import player_info
import asyncio
import random
import time

class Audio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
    
    @commands.command(aliases=["q"])
    async def queue(self, ctx):
        if ctx.author.voice == None:
            return await ctx.send("You're not connected to a voice channel")
        text = ""
        vc_id = ctx.author.voice.channel.id
        if vc_id not in self.bot.global_queue:
            text = "Queue is empty"
        elif len(self.bot.global_queue[vc_id]['song_list']) == 0:
            text = "Queue is empty"
        else:
            local_queue = self.bot.global_queue[vc_id]
            song_index = 0
            for song in local_queue['song_list']:
                if song_index == local_queue['current']:
                    text += f"**{song_index}: {song['title']}**\n"
                else:
                    text += f"{song_index}: {song['title']}\n"
                song_index += 1

        await ctx.send(embed=discord.Embed(title="Song queue", description=text, color=player_info.green))
 
    async def start_song_loop(self, ctx):
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        if local_queue['lock']: return
        vc = local_queue['vc_obj']  
        #Else
        local_queue['lock'] = True
        while (local_queue['current'] < len(local_queue['song_list'])):
            options = player.parse_options(local_queue['ffmpeg_options'])
            song_info = local_queue['song_list'][local_queue['current']]
            vc.play(discord.FFmpegPCMAudio(source=song_info['url'], options=options))
            while vc.is_playing() or local_queue['pause']:
                await asyncio.sleep(1)
                local_queue['time_elapsed'] += 1*(not local_queue['pause']) # Will add 1 if its not pause
            # Since song finished, Go to next song
            if not local_queue['loop']: local_queue['current'] += 1
            local_queue['time_elapsed'] = 0

            # Reset current song to 0 if user wants to loop the queue
            if local_queue['loopqueue']:
                if local_queue['current'] >= len(local_queue['song_list']):
                    local_queue['current'] = 0
                    vc.play(discord.FFmpegPCMAudio(source="songs/vVR8yM-POY8"))  # We  do a little trolling       
                    await asyncio.sleep(6)
        vc.play(discord.FFmpegPCMAudio(source="songs/vVR8yM-POY8")) # Here aswell
        local_queue['lock'] = False
    
    @commands.command(aliases=["p"])
    async def play(self, ctx, *, query):

        if ctx.author.voice == None:
            return await ctx.send(embed=discord.Embed(description="You're not connected to a voice channel", color=player_info.red))

        user_vc = ctx.author.voice.channel
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        # Measure time (for flexing purposes)
        initial_time = time.monotonic()
    
        if not vc:
            vc = await user_vc.connect()
        
        if vc.channel.id not in self.bot.global_queue:
            self.bot.global_queue[vc.channel.id] = {"lock":False, "current": 0, "song_list": [], "vc_obj": vc, "loop":False, "pause":False, "time_elapsed": 0, "loopqueue":True, "ffmpeg_options":{}}
        local_queue = self.bot.global_queue[vc.channel.id]
        
        queries = query.split(",")
        queue_text = ""
    
        for query in queries:
            info = await player.search(query)
            local_queue['song_list'].append(info)
            queue_text += info['title'] + '\n'
        # Remove the last newline character from string
        queue_text = queue_text[:-1]

        # Done
        time_taken = round( (time.monotonic() - initial_time) * 1000, 3)
        await ctx.send(embed=discord.Embed(title=f"Queued ({time_taken}ms)", description=queue_text, color=player_info.green))
        await self.start_song_loop(ctx)

    @commands.command()
    async def loop(self, ctx):
        """Toggles loop from queue, song and to disable loop"""
        if await queue.check_user_vc(self.bot, ctx):
            return

        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        if local_queue['loop']:
            local_queue['loop'] = False
            local_queue['loopqueue'] = False
            text = "Loop disabled"

        elif local_queue['loopqueue']:
            local_queue['loopqueue'] = False
            local_queue['loop'] = True
            text = "Looping current song"

        else:
            local_queue['loopqueue'] = True
            local_queue['loop'] = False
            text = "Looping queue"

        await ctx.send(embed=discord.Embed(description=text, color=player_info.green))

    @commands.command()
    async def replay(self, ctx):
        """Plays song starting from the beginning in queue"""
        if await queue.check_user_vc(self.bot, ctx):
            return
        vc_id = ctx.author.voice.channel.id
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]

        local_queue['current'] = 0
        local_queue['time_elapsed'] = 0
        await self.start_song_loop(ctx)
        player.restart(self, ctx)
        await ctx.send(embed=discord.Embed(description="Replaying queue from the start", color=player_info.green))
    
    @commands.command(aliases=['s'])
    async def skip(self, ctx):
        if await queue.check_user_vc(self.bot, ctx):
            return
        vc_id = ctx.author.voice.channel.id
        
        local_queue = self.bot.global_queue[vc_id]
        local_queue['vc_obj'].stop()

    @commands.command(aliases=['stop'])
    async def pause(self, ctx):
        if await queue.check_user_vc(self.bot, ctx):
            return
        
        self.bot.global_queue[ctx.author.voice.channel.id]['vc_obj'].pause()
        self.bot.global_queue[ctx.author.voice.channel.id]['pause'] = True

        await ctx.send(embed=discord.Embed(description="Paused", color=player_info.green))
    
    @commands.command(aliases=['resume'])
    async def unpause(self, ctx):
        if await queue.check_user_vc(self.bot, ctx):
            return
        
        self.bot.global_queue[ctx.author.voice.channel.id]['vc_obj'].resume()
        self.bot.global_queue[ctx.author.voice.channel.id]['pause'] = False
        await ctx.send(embed=discord.Embed(description="Unpaused", color=player_info.green))
    
    @commands.command(aliases=['j'])
    async def jump(self, ctx, n: int):
        """Jumps to specific location in queue, usage: jump <song number>"""
        if await queue.check_user_vc(self.bot, ctx):
            return

        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        local_queue['time_elapsed'] = 0
        local_queue['current'] = n
        await self.start_song_loop(ctx)
        player.restart(self, ctx)
    
    @commands.command(aliases=['b'])
    async def back(self, ctx):
        """Replays previous song"""
        if await queue.check_user_vc(self.bot, ctx):
            return
        
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        n = local_queue['current'] - 1
        if n < 0:   n = 0
        await self.jump(ctx, n)
    

    @commands.command(aliases=['c'])
    async def clear(self, ctx):
        """Clears queue"""
        if await queue.check_user_vc(self.bot, ctx):
            return

        self.bot.global_queue[ctx.author.voice.channel.id]['song_list'] = []
        self.bot.global_queue[ctx.author.voice.channel.id]['current'] = 0
        await ctx.send(embed=discord.Embed(description="Queue has been cleared", color=player_info.green))

    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        if await queue.check_user_vc(self.bot, ctx):
            return

        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        local_queue['vc_obj'].stop()
        await local_queue['vc_obj'].disconnect()
        local_queue['loop'] = False
        local_queue['current'] = 0
        local_queue['pause'] = False
        local_queue['destroy'] = True

        del self.bot.global_queue[ctx.author.voice.channel.id]
        await ctx.send(embed=discord.Embed(description="Disconnected", color=player_info.green))

    @commands.command()
    async def remove(self, ctx, n: int):
        """Removes specified song number"""
        if await queue.check_user_vc(self.bot, ctx):
            return #check if user is in vc and stuff


        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        if n-1 > len(local_queue['song_list']):
            return await ctx.send("invalid song number")


        local_queue['song_list'].pop(n)
        await ctx.send(embed=discord.Embed(description=f"Removed song number {n}", color=player_info.green))
    
    @commands.command()
    async def shuffle(self, ctx):
        # Check if user is in a vc and if it contains a queue
        if await queue.check_user_vc(self.bot, ctx):
            return

        song_list = self.bot.global_queue[ctx.author.voice.channel.id]['song_list']

        # Actual shuffling begins here
        list_length = len(song_list)
        for i in range(list_length-1, 0, -1):
            j = random.randint(0, i+1)
            temp = song_list[i]
            song_list[i] = song_list[j]
            song_list[j] = temp


        await ctx.send(embed=discord.Embed(description="Shuffled", color=player_info.green))

    @commands.command(aliases=['np'])
    async def current(self, ctx):
        if await queue.check_user_vc(self.bot, ctx):
            return
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        if local_queue['vc_obj'].is_playing():
            # Create the progress bar (unit of 20), this is kinda fun lol 
            current_song = local_queue['song_list'][local_queue['current']]
            progress = int( (local_queue['time_elapsed'] / current_song['duration']) * 13)
            leftbars = "▬" * progress
            rightbars = "▬" * (13 - progress)
            await ctx.send(embed=discord.Embed(title=current_song['title'], description=f"{leftbars}🔵{rightbars} {int(local_queue['time_elapsed'])}/{current_song['duration']}s", color=player_info.green))
        else:
            await ctx.send(embed=discord.Embed(description="A song is not playing", color=player_info.green))

def setup(bot):
    bot.add_cog(Audio(bot))


        
