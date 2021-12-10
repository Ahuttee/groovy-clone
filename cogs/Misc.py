import discord
from discord.ext import commands
import lyricsgenius
from youtube_dl import YoutubeDL
from stuff import player_info
import json
import os
import subprocess

with open("config.json", 'r') as f:
    config = json.load(f)

genius = lyricsgenius.Genius(os.environ['GENIUS_TOKEN'])

def auth(ctx):
    return ctx.author.id in config['authorized']

class Misc(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    @commands.command()
    @commands.check(auth)
    async def shell(self, ctx, *, args):
        await ctx.send(subprocess.getoutput(args))
           

    @commands.command()
    @commands.check(auth)
    async def db(self, ctx, command, *, query):

        if command == 'get':
            with YoutubeDL({'noplaylists':True,'quiet':True, 'format':'bestaudio'}) as ytdl:
                info = ytdl.extract_info("ytsearch:" + query,download=False)['entries'][0]
            text = f"title: {info['title']}\nid: {info['id']}\nfilesize: {info['filesize']} bytes\nduration: {info['duration']}s\n"
            text += f"in song_index? {info['id'] in song_index}\n"
            filepath = "./songs/" + info['id']
            text += f"supposed filepath: {filepath}\n"
            text += f"full file exists? {os.path.exists(filepath)}\n"
            text += f".part file exists? {os.path.exists(filepath + '.part')}\n"
            if info['id'] in song_index:
                text += f"queries: {song_index[info['id']]['queries']}"
            
            await ctx.send(text)

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
        

        


