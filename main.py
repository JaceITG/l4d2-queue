import json
import discord
from configparser import ConfigParser

# import utils
import interactions
from models import game_modal_comp, gen_q_id, GameQueue

#Obtain login token from hidden file
with open('.env', 'r') as f:
    token = json.loads(f.read())['token']

#Load config file
config = ConfigParser()
config.read('config.ini')

#Running queues
active_games = []

#Init bot
bot = interactions.Client(token=token)

#API Connectivity Test Command
@bot.command(
        name="ping",
        description="test",
)
async def ping(ctx: interactions.CommandContext):
    await ctx.send("pong")

### Command: create ###
# Usage: /create event_name start_time [end_time]
#
# Creates an event in the calendar
#####
@bot.command(
        name="start",
        description="Create a new queue for a L4D2 Versus game",
        options = [
            interactions.Option(
                name = "game_type",
                description = "Game mode to create a queue for",
                type = interactions.OptionType.STRING,
                required = False,
            ),
        ],
        scope=int(config['ServerInfo']['server_id']),   #TEMP: prevent needing to wait for /command to register with API
)
@discord.app_commands.checks.has_role(
    bot.get_guild(int(config["ServerInfo"]['server_id'])).get_role(int(config['ServerInfo']['Matchmaker']))
)
async def newgame(ctx: interactions.CommandContext, game_type: str = "standard"):
    global active_games

    try:
        new_queue = await GameQueue(q_id=gen_q_id(), q_ctx=ctx, game_type=game_type)
    except ValueError: 
        await ctx.send("Invalid queue type. View help message with !jockey for available game types.")
        return

    active_games.append(new_queue)

### Wait for admin response on game_modal component menus ###
    
@bot.component("gameconf_team_type")
async def team_type_response(ctx: interactions.ComponentContext, value):
    await ctx.send(f"Team Type: {value}", ephemeral=True)

    #TODO: pass response to GameQueue

@bot.component("gameconf_maps")
async def maps_response(ctx: interactions.ComponentContext, value):
    await ctx.send(f"Maps: {value}", ephemeral=True)

    #TODO: pass response to GameQueue

##############

@bot.event()
async def on_start():
    print("Bot started")

def start():
    bot.start()