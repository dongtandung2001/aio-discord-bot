from discord.ext import commands
from dotenv import load_dotenv
import os
load_dotenv()

from openai import OpenAI
from collections import defaultdict

class Ask(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.openaiClient = OpenAI(api_key=os.environ['OPENAI_API_KEY'])
        self.gpt_model = "gpt-3.5-turbo" 

    @commands.command()
    async def ask(self, ctx, *, args):
        await ctx.typing()
        response = self.openaiClient.chat.completions.create(
            model = self.gpt_model,
            messages= [{"role": "user", "content": args}],
            max_tokens=512
        )

        await ctx.send(response.choices[0].message.content)

    
async def setup(client:commands.Bot) -> None:
    await client.add_cog(Ask(client)) 