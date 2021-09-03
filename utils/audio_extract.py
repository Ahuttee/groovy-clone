# Gets song information
import youtube_dl

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
                "duration": f"{info_dict['duration']//60}:{info_dict['duration']%60}",
                "url":  info_dict['url']
            }

    return useful_info
    
