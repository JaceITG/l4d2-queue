import json
import discord
from configparser import ConfigParser

# import utils
import interactions
from models import game_modal_comp

#Obtain login token from hidden file
with open('.env', 'r') as f:
    token = json.loads(f.read())['token']

#Load config file
config = ConfigParser()
config.read('config.ini')

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
async def newgame(ctx: interactions.CommandContext, game_type: str = "standard"):
    game_modal = await game_modal_comp()
    await ctx.send(components=game_modal)

    print("Done sending")

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