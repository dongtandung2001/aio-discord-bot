import discord
from discord.ext import commands
from discord import File
from dotenv import load_dotenv
from collections import defaultdict

import os
import io
import logging
import sqlite3

load_dotenv()

from openai import OpenAI as openai

from PIL import Image
import requests
import pytesseract

from PyPDF2 import PdfReader
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains.question_answering import load_qa_chain
from langchain.prompts import PromptTemplate
from langchain_community.vectorstores.chroma import Chroma
from langchain_openai import OpenAI
from langchain_openai import OpenAIEmbeddings
from chromadb import PersistentClient


class Chat(commands.Cog):
    def __init__(self, client: commands.Bot):
        self.client = client

        self.openai_client = {}
        self.gpt_model = {}
        self.conversations = {}

        # Create folder for chat response > 4000 words (limit by Discord.py text channel)
        directory_name = "chatResponses"
        os.makedirs(directory_name, exist_ok=True)

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

    """
    Setup chat bot
    """

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
                self.openai_client[id] = openai(api_key=api_key)
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

    """
    Update/Modify chat model
    """

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

    """
    Send response to text channel
    """

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

    """
    Generate response by making api call to OPENAI API
    """

    def generate_response(self, client, model, messages):
        response = client.chat.completions.create(
            model=model,
            messages=messages,
        )

        return response

    """
    Single chat
    """

    @commands.group(
        name="chat", invoke_without_command=True, help="Single chat with the bot"
    )
    async def chat(self, ctx, *, args: str = commands.parameter(description="Test")):
        # precheck if bot is setup
        is_set_up = await self.is_bot_set_up(ctx)
        if not is_set_up:
            return

        id = int(ctx.guild.id)
        async with ctx.typing():
            response = self.generate_response(
                self.openai_client[id],
                self.gpt_model[id],
                [{"role": "user", "content": args}],
            )
            # if response length > limit of discord's message, send result through txt file
            return await self.answer(ctx, response)

    """
    Single image chat
    """

    @chat.command(
        name="image",
        help=f"pic-to-text and ask the bot (plain text image only)",
    )
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
                self.openai_client[id],
                self.gpt_model[id],
                [{"role": "user", "content": text}],
            )

            # if response length > limit of discord's message, send result through txt file
            return await self.answer(ctx, response)

    """
    Conversation Chat
    """

    # Conversation
    @commands.group(
        name="conversation",
        invoke_without_command=True,
        help="Conversation chat with bot",
    )
    async def conversation(self, ctx, *, args):
        is_set_up = await self.is_bot_set_up(ctx)
        if not is_set_up:
            return
        id = int(ctx.guild.id)

        async with ctx.typing():
            self.conversations[id][ctx.author].append({"role": "user", "content": args})

            response = self.generate_response(
                self.openai_client[id],
                self.gpt_model[id],
                self.conversations[id][ctx.author],
            )

            self.conversations[id][ctx.author].append(
                {"role": "system", "content": response.choices[0].message.content}
            )

            # if response length > limit of discord's message, send result through txt file
            return await self.answer(ctx, response)

    """
    Clear conversation history/memory
    """

    @conversation.command(help="Clear conversation memory")
    async def clear(self, ctx):
        async with ctx.typing():
            id = int(ctx.guild.id)
            self.conversations[id][ctx.author] = []
            return await ctx.send("Conversation cleared")

    """
    Conversation history
    """

    @conversation.command(help="Show history of conversation")
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

    """
    Conversation chat with image
    """

    @conversation.command(
        name="image",
        help="pic-to-text and ask the bot (plain text image only)",
    )
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
                self.openai_client[id],
                self.gpt_model[id],
                self.conversations[id][ctx.author],
            )

            self.conversations[id][ctx.author].append(
                {"role": "system", "content": response.choices[0].message.content}
            )
            # if response length > limit of discord's message, send result through txt file
            return await self.answer(ctx, response)

    """
    Chat With PDF
    """

    # chat with pdf
    @commands.group(name="pdf", invoke_without_command=True, help="Chat with PDF")
    async def pdf(self, ctx, *, arg=None):
        id = int(ctx.guild.id)
        is_set_up = await self.is_bot_set_up(ctx)
        if not is_set_up:
            return

        if not arg:
            return await ctx.send(
                "Please provide a args: .pdf <Filename ref> <question>"
            )
        args = arg.split()
        collection = args[0]
        question = " ".join(args[1:])
        response = self.get_answer(question=question, id=id, collection=collection)

        if response["status"] == 200:
            return await ctx.send(response["data"]["output_text"])
        else:
            return await ctx.send(response["msg"])

    """
    Upload pdf to server and process
    """

    # TODO: file hanlding ==> make sure its pdf
    @pdf.command(name="upload", help="Upload pdf file")
    async def pdf_upload(self, ctx, *, arg=None):
        is_set_up = await self.is_bot_set_up(ctx)
        if not is_set_up:
            return

        id = int(ctx.guild.id)
        if not ctx.message.attachments:
            return await ctx.send("No attachments found")

        if not arg:
            return await ctx.send(
                "Please specify a name for this PDF in order to search/query it later."
            )

        # let user chat with 1 pdf at a time for now
        # update multiple pdf files later
        if len(ctx.message.attachments) > 1:
            await ctx.send("Please attach only 1 file at a time")

        # name ref must be 1 word
        collection = arg.split()
        if len(collection) > 1:
            return await ctx.send("Filename reference must be 1 word")

        collection = collection[0]
        if not collection.isalnum or collection[0].isdigit():
            return await ctx.send(
                "Filename reference cant contain special characters, and it cant start with number"
            )

        await ctx.send("Processing...")
        try:
            # Get PDF object to process
            pdf_url = ctx.message.attachments[0].url
            r = requests.get(pdf_url, stream=True)
            pdf_binary = io.BytesIO(r.content)

            # Raw text
            raw_text = self.get_pdf_text(pdf_binary)
            # Text chunks
            text_chunks = self.get_text_chunks(raw_text)
            # Embedding
            self.store_vector(text_chunks, collection, id)

            await ctx.send(
                f"Upload successfully. Please refer to {arg} to chat with your document"
            )
        except Exception as e:
            logging.error("Fail to upload pdf", e)
            await ctx.send("Fail to upload/process. Please try again")

    """
    Functions for storing pdf file to chromadb
    """

    def get_pdf_text(self, pdf):
        text = ""

        pdf_reader = PdfReader(pdf)
        for page in pdf_reader.pages:
            text += page.extract_text()
        return text

    def get_text_chunks(self, text):
        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=10000, chunk_overlap=1000
        )

        chunks = text_splitter.split_text(text)
        return chunks

    def store_vector(self, text_chunks, collection, id):
        api_key = self.openai_client[id].api_key
        embedding = OpenAIEmbeddings(api_key=api_key)

        vector_db = Chroma.from_texts(
            text_chunks,
            embedding=embedding,
            persist_directory="./data",
            collection_name=collection,
            collection_metadata={"guild_id": id},
        )
        return vector_db

    def get_conversational_chain(self, id):
        prompt_template = """
        Answer the question as detailed as possible from the provided context, make sure to provide all the details, if the answer is not in
        provided context just say, "answer is not available in the context", don't provide the wrong answer\n\n
        Context:\n {context}?\n
        Question: \n{question}\n

        Answer:
        
        """
        api_key = self.openai_client[id].api_key
        model = OpenAI(api_key=api_key)

        prompt = PromptTemplate(
            template=prompt_template, input_variables=["context", "question"]
        )
        chain = load_qa_chain(model, chain_type="stuff", prompt=prompt)

        return chain

    def get_answer(self, question, id, collection):
        try:
            client = PersistentClient(path="./data")
            c = client.get_collection(collection)
            if c.metadata.get("guild_id") != id:
                return {"status": 401, "msg": "Filename ref not found"}
        except Exception as e:
            return {"status": 404, "msg": "Filename ref not found"}
        api_key = self.openai_client[id].api_key
        embedding = OpenAIEmbeddings(api_key=api_key)
        db = Chroma(
            persist_directory="./data",
            embedding_function=embedding,
            collection_name=collection,
            collection_metadata={"guild_id": id},
        )

        docs = db.similarity_search(question)

        chain = self.get_conversational_chain(id)

        response = chain.invoke(
            {"input_documents": docs, "question": question}, return_only_outputs=True
        )

        return {"status": 200, "data": response, "msg": "OK"}

    """
    Manage chroma collection of servers
    """

    """
    Show collection within server
    """

    @commands.group(
        name="collection",
        invoke_without_command=True,
        help="Show pdf filename ref in server",
    )
    async def collection(self, ctx):
        id = (int(ctx.guild.id),)
        con = sqlite3.connect("./data/chroma.sqlite3")
        cur = con.cursor()
        res = cur.execute(
            "SELECT c.name from collections as c \
            JOIN collection_metadata on c.id = collection_metadata.collection_id \
            WHERE collection_metadata.key = 'guild_id' AND collection_metadata.int_value = ?",
            id,
        )
        collections = "\n".join([c[0] for c in res.fetchall()])
        con.close()
        return await ctx.send(collections)

    """
    Delete collection in your server
    """

    @collection.command(name="delete")
    async def delete(self, ctx, arg):
        id = int(ctx.guild.id)
        client = PersistentClient(path="./data")
        try:
            collection = client.get_collection(name=arg)
            collection_id = str(collection.id)
            if collection.metadata["guild_id"] != id:
                return await ctx.send("Collection does not exist in your server")
            else:
                client.delete_collection(name=arg)
                # Delete metadata related to collections to free space
                con = sqlite3.connect("./data/chroma.sqlite3")
                cur = con.cursor()
                param = (str(collection_id),)
                cur.execute(
                    "DELETE FROM collection_metadata \
                    WHERE collection_id = ? \
                    ",
                    param,
                )
                con.commit()
                con.close()
                return await ctx.send("Deleted")
        except Exception as e:
            return await ctx.send("Collection does not exist in your server")


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Chat(client))
