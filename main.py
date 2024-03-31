import json
import discord

# import utils
import interactions
from models import game_modal_comp

#Obtain login token from hidden file
with open('.env', 'r') as f:
    token = json.loads(f.read())['token']

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
        scope=545410383339323403,   #TEMP: prevent needing to wait for /command to register with API
)
async def newgame(ctx: interactions.CommandContext):
    game_modal = await game_modal_comp()
    await ctx.send(components=game_modal)

    print("Done sending")


@bot.component("gameconf_team_type")
async def team_type_response(ctx: interactions.ComponentContext, value):
    await ctx.send(f"Team Type: {value}", ephemeral=True)

@bot.component("gameconf_maps")
async def maps_response(ctx: interactions.ComponentContext, value):
    await ctx.send(f"Maps: {value}", ephemeral=True)


@bot.event()
async def on_start():
    print("Bot started")

def start():
    bot.start()