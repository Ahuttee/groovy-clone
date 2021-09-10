import youtube_dl
import discord

async def check_user_vc(bot, ctx):  #Check if user is in a vc & if that vc contains a queue
    if ctx.author.voice == None:
        await ctx.send("You're not in a vc")
        return True
    if ctx.author.voice.channel.id not in bot.global_queue:
        await ctx.send("This vc does not contain a queue")
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

def search(query, bilibili=False):
    ytdl_options = {
    "noplaylist": True,
    "format": "bestaudio",
    "quiet": True
        }

    if bilibili:
        del ytdl_options['format']
    with youtube_dl.YoutubeDL(ytdl_options) as ytdl:
        if bilibili:
            info_dict = ytdl.extract_info(query, download=False)
        else:
            info_dict = ytdl.extract_info(f"ytsearch:{query}", download=False)['entries'][0]

    useful_info = {
                "title": info_dict['title'],
                "url":  info_dict['url'],
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

