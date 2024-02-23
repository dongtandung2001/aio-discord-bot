from discord.ext import commands
from discord import File

from dotenv import load_dotenv
import os

load_dotenv()

from openai import OpenAI

from PIL import Image
import requests
import pytesseract


class Chat(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.openaiClient = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.gpt_model = os.environ["OPENAI_CHAT_MODEL"]

    @commands.Cog.listener()
    async def on_ready(self):
        print("Using GPT Model: ", self.gpt_model)

    @commands.group(name="chat", invoke_without_command=True)
    async def chat(self, ctx, *, args):
        async with ctx.typing():
            response = self.openaiClient.chat.completions.create(
                model=self.gpt_model,
                messages=[{"role": "user", "content": args}],
            )
            if len(response.choices[0].message.content) < 2000:
                return await ctx.send(response.choices[0].message.content[0:3900])
            else:
                with open("response.txt", "w") as file:
                    file.write(response.choices[0].message.content)
                return await ctx.send(
                    "Answer is in the txt file", file=File("./response.txt")
                )

    @chat.command()
    async def image(self, ctx):
        pytesseract.pytesseract.tesseract_cmd = os.environ["TESSERACT_PATH"]
        image_url = ctx.message.attachments[0].url

        r = requests.get(image_url, stream=True)

        image = Image.open(r.raw)
        text = pytesseract.image_to_string(image)

        async with ctx.typing():
            response = self.openaiClient.chat.completions.create(
                model=self.gpt_model,
                messages=[{"role": "user", "content": text}],
            )
            return await ctx.send(response.choices[0].message.content)


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Chat(client))
