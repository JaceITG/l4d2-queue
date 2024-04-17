import json
import discord
from configparser import ConfigParser

# import utils
import interactions
from models import GameQueue
from utils import gen_q_id, announce_if_ready

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
        scope=[int(config['ServerInfo']['server_id']), 1224464761425494177],   #TEMP: prevent needing to wait for /command to register with API
)
@discord.ext.commands.has_role(config['ServerInfo']['matchmaker_role_id'])
async def newgame(ctx: interactions.CommandContext):
    global active_games

    new_queue = GameQueue(q_id=await gen_q_id(), q_ctx=ctx)

    active_games[new_queue.q_id] = new_queue

### Wait for admin response on game_modal component menus ###
    
@bot.component("gameconf_game_mode")
async def game_mode_response(ctx: interactions.ComponentContext, value):
    q_id = int(ctx.message.embeds[0].footer.text)

    active_games[q_id].game_type = value[0]
    await announce_if_ready(active_games[q_id])
    await ctx.defer(ephemeral=True, edit_origin=True)

@bot.component("gameconf_team_type")
async def team_type_response(ctx: interactions.ComponentContext, value):
    q_id = int(ctx.message.embeds[0].footer.text)

    active_games[q_id].team_type = value[0]
    await announce_if_ready(active_games[q_id])
    await ctx.defer(ephemeral=True, edit_origin=True)

@bot.component("gameconf_maps")
async def maps_response(ctx: interactions.ComponentContext, value):
    q_id = int(ctx.message.embeds[0].footer.text)

    active_games[q_id].map_options = value
    await announce_if_ready(active_games[q_id])
    await ctx.defer(ephemeral=True, edit_origin=True)

##############

@bot.event()
async def on_start():
    print("Bot started")

def start():
    bot.start()