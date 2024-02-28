import discord
import datetime
import logging
import json

from asyncio import run_coroutine_threadsafe
from discord.ext import commands
from yt_dlp import YoutubeDL

# to implement
# 1. search feature
# 2. show history of tracks
# 3. shuffle queue
# 4. re-create history and play it (shuffle option available)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, original: discord.FFmpegPCMAudio, *, info, volume: float = 0.5):
        super().__init__(original, volume)
        self.info = info
        self.playable_url = info.get("url")
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
    async def search_and_create_source(cls, kw):
        with YoutubeDL(cls.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info("ytsearch:%s" % kw, download=False)
                if "entries" in info:
                    info = info["entries"][0]

                else:
                    logging.error(
                        "@YTDLSource.search_and_create_source: Result not found with the give url/keyword"
                    )
                    return None
            except Exception:
                logging.error("@YTDLSource.search_and_create_source", Exception)
                return False
        return cls(discord.FFmpegPCMAudio(info["url"], **cls.FFMPEG_OPTIONS), info=info)

    @classmethod
    async def search_yt(cls, kw, number_of_result):
        with YoutubeDL(cls.YDL_OPTIONS) as ydl:
            try:
                info = ydl.extract_info(
                    f"ytsearch{number_of_result}:{kw}", download=False
                )
                if "entries" in info:
                    info = info["entries"]
                    return info
                else:
                    logging.error(
                        "@YTDLSource.search_and_create_source: Result not found with the give url/keyword"
                    )
                    return None
            except Exception:
                logging.error("@YTDLSource.search_and_create_source", Exception)
                return False

    @classmethod
    async def create_source(cls, info):
        return cls(discord.FFmpegPCMAudio(info["url"], **cls.FFMPEG_OPTIONS), info=info)


class Music(commands.Cog):
    def __init__(self, client):
        self.client = client
        self.vc = {}

        self.queue = {}
        self.history = {}
        self.replay = {}

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
            self.replay[id] = False
            self.vc[id] = None

    @commands.Cog.listener()
    async def on_voice_state_update(self, member, before, after):
        if before.channel is not None and after.channel is None:
            # User left the voice channel
            logging.info(f"{member.name} has stopped playing audio")
        elif before.channel is None and after.channel is not None:
            # User joined the voice channel
            logging.info(f"{member.name} has started playing audio")

    @commands.Cog.listener()
    async def on_command_error(self, ctx, error):
        if isinstance(error, commands.CommandError):
            logging.info("[" + str(datetime.datetime.now().time()) + "] " + str(error))
            return await ctx.send(embed=self.errorEmbed(error))

    def errorEmbed(self, error):
        embed = discord.Embed(title="Error", description=f"{str(error)}")

        return embed

    def create_embed(self, ctx, song: YTDLSource, embedType, msg=""):
        # get embeded's information
        if song:
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
            queue_embed = discord.Embed(
                title="Add to queue", description=f"[{title}]({url})"
            )
            queue_embed.set_thumbnail(url=thumbnail)
            queue_embed.set_footer(text=f"Requested by {author}", icon_url=avatar)
            return queue_embed
        # information/general message embed
        elif embedType == 3:
            msg_embed = discord.Embed(title="Information", description=msg)
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
            # Already connected
            return

    @commands.command(name="join", help="Join voice channel manually")
    @is_user_in_vc()
    async def join(self, ctx: commands.Context):
        channel = ctx.message.author.voice.channel
        return await self.join_helper(ctx, channel)

    async def play_or_add_to_queue(self, ctx, source, id):
        if self.vc[id].is_playing():
            queue_embed = self.create_embed(ctx, source, 2)
            await ctx.send(embed=queue_embed)
            self.queue[id].append(source)
        else:
            self.history[id].append(source)
            self.vc[id].play(
                source,
                after=lambda e: self.play_next_in_queue(ctx, id=id),
            )
            now_playing_embed = self.create_embed(ctx, source, 1)
            return await ctx.send(embed=now_playing_embed)

    @commands.command(name="play", help="Play the most relevant track on Yotube ")
    @is_user_in_vc()
    async def play(self, ctx, *, args):
        try:
            channel = ctx.message.author.voice.channel
            await self.join_helper(ctx, channel)
        except Exception as e:
            logging.error(f"Music.play1: {e}")

        try:
            id = int(ctx.guild.id)
            server = ctx.message.guild
            self.vc[id] = server.voice_client
            async with ctx.typing():
                source = await YTDLSource.search_and_create_source(kw=args)

                if source is None:
                    return await ctx.send("Result not found with the give url/keyword")
                elif not source:
                    return await ctx.send("Internal Error")
                else:
                    return await self.play_or_add_to_queue(ctx, source, id)
        except Exception as e:
            await ctx.send("An error occurred while playing the track.")
            logging.error(f"Music.play2: {e}")

    @commands.command(
        "search", help="Search tracks on youtube and pick one to add to queue/play"
    )
    @is_user_in_vc()
    async def search(self, ctx, *, kw):
        id = int(ctx.guild.id)
        channel = ctx.message.author.voice.channel
        await self.join_helper(ctx, channel)
        async with ctx.typing():
            results = await YTDLSource.search_yt(kw, 5)
            result_titles = [
                f'`{i + 1}. {result["title"]}`' for i, result in enumerate(results)
            ]

            await ctx.send("Which one?\n" + "\n".join(result_titles))

            # check if the user who is replying is the same as the user use command
            def check(message):
                return message.author.id == ctx.author.id

            user_msg = await self.client.wait_for("message", check=check)
            await ctx.send(f"You picked {user_msg.content}")

            chosen_track = results[int(user_msg.content) - 1]
            source = await YTDLSource.create_source(info=chosen_track)

            # play or add to queue
            return await self.play_or_add_to_queue(ctx, source, id)

    def play_next_in_queue(self, ctx, id, error=None):
        if error:
            logging.error("play_next_in_queue: ", error)
            return
        # other audio source is being played
        if self.vc[id].is_playing():
            logging.info("Audio is being played")
            return

        # check if replay option is on:
        if self.replay[id]:
            # check if there is something in the history to replay
            if len(self.history[id]) > 0:
                # get the source to replay
                replay_source = self.history[id][-1]

                # create new source with the same info to play
                # old source cannot put in here to replay
                source = YTDLSource(
                    discord.FFmpegPCMAudio(
                        replay_source.playable_url, **YTDLSource.FFMPEG_OPTIONS
                    ),
                    info=replay_source.info,
                )
                self.vc[id].play(
                    source, after=lambda e: self.play_next_in_queue(ctx, id)
                )
                return
        else:
            # check if there is anything in queue to play_next
            if len(self.queue[id]) == 0:
                # async task that cant await here
                msg_embed = self.create_embed(
                    ctx, None, 3, "No more song in queue to play"
                )
                co_routine = ctx.send(embed=msg_embed)
                task = run_coroutine_threadsafe(co_routine, self.client.loop)
                try:
                    task
                except Exception as e:
                    logging.error("Music.play_next_in_queue1:", e)

            else:
                # get the next in queue
                self.history[id].append(self.queue[id].pop(0))
                source = self.history[id][-1]

                # play audio source
                self.vc[id].play(
                    source, after=lambda e: self.play_next_in_queue(ctx, id)
                )

                # async task that cant await here
                now_playing_embed = self.create_embed(ctx, source, 1)
                co_routine = ctx.send(embed=now_playing_embed)
                task = run_coroutine_threadsafe(co_routine, self.client.loop)
                try:
                    task
                except Exception as e:
                    logging.error("Music.play_next_in_queue2:", e)
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
            logging.error(f"Music.pause: {e}")

    @commands.command(name="resume", help="Resume the audio")
    @is_user_in_vc()
    async def resume(self, ctx):
        id = int(ctx.guild.id)
        try:
            if self.vc[id].is_paused():
                self.vc[id].resume()
        except Exception as e:
            logging.error(f"Music.resume: {e}")

    @commands.command(name="stop", help="Stop the current audio source")
    @is_user_in_vc()
    async def stop(self, ctx):
        id = int(ctx.guild.id)
        try:
            if self.vc[id] and self.vc[id].is_playing():
                # clear queue
                self.queue[id] = []
                self.history[id] = []
                # stop audio
                self.vc[id].stop()
                # disconnect bot
                await self.vc[id].disconnect()

                stop_msg_embed = self.create_embed(
                    ctx, None, 3, "Bot stopped. Clearing queue..."
                )
                await ctx.send(embed=stop_msg_embed)
        except Exception as e:
            logging.error(f"Music.stop: {e}")

    @commands.command(
        name="skip", help="Skip the current playing track, play the next track in queue"
    )
    @is_user_in_vc()
    async def skip(self, ctx):
        id = int(ctx.guild.id)
        try:
            if self.vc[id].is_playing():
                self.vc[id].pause()
                self.vc[id].stop()
                skip_msg_embed = self.create_embed(
                    ctx, None, 3, "Track skipped successfully"
                )
                return await ctx.send(embed=skip_msg_embed)
        except Exception as e:
            logging.error(f"Music.skip:", e)

    @commands.command(
        name="replay",
        help="Turn on replay mode: replay the current track\
                Use it again to turn it off",
    )
    @is_user_in_vc()
    async def replay(self, ctx):
        id = int(ctx.guild.id)
        self.replay[id] = not self.replay[id]
        # On
        if self.replay[id]:
            replay_msg = self.create_embed(ctx, None, 3, "Replay: On")
            await ctx.send(embed=replay_msg)
        else:
            replay_msg = self.create_embed(ctx, None, 3, "Replay: Off")
            await ctx.send(embed=replay_msg)

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
