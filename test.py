# from yt_dlp import YoutubeDL
# import json

# item = "hanh phuc ao"
# YDL_OPTIONS = {"format": "all", "noplaylist": "True"}
# with YoutubeDL(YDL_OPTIONS) as ydl:
#     try:
#         info = ydl.extract_info(f"ytsearch3:{item}", download=False)
#         info = info["entries"]
#     except Exception:
#         print(Exception)
#     with open("info.json", "w") as file:
#         json.dump(info, file)


# # # from dotenv import load_dotenv
# # # import sys, os

# # # path = "".join(sys.path[0]) + "\.env"
# # # print(path)
# # # load_dotenv(path, override=True)

# # # print(os.environ["DISCORD_BOT_TOKEN"])


# # def positive_input(func):
# #     def wrapper(x):
# #         if x <= 0:
# #             raise ValueError("Input must be positive")
# #         return func(x)

# #     return wrapper


# # @positive_input
# # def square(x):
# #     return x**2


# # print(square(-1))

# a = "abc"
# if a is bool:
#     print(a)
# from openai import OpenAI

# client = OpenAI()

# try:
#     response = client.chat.completions.create(
#         model="gpt-3.5-turbo-012",
#         response_format={"type": "json_object"},
#         messages=[
#             {
#                 "role": "system",
#                 "content": "You are a helpful assistant designed to output JSON.",
#             },
#             {"role": "user", "content": "Who won the world series in 2020?"},
#         ],
#     )
#     print(response.choices[0].message.content)
# except Exception as e:
#     print("Error:\n", e.code)
#     print(type(e))

# from langchain_openai import OpenAI
# from langchain.prompts import PromptTemplate
# from langchain_community.llms.huggingface_endpoint import HuggingFaceEndpoint
# import os
# import dotenv

# dotenv.load_dotenv()
# import getpass

# OPENAI_API_KEY = os.environ["OPENAI_API_KEY"]
# template = """Question: {question}

# Answer: Let's think step by step."""

# prompt = PromptTemplate.from_template(template)

# llm = OpenAI(api_key=OPENAI_API_KEY)
# # llm = HuggingFaceEndpoint(
# #     repo_id="mistralai/Mistral-7B-Instruct-v0.2",
# #     huggingfacehub_api_token=os.environ["HUGGINGFACEHUB_API_TOKEN"],
# # )

# from langchain.memory import ConversationBufferMemory

# memory = ConversationBufferMemory()

# from langchain.chains import ConversationChain
# import datetime

# start = datetime.datetime.now()
# c = ConversationChain(llm=llm, verbose=True, memory=memory)
# res = c.invoke(input="Do you know sjsu")
# res = c.invoke(input="how is it?")
# end = datetime.datetime.now()
# print(res, (end - start).total_seconds())
