import discord
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

    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

    def __init__(self, original: discord.FFmpegPCMAudio, *, info, volume: float = 0.5):
        super().__init__(original, volume)
        self.info = info
        self.url = info.get("url")
        self.title = info.get("title")

    @classmethod
    async def search(cls, kw):
        with YoutubeDL(cls.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % kw, download=False)
                if "entries" in info:
                    info = info["entries"][0]
                else:
                    print(
                        "@YTDLSource.Search: Result not found with the give url/keyword"
                    )
                    return None

            except Exception:
                print("@YTDLSource.Search", Exception)
                return False
        return cls(discord.FFmpegPCMAudio(info["url"], **cls.FFMPEG_OPTIONS), info=info)


class Music(commands.Cog):
    def __init__(self, client):
        self.client = client

        self.is_playing = False
        self.is_paused = False
        self.is_connected = False

        self.queue = []
        self.history = []

        self.vc = None

    # Wrapper Function: check if user is in voice channel
    def is_user_in_vc():
        async def is_in(ctx):
            if ctx.message.author.voice == None:
                await ctx.send("Please join a voice channel to use this command!")
                return False
            return True

        return commands.check(is_in)

    def connect_to_voice_channel(self, ctx):
        pass

    @commands.command(name="join", help="Join voice channel manually")
    @is_user_in_vc()
    async def join(self, ctx):
        channel = ctx.message.author.voice.channel
        self.is_connected = True
        return await channel.connect()

    @commands.command(name="play", help="Play the most relevant track on Yotube ")
    @is_user_in_vc()
    async def play(self, ctx, *, args):
        if self.is_connected == False:
            channel = ctx.message.author.voice.channel
            self.is_connected = True
            await channel.connect()
        try:
            server = ctx.message.guild
            self.vc = server.voice_client
            async with ctx.typing():
                source = await YTDLSource.search(kw=args)

                if source == None:
                    return await ctx.send("Result not found with the give url/keyword")
                elif source == False:
                    return await ctx.send("Internal Error")
                else:
                    self.is_playing = True
                    self.vc.play(source)
            return await ctx.send(f"Now playing {source.title}")
        except Exception as e:
            await ctx.send("An error occurred while playing the track.")
            print(f"Music.play: {e}")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Music(client))
