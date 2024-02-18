from discord.ext import commands
from dotenv import load_dotenv
import os

load_dotenv()

from openai import OpenAI
from collections import defaultdict


class Conversation(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client
        self.openaiClient = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.conversations = defaultdict(list)
        self.gpt_model = os.environ["OPENAI_CHAT_MODEL"]

    @commands.group(name="conversation", invoke_without_command=True)
    async def conversation(self, ctx, *, args):
        async with ctx.typing():
            self.conversations[ctx.author].append({"role": "user", "content": args})

            response = self.openaiClient.chat.completions.create(
                model=self.gpt_model,
                messages=self.conversations[ctx.author],
            )
            self.conversations[ctx.author].append(
                {"role": "system", "content": response.choices[0].message.content}
            )

            return await ctx.send(response.choices[0].message.content)

    @conversation.command()
    async def clear(self, ctx):
        self.conversations[ctx.author] = []
        return await ctx.send("Conversation cleared")

    @conversation.command()
    async def history(self, ctx):
        res = list(
            map(
                lambda x: f'{x["role"]}: {x["content"]}\n',
                self.conversations[ctx.author],
            )
        )
        return await ctx.send("".join(res))


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Conversation(client))
