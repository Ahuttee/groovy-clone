import youtube_dl
from stuff import player_info
import discord
import json
import asyncio
import threading
import os

async def check_user_vc(bot, ctx):  #Check if user is in a vc & if that vc contains a queue
    if ctx.author.voice == None:
        await ctx.send(embed=discord.Embed(description="You're not in a vc", color=player_info.red))
        return True
    if ctx.author.voice.channel.id not in bot.global_queue:
        await ctx.send(embed=discord.Embed(description="This vc does not contain a queue", color=player_info.red))
        return True

def parse_options(option_dict):
    options = ""
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

    return options


# Gets song information
async def search(query):
    ytdl_options = {
    "noplaylist": True,
    "format": "bestaudio",
    "quiet": True,
        }
    with youtube_dl.YoutubeDL(ytdl_options) as ytdl:
        song_info = ytdl.extract_info('ytsearch:' + query, download=False)['entries'][0]
    if song_info:
        return {
            "title": song_info['title'],
            "url":  song_info['url'],
            "query": query,
            "duration": song_info['duration']
        }
    else:
        return False
 
def restart(self, ctx):
    local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
    local_queue['vc_obj'].stop()
    # Add exisitng effects
    options = parse_options(local_queue['ffmpeg_options'])
    local_queue['vc_obj'].play(discord.FFmpegPCMAudio(before_options=f"-vn -ss {local_queue['time_elapsed']}", source=local_queue['song_list'][local_queue['current']]['url'], options=options))

