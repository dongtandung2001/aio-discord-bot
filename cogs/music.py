import discord
import datetime

from asyncio import run_coroutine_threadsafe
from discord.ext import commands
from yt_dlp import YoutubeDL
from collections import defaultdict


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, original: discord.FFmpegPCMAudio, *, info, volume: float = 0.5):
        super().__init__(original, volume)
        self.info = info
        self.url = info.get("original_url")
        self.title = info.get("title")
        self.thumbnail = info.get("thumbnail")

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
        "source_address": "0.0.0.0",
        "noplaylist": True,
    }

    FFMPEG_OPTIONS = {
        "before_options": "-reconnect 1 -reconnect_streamed 1 -reconnect_delay_max 5",
        "options": "-vn",
    }

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
        self.vc = defaultdict(discord.VoiceClient)

        self.queue = {}
        self.history = {}

    @commands.Cog.listener()
    async def on_ready(self):
        # make voiceClient / Bot unique in each guild
        # self.vc[id] = voiceClient of guild with guildID = id
        # self.queue[id] = queue of songs of guild with guildID = id
        # self.history[id] = history of songs of guild with guildID = id
        for guild in self.client.guilds:
            id = int(guild.id)
            self.queue[id] = []
            self.history[id] = []
            self.vc[id] = None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is not None and after.channel is None:
            # User left the voice channel
            print(f"{member.name} has stopped playing audio")
        elif before.channel is None and after.channel is not None:
            # User joined the voice channel
            print(f"{member.name} has started playing audio")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            return
        print("[" + datetime.time.now() + "] " + str(error))
        await ctx.send(embed=self.errorEmbedGen(error))

    def errorEmbed(self, error):
        embed = discord.Embed(
            title="Error",
            description="There was an error occur. Restart needed! \n\nError:\n**`"
            + str(error)
            + "`**",
        )
        return embed

    def create_embed(self, ctx, song: YTDLSource, embedType):
        # get embeded's information
        title = song.title
        url = song.url
        thumbnail = song.thumbnail
        author = ctx.author
        avatar = author.avatar

        # now playing embed
        if embedType == 1:
            now_playing_embed = discord.Embed(
                title="Now Playing", description=f"[{title}]({url})"
            )

            now_playing_embed.set_thumbnail(url=thumbnail)
            now_playing_embed.set_footer(text=f"Requested by {author}", icon_url=avatar)
            return now_playing_embed
        # add to queue embed
        elif embedType == 2:
            queue_embed = discord.Embed()
            return queue_embed
        # information/general message embed
        elif embedType == 3:
            msg_embed = discord.Embed()
            return msg_embed

    # Wrapper Function: check if user is in voice channel
    def is_user_in_vc():
        async def is_in(ctx):
            if ctx.message.author.voice is None:
                await ctx.send("Please join a voice channel to use this command!")
                return False
            return True

        return commands.check(is_in)

    def connect_to_voice_channel(self, ctx):
        pass

    async def join_helper(self, ctx, channel):
        id = int(ctx.guild.id)
        # if there is no voiceClient init yet --> connect
        # or if there is voiceClient but it's not conncted --> connect
        if self.vc[id] == None or not self.vc[id].is_connected():
            # connect
            self.vc[id] = await channel.connect()

            # cannot find voiceClient
            if self.vc[id] == None:
                return await ctx.send("Could not connect to the voice channel")
            else:
                # connect successfully
                return await ctx.send(f"Bot has joined `{channel}`")
        else:
            # the bot is already join
            return await ctx.send(f"Bot is already joined `{channel}`")

    @commands.command(name="join", help="Join voice channel manually")
    @is_user_in_vc()
    async def join(self, ctx: commands.Context):
        channel = ctx.message.author.voice.channel
        return await self.join_helper(ctx, channel)

    @commands.command(name="play", help="Play the most relevant track on Yotube ")
    @is_user_in_vc()
    async def play(self, ctx, *, args):
        try:
            channel = ctx.message.author.voice.channel
            await self.join_helper(ctx, channel)
        except Exception as e:
            print(f"Music.play1: {e}")

        try:
            id = int(ctx.guild.id)
            server = ctx.message.guild
            self.vc[id] = server.voice_client
            async with ctx.typing():
                source = await YTDLSource.search(kw=args)

                if source is None:
                    return await ctx.send("Result not found with the give url/keyword")
                elif not source:
                    return await ctx.send("Internal Error")
                else:
                    if self.vc[id].is_playing():
                        await ctx.send(f"Added {source.title} to the queue")
                        self.queue[id].append(source)
                    else:
                        self.history[id].append(source)
                        self.vc[id].play(
                            source,
                            after=lambda e: self.play_next_in_queue(ctx, id=id),
                        )
                        now_playing_embed = self.create_embed(ctx, source, 1)
                        return await ctx.send(embed=now_playing_embed)
        except Exception as e:
            await ctx.send("An error occurred while playing the track.")
            print(f"Music.play2: {e}")

    def play_next_in_queue(self, ctx, id, error=None):
        if error:
            print("play_next_in_queue: ", error)
            return
        # other audio source is being played
        if self.vc[id].is_playing():
            return
        if len(self.queue[id]) == 0:
            # async task that cant await here
            co_routine = ctx.send("No more song in queue")
            task = run_coroutine_threadsafe(co_routine, self.client.loop)
            try:
                task
            except Exception as e:
                print("Music.play_next_in_queue1:", e)

        else:
            self.history[id].append(self.queue[id].pop(0))
            source = self.history[id][-1]

            self.vc[id].play(source, after=lambda e: self.play_next_in_queue(ctx, id))

            # async task that cant await here
            now_playing_embed = self.create_embed(ctx, source, 1)
            co_routine = ctx.send(embed=now_playing_embed)
            task = run_coroutine_threadsafe(co_routine, self.client.loop)
            try:
                task
            except Exception as e:
                print("Music.play_next_in_queue2:", e)
            return

    @commands.command(name="pause", help="Stop music")
    @is_user_in_vc()
    async def pause(self, ctx):
        id = int(ctx.guild.id)
        try:
            if self.vc[id].is_playing():
                self.vc[id].pause()
            else:
                ctx.send("The bot is not playing anything!")
        except Exception as e:
            print(f"Music.pause: {e}")

    @commands.command(name="resume", help="Resume the audio")
    @is_user_in_vc()
    async def resume(self, ctx):
        id = int(ctx.guild.id)
        try:
            if self.vc[id].is_paused():
                self.vc[id].resume()
        except Exception as e:
            print(f"Music.resume: {e}")

    @commands.command(name="stop", help="Stop the current audio source")
    @is_user_in_vc()
    async def stop(self, ctx):
        id = int(ctx.guild.id)
        try:
            if self.vc[id].is_playing():
                self.vc[id].stop()
        except Exception as e:
            print(f"Music.skip: {e}")

    @commands.command(name="disconnect", help="Disconnect bot from voice channel")
    async def disconnect(self, ctx):
        id = int(ctx.guild.id)
        if self.vc[id] != None:
            self.queue[id] = []
            self.history[id] = []
            await ctx.send("Bot disconnected from voice channel. Queue cleared!")
            await self.vc[id].disconnect()


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Music(client))
