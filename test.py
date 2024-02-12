from yt_dlp import YoutubeDL
import json

item = "hanh phuc ao"
YDL_OPTIONS = {"format": "all", "noplaylist": "True"}
with YoutubeDL(YDL_OPTIONS) as ydl:
    try:
        info = ydl.extract_info("ytsearch:%s" % item, download=False)
        s = ydl.prepare_filename(info)
    except Exception:
        print(Exception)
    with open("info.json", "w") as file:
        json.dump(info, file)
        print(s)


# from dotenv import load_dotenv
# import sys, os

# path = "".join(sys.path[0]) + "\.env"
# print(path)
# load_dotenv(path, override=True)

# print(os.environ["DISCORD_BOT_TOKEN"])