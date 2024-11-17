import discord
import subprocess
import re
import asyncio
import random
from dotenv import load_dotenv
import os
import json

# Load environment variables from the .env file
load_dotenv()

# Fetch values from the .env file
TOKEN = os.getenv('BOT_TOKEN')
LOGIN_CHANNEL_ID = int(os.getenv('LOGIN_CHANNEL_ID'))
FEED_CHANNEL_ID = int(os.getenv('FEED_CHANNEL_ID'))
ROLE_NAME = os.getenv('ROLE_NAME')
SERVER_JAR_PATH = os.getenv('SERVER_JAR_PATH')

# Create intents
intents = discord.Intents.default()
intents.messages = True  # Enable message-related events
intents.guilds = True    # Enable guild-related events

# Create a Discord client with the specified intents
client = discord.Client(intents=intents)

# Dictionary to store each player's login message
logged_in_players = {}

# GIF URLs for various death types
with open('death-gifs.json', 'r') as file:
    gifs = json.load(file)

# Death messages for each death type
death_messages = {
    "slain": "was bested in combat!",
    "fell": "learned about gravity the hard way!",
    "drowned": "met an unfortunate watery end.",
    "burned": "was consumed by flames!",
    "explosion": "went out with a bang!",
    "hit the ground too hard": "had a close encounter with the ground!",
    "suffocated": "suffocated in a wall... Yikes!",
    "shot by": "was shot by a skeleton!",
    "pricked to death": "was pricked by a cactus!",
    "lava": "was engulfed by lava!",
    "blew up": "blew up in a fiery explosion!",
    "walked into a cactus": "walked into a cactus... Ouch!"
}

async def send_message(content, gif_url=None, channel_id=None):
    channel = client.get_channel(channel_id)
    if channel:
        # Send the main content message
        main_message = await channel.send(content)
        # Send GIF if provided
        if gif_url:
            await channel.send(gif_url)
        return main_message  # Return the main message for tracking

async def player_login(login_match):
    player_name = login_match.group(1)
    role = discord.utils.get(client.guilds[0].roles, name=ROLE_NAME)
    if role:
        message_content = f"{player_name} has entered the Grove! <@&{role.id}>"
        # Store the message object returned so it can be deleted on logout
        message = await send_message(message_content, channel_id=LOGIN_CHANNEL_ID)
        logged_in_players[player_name] = message

async def player_logout(logout_match):
    player_name = logout_match.group(1)
    # Retrieve and delete the login message
    if player_name in logged_in_players:
        await logged_in_players[player_name].delete()
        del logged_in_players[player_name]

async def listen_to_server():
    process = subprocess.Popen(
        ['java', '-Xms6G', '-Xmx6G', '-jar', SERVER_JAR_PATH, 'nogui'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
        cwd=os.path.dirname(SERVER_JAR_PATH)  # Set working directory to the jar file's folder
    )

    while True:
        output = await asyncio.get_event_loop().run_in_executor(None, process.stdout.readline)
        if output:
            print(output.strip())

            # Player login message
            login_match = re.search(r'\[.*INFO]: (.*) joined the game', output)
            if login_match:
                await player_login(login_match)

            # Player logout message
            logout_match = re.search(r'\[.*INFO\]: (.*) left the game', output)
            if logout_match:
                await player_logout(logout_match)

            # Player death message
            death_match = re.search(r'\[.*INFO\]: (.*) (was slain by .*|fell from a high place|burned to death|lava|drowned|blew up|hit the ground too hard|was shot by .*|was pricked to death|walked into a cactus|suffocated)', output)
            if death_match:
                player_name = death_match.group(1)
                death_type = death_match.group(2)

                # Get the custom death message and select a GIF if defined
                custom_message = death_messages.get(death_type, f"{player_name} met an unfortunate end.")
                gif_url = None

                if death_type in gifs:
                    gif_url = random.choice(gifs[death_type])

                await send_message(custom_message, gif_url, channel_id=FEED_CHANNEL_ID)

# Run the bot
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await listen_to_server()

# Start the bot with the specified token
client.run(TOKEN)
