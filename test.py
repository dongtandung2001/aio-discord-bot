from yt_dlp import YoutubeDL
import json

item = "hanh phuc ao"
YDL_OPTIONS = {"format": "all", "noplaylist": "True"}
with YoutubeDL(YDL_OPTIONS) as ydl:
    try:
        info = ydl.extract_info(f"ytsearch3:{item}", download=False)
        info = info["entries"]
    except Exception:
        print(Exception)
    with open("info.json", "w") as file:
        json.dump(info, file)


# # from dotenv import load_dotenv
# # import sys, os

# # path = "".join(sys.path[0]) + "\.env"
# # print(path)
# # load_dotenv(path, override=True)

# # print(os.environ["DISCORD_BOT_TOKEN"])


# def positive_input(func):
#     def wrapper(x):
#         if x <= 0:
#             raise ValueError("Input must be positive")
#         return func(x)

#     return wrapper


# @positive_input
# def square(x):
#     return x**2


# print(square(-1))

a = "abc"
if a is bool:
    print(a)
