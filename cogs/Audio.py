import discord
from discord.ext import commands
from utils import audio_extract
import asyncio
import random

class Audio(commands.Cog):
    def __init__(self, bot):
        self.bot = bot
        self.bool_response = ["disabled", "enabled"]
        self.embed_color = discord.Colour.from_rgb(42, 204, 112)


    async def check_user_vc(self, ctx):  #Check if user is in a vc & if that vc contains a queue
        if ctx.author.voice == None:
            await ctx.send("You're not in a vc")
            return True
        if ctx.author.voice.channel.id not in self.bot.global_queue:
            await ctx.send("This vc does not contain a queue")
            return True

    def parse_options(self, option_dict):
        if len(option_dict) > 0:
            options = "-filter_complex '"
            if len(option_dict) > 1:
                for effect in option_dict:
                    options += option_dict[effect] + ","
                options = options[:-1]
            else:
                for effect in option_dict:
                    options += option_dict[effect]
            options += "'"
        else:
            options = ""

        return options

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
            for song in local_queue['song_list']:
                song_index = local_queue['song_list'].index(song)
                if song_index == local_queue['current']:
                    text += f"**{song_index}: {song['title']}**\n"
                else:
                    text += f"{song_index}: {song['title']}\n"

        await ctx.send(embed=discord.Embed(title="Song queue", description=text, color=self.embed_color))
    
    @commands.command(aliases=["p"])
    async def play(self, ctx, *, query):
        if ctx.author.voice == None:
            return await ctx.send("You're not connected to a voice channel")

        user_vc = ctx.author.voice.channel
        vc = discord.utils.get(self.bot.voice_clients, guild=ctx.guild)
        if not vc:
            vc = await user_vc.connect()
            await ctx.send("connected")
        
        if vc.channel.id not in self.bot.global_queue:
            self.bot.global_queue[vc.channel.id] = {"current": 0, "song_list": [], "vc_obj": vc, "loop":False, "destroy":False, "pause":False, "time_elapsed": 0, "loopqueue":False, "ffmpeg_options":{}}
        local_queue = self.bot.global_queue[vc.channel.id]
        
        queries = query.split(",")
        queue_text = ""
        for query in queries:
            if query[-2:] == '-b':
                query = query[:-2]
                info = audio_extract.search(query, bilibili=True)
            else:
                info = audio_extract.search(query)
            local_queue['song_list'].append(info)
            queue_text += info['title'] + '\n'
        # Remove the last newline character from string
        queue_text = queue_text[:-1]

        await ctx.send(embed=discord.Embed(title="Queued", description=queue_text, color=self.embed_color))
        if not vc.is_playing():
            while not (local_queue['destroy']):

                while local_queue['current'] > (len(local_queue['song_list'])-1):
                    await asyncio.sleep(1) # Stop it from playing more songs until song count is at a normal value
                
                options = self.parse_options(local_queue['ffmpeg_options'])

                song_info = local_queue['song_list'][local_queue['current']]
                vc.play(discord.FFmpegPCMAudio(source=song_info['url'], options=options))
                while (vc.is_playing() or local_queue['pause']):
                    await asyncio.sleep(0.5)
                    local_queue['time_elapsed'] += 0.5*(not local_queue['pause'])

                if not local_queue["loop"]:
                    local_queue['current'] += 1
                
                if local_queue['current'] > len(local_queue['song_list'])-1:
                    if local_queue['loopqueue']:
                        local_queue['current'] = 0
                
                local_queue['time_elapsed'] = 0
            del self.bot.global_queue[vc.channel.id]

    @commands.command()
    async def loop(self, ctx):
        """Toggles loop from queue, song and to disable loop"""
        if await self.check_user_vc(ctx):
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

        await ctx.send(embed=discord.Embed(description=text, color=self.embed_color))

    @commands.command()
    async def replay(self, ctx):
        """Plays song starting from the beginning in queue"""
        if await self.check_user_vc(ctx):
            return
        vc_id = ctx.author.voice.channel.id
        
        self.bot.global_queue[vc_id]['current'] = 0
        await ctx.send(embed=discord.Embed(description="Replaying queue from the start", color=self.embed_color))
    
    @commands.command(aliases=['s'])
    async def skip(self, ctx):
        if await self.check_user_vc(ctx):
            return
        vc_id = ctx.author.voice.channel.id
        
        local_queue = self.bot.global_queue[vc_id]
        local_queue['vc_obj'].stop()

    @commands.command(aliases=['stop'])
    async def pause(self, ctx):
        if await self.check_user_vc(ctx):
            return
        
        self.bot.global_queue[ctx.author.voice.channel.id]['vc_obj'].pause()
        self.bot.global_queue[ctx.author.voice.channel.id]['pause'] = True

        await ctx.send(embed=discord.Embed(description="Paused", color=self.embed_color))
    @commands.command(aliases=['resume'])
    async def unpause(self, ctx):
        if await self.check_user_vc(ctx):
            return
        
        self.bot.global_queue[ctx.author.voice.channel.id]['vc_obj'].resume()
        self.bot.global_queue[ctx.author.voice.channel.id]['pause'] = False
        await ctx.send(embed=discord.Embed(description="Unpaused", color=self.embed_color))
    
    @commands.command(aliases=['j'])
    async def jump(self, ctx, n: int):
        """Jumps to specific location in queue, usage: jump <song number>"""
        if await self.check_user_vc(ctx):
            return

        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        local_queue['time_elapsed'] = 0
        local_queue['current'] = n
        await self.restart(ctx)
    @commands.command(aliases=['b'])
    async def back(self, ctx):
        """Replays previous song"""
        if await self.check_user_vc(ctx):
            return
        
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        n = local_queue['current'] - 1
        if n < 0:   n = 0
        await self.jump(ctx, n)
    

    @commands.command(aliases=['c'])
    async def clear(self, ctx):
        """Clears queue"""
        if await self.check_user_vc(ctx):
            return

        self.bot.global_queue[ctx.author.voice.channel.id]['song_list'] = []
        self.bot.global_queue[ctx.author.voice.channel.id]['current'] = 0
        await ctx.send(embed=discord.Embed(description="Queue has been cleared", color=self.embed_color))

    @commands.command(aliases=['dc'])
    async def disconnect(self, ctx):
        if await self.check_user_vc(ctx):
            return

        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        local_queue['vc_obj'].stop()
        await local_queue['vc_obj'].disconnect()
        local_queue['loop'] = False
        local_queue['pause'] = False
        local_queue['destroy'] = True

        
        await ctx.send(embed=discord.Embed(description="Disconnected", color=self.embed_color))

    @commands.command()
    async def remove(self, ctx, n: int):
        """Removes specified song number"""
        if await self.check_user_vc(ctx):
            return #check if user is in vc and stuff


        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        if n-1 > len(local_queue['song_list']):
            return await ctx.send("invalid song number")


        local_queue['song_list'].pop(n)
        await ctx.send(embed=discord.Embed(description=f"Removed song number {n+1}"))
    
    @commands.command()
    async def restart(self, ctx):
        """Restarts player, useful if it gets stuck for some reason"""
        
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        local_queue['vc_obj'].stop()
        try:
            # Add exisitng effects
            options = self.parse_options(local_queue['ffmpeg_options'])

            timestamp = local_queue['time_elapsed']
            local_queue['vc_obj'].play(discord.FFmpegPCMAudio(source=local_queue['song_list'][local_queue['current']]['url'], options=options + f" -vn -ss {timestamp}"))
        except Exception as e:
            await ctx.send(str(e))


    @commands.command(aliases=['ffopt'])
    async def ffopts(self, ctx, *, ffopts):
        """Replays song with specified ffmpeg options"""
        
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        local_queue['vc_obj'].stop()
        try:
            timestamp = local_queue['time_elapsed']
            local_queue['vc_obj'].play(discord.FFmpegPCMAudio(source=local_queue['song_list'][local_queue['current']]['url'], options=ffopts + f" -vn -ss {timestamp}"))
        except Exception as e:
            await ctx.send(str(e))
        
    @commands.command()
    async def seek(self, ctx, n: int):
        """Skips to specified timestamp (in seconds)"""
        if await self.check_user_vc(ctx):
            return
        # Check if a song is actually playing in the vc
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        if not local_queue['vc_obj'].is_playing():
            return await ctx.send("The song is not currently playing in this vc")
        options = self.parse_options(local_queue['ffmpeg_options'])
        local_queue['vc_obj'].stop()
        local_queue['vc_obj'].play(discord.FFmpegPCMAudio(source=local_queue['song_list'][local_queue['current']]['url'], options=options + f"-vn -ss {n}"))
        

    @commands.command(aliases=['ff'])
    async def fastfoward(self, ctx, n: int):
        """Fast fowards (in seconds), use negative numbers to rewind"""
        if await self.check_user_vc(ctx):
            return
        new_timestamp = self.bot.global_queue[ctx.author.voice.channel.id]['time_elapsed'] + n
        await self.seek(ctx, new_timestamp)
        await ctx.send(embed=discord.Embed(description=f"Fast fowarded {n} seconds", color=self.embed_color))

    @commands.command()
    async def reset(self,ctx):
        if await self.check_user_vc(ctx):
            return

        self.bot.global_queue[ctx.author.voice.channel.id]['ffmpeg_options'] = {}
        await self.restart(ctx)
        await ctx.send(embed=discord.Embed(description="All effects has been cleared", color=self.embed_color))

    @commands.command()
    async def bass(self, ctx, n):
        if await self.check_user_vc(ctx):
            return
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id] 
        if n == 'clear':
            if not 'bass' in local_queue['ffmpeg_options']:
                return
            
            del local_queue['ffmpeg_options']['bass']
            await self.restart(ctx)
            return

        n = int(n)
        local_queue['ffmpeg_options']['bass'] = f"bass=g={n}"
        await self.restart(ctx)
        await ctx.send(embed=discord.Embed(description=f"Bass set to {n}", color=self.embed_color))

    @commands.command()
    async def speed(self, ctx, n):
        if await self.check_user_vc(ctx):
            return
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id] 
        if n == 'clear':
            if not 'speed' in local_queue['ffmpeg_options']:
                return
            
            del local_queue['ffmpeg_options']['speed']
            await self.restart(ctx)
            return

        n = int(n)
        if n < 50 or n > 200:
            return await ctx.send(embed=discord.Embed(description=f"Speed is only limited between 50% and 200%", color=self.embed_color))

        local_queue['ffmpeg_options']['speed'] = f"atempo={n/100}"
        await self.restart(ctx)
        await ctx.send(embed=discord.Embed(description=f"Speed set to {n}", color=self.embed_color))

    @commands.command()
    async def pitch(self, ctx, n):
        if await self.check_user_vc(ctx):
            return
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id] 
        if n == 'reset':
            if not 'pitch' in local_queue['ffmpeg_options']:
                return
            
            del local_queue['ffmpeg_options']['pitch']
            await self.restart(ctx)
            return

        n = int(n)
        local_queue['ffmpeg_options']['pitch'] = f"asetrate={n + 44100}"
        await self.restart(ctx)
        await ctx.send(embed=discord.Embed(description=f"Pitch has been offset to {n}", color=self.embed_color))

 
    @commands.command()
    async def shuffle(self, ctx):
        # Check if user is in a vc and if it contains a queue
        if await self.check_user_vc(ctx):
            return

        song_list = self.bot.global_queue[ctx.author.voice.channel.id]['song_list']

        # Actual shuffling begins here
        list_length = len(song_list)
        print(song_list)
        for i in range(list_length-1, 0, -1):
            j = random.randint(0, i+1)
            temp = song_list[i]
            song_list[i] = song_list[j]
            song_list[j] = temp


        await ctx.send(embed=discord.Embed(description="Shuffled", color=self.embed_color))

    @commands.command(aliases=['v'])
    async def volume(self, ctx, n):
        if await self.check_user_vc(ctx):
            return

        ffmpeg_options = self.bot.global_queue[ctx.author.voice.channel.id]['ffmpeg_options']
        if n == "reset":
            if not 'volume' in ffmpeg_options:
                return
            del ffmpeg_options['volume']
            await self.restart(ctx)
            return
        
        n = int(n)
        ffmpeg_options['volume'] = f'volume={n/100}'
        await self.restart(ctx)
        await ctx.send(embed=discord.Embed(description=f"Volume set to {n}%", color=self.embed_color))
    
    
def setup(bot):
    bot.add_cog(Audio(bot))



        
