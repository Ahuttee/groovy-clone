import discord
import json
from stuff import player_info
from utils import player
from discord.ext import commands

with open("db/playlist.json", "r") as f:
    playlist_db = json.load(f)

# An additional retarded step to convert all id keys to string, thx json
playlist_db = { int(user_id):value for user_id,value in playlist_db.items() }

class Playlist(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    
    async def check_user_stuff(self, ctx):
        # I dislike having to check so many times
        if ctx.author.id not in playlist_db:
            playlist_db[ctx.author.id] = {}
            await ctx.send(embed=discord.Embed(description="You dont have any playlists"))
            return True
        if len(playlist_db[ctx.author.id]) == 0:
            await ctx.send(embed=discord.Embed(description="You dont have any playlists"))
            return True

    @commands.command(aliases=["list", "l"])
    async def listplaylist(self, ctx, *, name=None):
        if await self.check_user_stuff(ctx):
            return
        
        playlists = playlist_db[ctx.author.id]
        if name == None:
            text = ""
            for playlist in playlists:
                text += playlist + "\n"
            await ctx.send(embed=discord.Embed(title="Playlists", description=text, color=player_info.green))
        else:
            if name not in playlists:   return await ctx.send(embed=discord.Embed(description="Playlist does not exist", color=player_info.red))
            text = ""
            for song in playlists[name]:
                text += song['title'] + "\n"
            await ctx.send(embed=discord.Embed(title=name, description=text, color=player_info.green))

    @commands.command()
    async def load(self, ctx, *, name, overwrite=True):
        if await self.check_user_stuff(ctx):
            return
        if ctx.author.voice == None:    return await ctx.send(embed=discord.Embed(description="You're not in a voice channel", color=player_info.red))
        playlists = playlist_db[ctx.author.id]
        if name not in playlists:   return await ctx.send(embed=discord.Embed(description="Playlist does not exist", color=player_info.red))

        play_command_text = ""
        loading_msg = await ctx.send(embed=discord.Embed(description="Loading playlist...", color=player_info.blue))
        for song in playlists[name]:
            play_command_text += song['query'] + ","
        # Remove the last ","
        play_command_text = play_command_text[:-1]

        await loading_msg.edit(embed=discord.Embed(description="Playlist loaded", color=player_info.green))
        await ctx.invoke(self.bot.get_command('play'), query=play_command_text)       

    @commands.command()
    async def append(self, ctx, *, name):
        await self.load(ctx, name=name, overwrite=False)

    @commands.command(aliases=['save'])
    async def unload(self, ctx, *, name):
        if await player.check_user_vc(self.bot, ctx):
            return
        if ctx.author.id not in playlist_db:    playlist_db[ctx.author.id] = {}


        queue = []
        for song in self.bot.global_queue[ctx.author.voice.channel.id]['song_list']:
            song_dict = {
                    'title':song['title'],
                    'query':song['query'],
                    }

            queue.append(song_dict)

        playlist_db[ctx.author.id][name] = queue.copy()
        with open("db/playlist.json", 'w') as f:
            json.dump(playlist_db, f)

        await ctx.send(embed=discord.Embed(description="Playlist saved", color=player_info.green))


def setup(bot):
    bot.add_cog(Playlist(bot))
