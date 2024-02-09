import discord
import asyncio
from discord.ext import commands
from yt_dlp import YoutubeDL


class YTDLSource(discord.PCMVolumeTransformer):
    YDL_OPTIONS = {
        "format": "bestaudio",
        "restrictfilenames": True,
        "noplaylist": True,
        "nocheckcertificate": True,
        "ignoreerrors": False,
        "logtostderr": False,
        "quiet": True,
        "no_warnings": True,
        "default_search": "auto",
        "source_address": "0.0.0.0",  # bind to ipv4 since ipv6 addresses cause issues sometimes
        "noplaylist": True,
    }

    def __init__(self, original: discord.FFmpegPCMAudio, *, volume: float = 0.5):
        super().__init__(original, volume)

    @classmethod
    async def search(cls, kw):
        with YoutubeDL(cls.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(kw, download=False)
                if "entries" in info:
                    info = info["entries"][0]
                else:
                    print("Result not found")
                    return None
            except Exception:
                print(Exception)
                return False
        return info


class Music(commands.Cog):
    def __init__(self, client):
        self.client = client

        self.is_playing = False
        self.is_paused = False

        self.queue = []
        self.history = []

        self.FFMPEG_OPTIONS = {
            "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
            "options": "-vn",
        }
        self.vc = None

    def is_in_vc(self, ctx):
        return ctx.message.author.voice == True

    @commands.command(name="join", help="Ask bot to join voice channel manually")
    async def join(self, ctx):
        if self.is_in_vc:
            channel = ctx.message.author.voice.channel
            return await channel.connect()
        else:
            return await ctx.send(
                "Please connect to a voice a channel to use this command"
            )

    @commands.command(name="play", help="play a song")
    async def play(self, ctx, *, args):
        sv = ctx.message.guild
        self.vc = sv.voice_client
        async with ctx.typing():
            file = await YTDLSource.search(kw=args)

            self.vc.play(
                discord.FFmpegPCMAudio(
                    source=file["url"],
                )
            )
        await ctx.send(f"Now playing {file['title']}")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Music(client))
