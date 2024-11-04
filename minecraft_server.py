import discord
import subprocess
import re
import asyncio

# Replace these with your actual values
TOKEN = 'Your token here'  # Replace with your bot token
CHANNEL_ID = 123456789  # Replace with your channel ID (an integer)
ROLE_NAME = 'Your role here'  # The role to target
SERVER_JAR = 'server_1_21_3.jar' # Server runtime file (update here when you update after a new version release)

# Create intents
intents = discord.Intents.default()
intents.messages = True  # Enable message-related events
intents.guilds = True    # Enable guild-related events

# Create a Discord client with the specified intents
client = discord.Client(intents=intents)

# Dictionary to store each player's login message
logged_in_players = {}

async def send_message(content):
    channel = client.get_channel(CHANNEL_ID)
    if channel:
        return await channel.send(content)

async def listen_to_server():
    # Start the Minecraft server process, adjust params as needed
    process = subprocess.Popen(['java', '-Xms6G', '-Xmx6G', '-jar', SERVER_JAR, 'nogui'],
                               stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

    while True:
        # Use run_in_executor to prevent blocking the event loop
        output = await asyncio.get_event_loop().run_in_executor(None, process.stdout.readline)
        if output:
            print(output.strip())  # Print the output to the console

            # Check for player login
            login_match = re.search(r'\[.*INFO\]: (.*) joined the game', output)
            if login_match:
                player_name = login_match.group(1)
                role = discord.utils.get(client.guilds[0].roles, name=ROLE_NAME)  # Get the role
                if role:
                    message_content = f"{player_name} has entered the Grove! <@&{role.id}>"
                    message = await send_message(message_content)  # Send the message to Discord
                    logged_in_players[player_name] = message  # Store the message for future deletion

            # Check for player logout
            logout_match = re.search(r'\[.*INFO\]: (.*) left the game', output)
            if logout_match:
                player_name = logout_match.group(1)
                role = discord.utils.get(client.guilds[0].roles, name=ROLE_NAME)  # Get the role
                if role and player_name in logged_in_players:
                    # Delete the login message when the player logs out
                    await logged_in_players[player_name].delete()  # Delete the stored message
                    del logged_in_players[player_name]  # Remove the player from the dictionary

# Run the bot
@client.event
async def on_ready():
    print(f'Logged in as {client.user}')
    await listen_to_server()  # Start listening for server output

# Start the bot with the specified token
client.run(TOKEN)
