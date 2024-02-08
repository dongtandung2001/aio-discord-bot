import discord
from discord.ext import commands

from youtube_dl import YoutubeDL

class Music(commands.Cog):
    def __init__(self, client):
        self.client = client

        self.is_playing = False
        self.is_paused = False

        self.queue = []
        self.history = []
        self.YDL_OPTIONS = {"format": "bestaudio", "noplaylist": "True"}
        self.FFMPEG_OPTIONS = {'options': '-vn'}
        self.vc = None
    
    

    def search(self, url):
        with YoutubeDL(self.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(url, download = False)
            except Exception:
                return False
        return {'source': info['formats'[0]['url']]}
    
    def play_next_in_queue(self):
        if len(self.queue) > 0:
            self.is_playing = True

            url = self.queue[0][0]['source']

            self.history = self.queue.pop(0)

            self.vc.play(discord.FFmpegPCMAudio(url, **self.FFMPEG_OPTIONS), after=lambda e: self.play_next_in_queue())
        else:
            self.is_playing = False

async def setup(client:commands.Bot) -> None:
    await client.add_cog(Music(client))