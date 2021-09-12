import youtube_dl
from stuff import player_info
import discord
import json
import asyncio
import threading

with open("db/song_index.json", "r") as f:
    song_index = json.load(f)

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

def query_exists(query):
    for yt_id in song_index:
        if query in song_index[yt_id]['queries']:
            song_info = song_index[yt_id]
            return {
            "title": song_info['title'],
            "url":  song_info['url'],
            "query": query,
            "duration": song_info['duration']
        }
    return False


# Gets song information

def download_song(info_dict, options, query):
    global song_index
    with youtube_dl.YoutubeDL(options) as ytdl:
        ytdl.extract_info(info_dict['url'], download=True)
    song_index[info_dict['id']] = {
                "title":info_dict['title'],
                "url": f"songs/{info_dict['id']}",
                "queries": [query],
                "duration": info_dict['duration']
            }
    with open('db/song_index.json', 'w') as f:
        json.dump(song_index, f)    

async def search(query):
    global song_index

    ytdl_options = {
    "noplaylist": True,
    "format": "bestaudio",
    "quiet": True,
        }
    song_info = query_exists(query)
    if song_info:
        return {
            "title": song_info['title'],
            "url":  song_info['url'],
            "query": query,
            "duration": song_info['duration']
        }
    #else
    with youtube_dl.YoutubeDL(ytdl_options) as ytdl:
        info_dict = ytdl.extract_info('ytsearch:' + query, download=False)['entries'][0]
    if info_dict['id'] in song_index:
        song_index[info_dict['id']]['queries'].append(query)
        with open('db/song_index.json', 'w') as f:
            json.dump(song_index, f)
        return query_exists(query)
    else:
        ytdl_options['outtmpl'] = 'songs/' + info_dict['id']
        with youtube_dl.YoutubeDL(ytdl_options) as ytdl:
            song_index[info_dict['id']] = {
                "title":info_dict['title'],
                "url": f"songs/{info_dict['id']}",
                "queries": [query],
                "duration": info_dict['duration']
            }
            t = threading.Thread(target=download_song, args=[info_dict, ytdl_options, query])
            t.setDaemon(False)
            t.start()
            return {
                    "title":info_dict['title'],
                    "url":info_dict['url'],
                    "duration":info_dict['duration']
                    }

 
def restart(self, ctx):
    local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
    local_queue['vc_obj'].stop()
    # Add exisitng effects
    options = parse_options(local_queue['ffmpeg_options'])

    timestamp = local_queue['time_elapsed']
    local_queue['vc_obj'].play(discord.FFmpegPCMAudio(source=local_queue['song_list'][local_queue['current']]['url'], options=options +
f" -vn -ss {timestamp}"))

