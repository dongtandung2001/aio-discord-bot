from collections import defaultdict

from discord.ext import commands

from dotenv import load_dotenv
import os
load_dotenv()

from openai import OpenAI

from PIL import Image
import requests
import pytesseract
import uuid
class Ask(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.openaiClient = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        self.gpt_model = "gpt-3.5-turbo" 

    @commands.group(name='ask', invoke_without_command=True)
    async def ask(self, ctx, *, args):
        await ctx.typing()
        response = self.openaiClient.chat.completions.create(
            model = self.gpt_model,
            messages= [{"role": "user", "content": args}],
            max_tokens=512
        )
        await ctx.send(response.choices[0].message.content)
    
    @ask.command()
    async def image(self, ctx):
        pytesseract.pytesseract.tesseract_cmd = os.environ['TESSERACT_PATH']
        image_url = ctx.message.attachments[0].url
        
        r = requests.get(image_url, stream=True)

        image = Image.open(r.raw)
        text = pytesseract.image_to_string(image)

        await ctx.typing()
        response = self.openaiClient.chat.completions.create(
            model = self.gpt_model,
            messages= [{"role": "user", "content": text}],
            max_tokens=512
        )
        await ctx.send(response.choices[0].message.content)

    
async def setup(client:commands.Bot) -> None:
    await client.add_cog(Ask(client)) 