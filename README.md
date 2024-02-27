# Discord Chat Bot with OpenAI API
This Discord chat bot utilizes the OpenAI API to provide users with a single chat, conversation chat, and image to text chat capabilities. Additionally, it also includes a music feature for users to enjoy.

## Features
Single chat: Users can interact with the bot in one-on-one conversations.

Conversation chat: Users can engage in conversations with the bot over multiple messages.

Image to text chat: Users can upload images and receive text descriptions from the bot.

Music feature: Users can listen to music through the bot.

## Installation
Clone the repository: git clone https://github.com/dongtandung2001/aio-discord-bot.git

Install dependencies: `pip install -r requirements.txt`

Set up enviroment variables `cp .env_example .env`

Run the bot: Choose one of these 2
```sh
python server.py
```

```sh
docker-compose up --build
```
## Usage
Invite the bot to your Discord server.

Use the following commands to interact with the bot:

### Chat Bot

`.chat [message]`: Start a single chat with the bot.

`.conversation [message]`: Engage in a conversation with the bot.

`.chat image [image]`: Upload a text image to receive answer.

### Music Bot

`.play [song]`: Play a song using the music feature.

`.replay`: Auto replay the last played track

`.join`: Ask bot to join voice channel

`.disconnect`: Disconnect bot from voice channel

`.skip`: Skip the current track

`.stop`: Stop the bot, clear queue and leave voice channel


## Contributing
Contributions are welcome! Feel free to fork the repository and submit a pull request with your improvements.

## License
This project is licensed under the MIT License.

## Acknowledgements
OpenAI API for providing the chat capabilities.
discord.py for enabling bot interactions.
yt_dlp for the music feature.

--- 

Feel free to reach out if you have any questions or feedback!
