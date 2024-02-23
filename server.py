import discord
from discord.ext import commands
import time
import platform
import asyncio
import os
import logging
from dotenv import load_dotenv

load_dotenv(override=True)

logging.Formatter.converter = time.gmtime
format = "%(asctime)s.%(msecs)03dZ %(threadName)s\
 %(levelname)s:%(name)s:%(message)s"

formatter = logging.basicConfig(
    format=format,
    datefmt="%Y-%m-%dT%H:%M:%S",
    level=logging.INFO,
)


class Client(commands.Bot):
    def __init__(self):
        super().__init__(
            command_prefix=commands.when_mentioned_or("."),
            intents=discord.Intents().all(),
        )

    async def setup_hook(self):
        for filename in os.listdir("./cogs"):
            if filename.endswith(".py"):
                await client.load_extension(f"cogs.{filename[:-3]}")
                logging.info(f"Loaded Cog:{filename[:-3]}")
            else:
                logging.info("Unable to load pycache folder.")

    async def on_ready(self):
        logging.info(" Logged sin as " + self.user.name)
        logging.info(" Bot ID " + str(self.user.id))
        logging.info(" Discord Version " + discord.__version__)
        logging.info(" Python Version " + str(platform.python_version()))
        synced = await self.tree.sync()
        logging.info(" Slash CMDs Synced " + str(len(synced)) + " Commands")


DISCORD_BOT_TOKEN = os.environ["DISCORD_BOT_TOKEN"]
client = Client()


async def run():
    async with client:
        await client.start(
            DISCORD_BOT_TOKEN, reconnect=True
        )  # Start client and allow for reconnecting


try:
    client = Client()  # Create instance of client
    asyncio.run(run())  # Run main method

except Exception as error:
    print("Script Ending")  # Error handling
    raise (error)
