from collections import defaultdict

from discord.ext import commands

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
        self.gpt_model = "gpt-3.5-turbo"

    @commands.group(name="chat", invoke_without_command=True)
    async def chat(self, ctx, *, args):
        async with ctx.typing():
            response = self.openaiClient.chat.completions.create(
                model=self.gpt_model,
                messages=[{"role": "user", "content": args}],
            )
            return await ctx.send(response.choices[0].message.content[0:3900])

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
