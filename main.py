import json
import discord
from configparser import ConfigParser

# import utils
import interactions
from models import GameQueue
from utils import gen_q_id

#Obtain login token from hidden file
with open('.env', 'r') as f:
    token = json.loads(f.read())['token']

#Init bot
bot = interactions.Client(token=token)

#Load config file
config = ConfigParser()
config.read('config.ini')

#Running queues
active_games = {}

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
        scope=int(config['ServerInfo']['server_id']),   #TEMP: prevent needing to wait for /command to register with API
)
@discord.ext.commands.has_role(config['ServerInfo']['matchmaker_role_id'])
async def newgame(ctx: interactions.CommandContext):
    global active_games

    try:
        new_queue = GameQueue(q_id=await gen_q_id(), q_ctx=ctx)
    except ValueError: 
        await ctx.send("Invalid queue type. View help message with !jockey for available game types.")
        return

    active_games[new_queue.q_id] = new_queue

### Wait for admin response on game_modal component menus ###
    
@bot.component("gameconf_game_mode")
async def team_type_response(ctx: interactions.ComponentContext, value):
    value = value[0].split('_')
    q_id = int(value[-1])
    value = '_'.join(value[:-1])

    # try:
    #     queue.q_message = queue_message(self.game_type)
    # except ValueError:
    #     raise
    
    await ctx.send(f"Game Mode: {value} (q_id: {q_id})", ephemeral=True)

    active_games[q_id].game_type = value

@bot.component("gameconf_team_type")
async def team_type_response(ctx: interactions.ComponentContext, value):
    value = value[0].split('_')
    q_id = value[-1]
    value = '_'.join(value[:-1])

    await ctx.send(f"Team Type: {value} (q_id: {q_id})", ephemeral=True)

    active_games[q_id].team_type = value

@bot.component("gameconf_maps")
async def maps_response(ctx: interactions.ComponentContext, value):
    maps = []
    q_id = None
    for v in value:
        m = v.split('_')
        q_id = m[-1]
        maps.append(' '.join(m[:-1]))

    await ctx.send(f"Maps: {maps} (q_id: {q_id})", ephemeral=True)

    active_games[q_id].map_options = maps

##############

@bot.event()
async def on_start():
    print("Bot started")

def start():
    bot.start()