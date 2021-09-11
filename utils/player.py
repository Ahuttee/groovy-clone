import youtube_dl
from stuff import player_info
import discord
import asyncio

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

def search(query, is_url=False):
    ytdl_options = {
    "noplaylist": True,
    "format": "bestaudio",
    "quiet": True
        }

    if is_url:
        del ytdl_options['format']
    with youtube_dl.YoutubeDL(ytdl_options) as ytdl:
        if is_url:
            info_dict = ytdl.extract_info(query, download=False)
        else:
            info_dict = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]

    useful_info = {
                "title": info_dict['title'],
                "url":  info_dict['url'],
                "query": query,
                "is_url": is_url,
                "duration": info_dict['duration']
            }

    return useful_info
 
async def restart(self, ctx):
    local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
    local_queue['vc_obj'].stop()
    # Add exisitng effects
    options = parse_options(local_queue['ffmpeg_options'])

    timestamp = local_queue['time_elapsed']
    local_queue['vc_obj'].play(discord.FFmpegPCMAudio(source=local_queue['song_list'][local_queue['current']]['url'], options=options +
f" -vn -ss {timestamp}"))


async def start_song_loop(self, ctx):
    local_queue = self.bot.global_queue[ctx.author.voice.channel.id]
    vc = local_queue['vc_obj']
    while not (local_queue['destroy']):

        options = parse_options(local_queue['ffmpeg_options'])

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

        while local_queue['current'] >= (len(local_queue['song_list'])):
           await asyncio.sleep(1) # Stop it from playing more songs until song count is at a normal value
           if local_queue['destroy']:
               return
    return
