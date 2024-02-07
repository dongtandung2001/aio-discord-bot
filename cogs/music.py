import discord
from discord.ext import commands

from youtube_dl import YoutubeDL

class Music(commands.Cog):
    def __init__(self, client):
        self.client = client

        self.is_playing = False
        self.is_paused = False

        self.queue = []
        self.YDL_OPTIONS = {"format": "bestaudio", "noplaylist": "True"}

        self.vc = None

    
    def search(self, args):
        
async def setup(client:commands.Bot) -> None:
    await client.add_cog(Music(client))