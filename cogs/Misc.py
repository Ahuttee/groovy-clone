import discord
from discord.ext import commands
import lyricsgenius
from stuff import player_info
import json

with open("config.json", 'r') as f:
    config = json.load(f)

genius = lyricsgenius.Genius(config['geniusapitoken'])

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @commands.command(aliases=['lyric'])
    async def lyrics(self, ctx, *, song_name=None):
        if song_name:
            song = genius.search_song(song_name)
            if song:
                await ctx.send(embed=discord.Embed(title=song.title, description=song.lyrics, color=player_info.green))
            else:
                await ctx.send(embed=discord.Embed(description="Song not found", color=player_info.red))
            return

        #else search for the current song in queue (if there even is one)
        if ctx.author.voice == None or ctx.author.voice.channel.id not in self.bot.global_queue:
            return ctx.send(embed=discord.Embed(description="Specify song name", color=player_info.red))

        # Here, this is checking if the local queue is locked because if it is, then there likely is a song actually playing
        local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
        if local_queue['lock']:
            song_name = local_queue['song_list'][local_queue['current']]['query']
            song = genius.search_song(song_name)
            if song:
                await ctx.send(embed=discord.Embed(title=song.title, description=song.lyrics, color=player_info.green))
            else:
                await ctx.send(embed=discord.Embed(description="Song not found", color=player_info.red))
            return

        #Else
        return ctx.send(embed=discord.Embed(description="Specify song name", color=player_info.red))

def setup(bot):
    bot.add_cog(Misc(bot))
        

        


