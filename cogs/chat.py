from discord.ext import commands
from discord import File
from dotenv import load_dotenv
from collections import defaultdict

import discord
import os

load_dotenv()

from openai import OpenAI

from PIL import Image
import requests
import pytesseract

# TODO: Add langchain to let users decide the prompt of the answer
# FIXME: Fix path to return txt file when response > 4000 length when run the bot using Docker


class Chat(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        # self.openai_client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        # self.gpt_model = os.environ["OPENAI_CHAT_MODEL"]

        self.openai_client = {}
        self.gpt_model = {}
        self.conversations = {}

    @commands.Cog.listener()
    async def on_ready(self):
        for guild in self.client.guilds:
            id = int(guild.id)
            self.openai_client[id] = None
            self.gpt_model[id] = None
            self.conversations[id] = defaultdict(list)

    async def is_bot_set_up(self, ctx):
        id = int(ctx.guild.id)
        if self.openai_client[id] == None:
            error_embed = self.create_embed(
                ctx, "Error", "Bot is not setup. Please use `.setup` to setup the bot"
            )
            await ctx.send(embed=error_embed)
            return False
        else:
            return True

    # generate embed message
    def create_embed(self, ctx, title, msg):
        msg_embed = discord.Embed(title=title, description=msg)
        return msg_embed

    @commands.group(
        name="setup", invoke_without_command=True, help="Activate server's API key"
    )
    async def setup(self, ctx: commands.Context):
        id = int(ctx.guild.id)

        def check(message):
            return message.author.id == ctx.author.id

        await ctx.send("Enter your OPENAI_API_KEY")

        user_msg = await self.client.wait_for("message", check=check)

        api_key = user_msg.content

        async with ctx.typing():
            try:
                self.openai_client[id] = OpenAI(api_key=api_key)
                self.gpt_model[id] = "gpt-3.5-turbo-0125"
                # test request with given apikey
                self.openai_client[id].chat.completions.create(
                    model=self.gpt_model[id],
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant designed to output JSON.",
                        },
                        {
                            "role": "user",
                            "content": "Who won the world series in 2020?",
                        },
                    ],
                )
                succesful_embed = self.create_embed(
                    ctx,
                    "Succesfull",
                    "Valid OPENAI API KEY\nDefault chat model: gpt-3.5-turbo-0125\nYou can change it later by .setup chat_model <model>",
                )

                await ctx.send(embed=succesful_embed)

            except Exception as e:
                print("@Chat.setup", e)
                error_embed = self.create_embed(
                    ctx, "Error", "Invalid API Key. Please try another key"
                )
                await ctx.send(embed=error_embed)

    @setup.command(name="chat_model", help="Change chat model of OPENAI API")
    async def chat_model(self, ctx, model):
        # precheck if bot is setup
        is_set_up = await self.is_bot_set_up(ctx)
        if not is_set_up:
            return
        id = ctx.guild.id
        async with ctx.typing():
            try:
                self.gpt_model[id] = model
                self.openai_client[id].chat.completions.create(
                    model=self.gpt_model[id],
                    response_format={"type": "json_object"},
                    messages=[
                        {
                            "role": "system",
                            "content": "You are a helpful assistant designed to output JSON.",
                        },
                        {
                            "role": "user",
                            "content": "Who won the world series in 2020?",
                        },
                    ],
                )
                success_embed = self.create_embed(
                    ctx, "Succesfull", f"Successfully update ChatGpt Model to: {model}"
                )
                return await ctx.send(embed=success_embed)

            except Exception as e:
                print("@Chat.setup.chat_model", e)
                error_embed = self.create_embed(
                    ctx,
                    "Error",
                    "Invalid model. Please use another one. More information on https://platform.openai.com/docs/models",
                )
                await ctx.send(embed=error_embed)

    async def answer(self, ctx, response):
        if len(response.choices[0].message.content) < 2000:
            return await ctx.send(response.choices[0].message.content)
        else:
            with open(f"./chatResponses/{ctx.author}.txt", "w") as file:
                file.write(response.choices[0].message.content)
            await ctx.send(
                "Answer is in the txt file",
                file=File(f"./chatResponses/{ctx.author}.txt"),
            )

    def generate_response(self, id, client, model, messages):
        response = client.chat.completions.create(
            model=self.gpt_model[id],
            messages=messages,
        )

        return response

    @commands.group(name="chat", invoke_without_command=True)
    async def chat(self, ctx, *, args):
        # precheck if bot is setup
        is_set_up = await self.is_bot_set_up(ctx)
        if not is_set_up:
            return

        id = int(ctx.guild.id)
        async with ctx.typing():
            response = self.generate_response(
                id,
                self.openai_client[id],
                self.gpt_model[id],
                [{"role": "user", "content": args}],
            )
            # if response length > limit of discord's message, send result through txt file
            return await self.answer(ctx, response)

    @chat.command(name="image")
    async def single_chat_image_chat(self, ctx, *, args=None):
        # precheck if bot is setup
        is_set_up = await self.is_bot_set_up(ctx)
        if not is_set_up:
            return

        id = int(ctx.guild.id)
        pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_PATH"]
        image_url = ctx.message.attachments[0].url

        r = requests.get(image_url, stream=True)

        image = Image.open(r.raw)
        text = pytesseract.image_to_string(image)
        if args is not None:
            text = args + "\n" + '"' + text + '"'

        async with ctx.typing():
            response = self.generate_response(
                id,
                self.openai_client[id],
                self.gpt_model[id],
                [{"role": "user", "content": text}],
            )

            # if response length > limit of discord's message, send result through txt file
            return await self.answer(ctx, response)

    # Conversation
    @commands.group(name="conversation", invoke_without_command=True)
    async def conversation(self, ctx, *, args):
        is_set_up = await self.is_bot_set_up(ctx)
        if not is_set_up:
            return
        id = int(ctx.guild.id)

        async with ctx.typing():
            self.conversations[id][ctx.author].append({"role": "user", "content": args})

            response = self.generate_response(
                id,
                self.openai_client[id],
                self.gpt_model[id],
                self.conversations[id][ctx.author],
            )

            self.conversations[id][ctx.author].append(
                {"role": "system", "content": response.choices[0].message.content}
            )

            # if response length > limit of discord's message, send result through txt file
            return await self.answer(ctx, response)

    @conversation.command()
    async def clear(self, ctx):
        async with ctx.typing():
            id = int(ctx.guild.id)
            self.conversations[id][ctx.author] = []
            return await ctx.send("Conversation cleared")

    @conversation.command()
    async def history(self, ctx):
        async with ctx.typing():
            id = int(ctx.guild.id)
            if len(self.conversations[id][ctx.author]) == 0:
                return await ctx.send("No chat to show")
            res = list(
                map(
                    lambda x: f'{x["role"]}: {x["content"]}\n',
                    self.conversations[id][ctx.author],
                )
            )
            return await ctx.send("".join(res))

    @conversation.command(name="image")
    async def conversation_image_chat(self, ctx, *, args=None):
        is_set_up = await self.is_bot_set_up(ctx)
        if not is_set_up:
            return
        id = int(ctx.guild.id)
        pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_PATH"]
        image_url = ctx.message.attachments[0].url

        r = requests.get(image_url, stream=True)

        image = Image.open(r.raw)
        text = pytesseract.image_to_string(image)
        if args is not None:
            text = args + "\n" + '"' + text + '"'

        self.conversations[id][ctx.author].append({"role": "user", "content": text})

        async with ctx.typing():
            response = self.generate_response(
                id,
                self.openai_client[id],
                self.gpt_model[id],
                self.conversations[id][ctx.author],
            )

            self.conversations[id][ctx.author].append(
                {"role": "system", "content": response.choices[0].message.content}
            )
            # if response length > limit of discord's message, send result through txt file
            return await self.answer(ctx, response)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Chat(client))
