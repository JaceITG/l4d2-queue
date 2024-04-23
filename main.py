import json, random
import discord
from configparser import ConfigParser

# import utils
import interactions
from models import GameQueue
from utils import gen_q_id, announce_if_ready, queue_unjoinable_comp
from utils import get_random_maps

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

@bot.command(
        name="get_maps",
        scope=[int(config['ServerInfo']['server_id']), 1224464761425494177], 
)
async def get_maps(ctx: interactions.CommandContext):
    await ctx.send(', '.join(get_random_maps()), ephemeral=True)


### Command: create ###
# Usage: /create event_name start_time [end_time]
#
# Creates an event in the calendar
#####
@bot.command(
        name="start",
        description="Create a new queue for a L4D2 Versus game",
        scope=[int(config['ServerInfo']['server_id']), 1224464761425494177, 545410383339323403],   #TEMP: prevent needing to wait for /command to register with API
)
@discord.ext.commands.has_role(config['ServerInfo']['matchmaker_role_id'])
async def newgame(ctx: interactions.CommandContext):
    global active_games

    new_queue = GameQueue(q_id=await gen_q_id(), q_ctx=ctx)

    active_games[new_queue.q_id] = new_queue

### Handle incoming reaction adds ###

@bot.event()
async def on_reaction_add(reaction: discord.Reaction, user: discord.Member):
    q_id = int(reaction.message.embeds[0].footer.text.split(' ')[-1])
    
    queue = active_games[q_id]
    queue.handle_reaction(reaction, user)

### Wait for admin response on game_modal component menus ###
    
@bot.component("gameconf_game_mode")
async def game_mode_response(ctx: interactions.ComponentContext, value):
    q_id = int(ctx.message.embeds[0].footer.text.split(' ')[-1])

    active_games[q_id].game_type = value[0]
    await announce_if_ready(active_games[q_id])
    await ctx.defer(ephemeral=True, edit_origin=True)

@bot.component("gameconf_team_type")
async def team_type_response(ctx: interactions.ComponentContext, value):
    q_id = int(ctx.message.embeds[0].footer.text.split(' ')[-1])

    active_games[q_id].team_type = value[0]
    await announce_if_ready(active_games[q_id])
    await ctx.defer(ephemeral=True, edit_origin=True)

@bot.component("gameconf_maps")
async def maps_response(ctx: interactions.ComponentContext, value):
    q_id = int(ctx.message.embeds[0].footer.text.split(' ')[-1])

    active_games[q_id].map_options = value
    await announce_if_ready(active_games[q_id])
    await ctx.defer(ephemeral=True, edit_origin=True)

##############

### Catch Button Join Component Interactions ###

@bot.component("join_button")
async def player_join(ctx: interactions.ComponentContext):
    q_id = int(ctx.message.embeds[0].footer.text.split(' ')[-1])

    try:
        await active_games[q_id].handle_join(ctx, "player_join")
    except IndexError:
        await ctx.send(content="**Cannot join queue: already full or started**",
                    components=[queue_unjoinable_comp()],
                    embeds=interactions.Embed().set_footer(text=f"ID: {q_id}"),
                    ephemeral=True)
    
    await ctx.defer(ephemeral=True, edit_origin=True)

@bot.component("sub_button")
async def sub_join(ctx: interactions.ComponentContext):
    q_id = int(ctx.message.embeds[0].footer.text.split(' ')[-1])

    try:
        await active_games[q_id].handle_join(ctx, "sub_join")
    except IndexError:
        await ctx.send(content="**Cannot join queue as a sub when you are already a player**", ephemeral=True)
    
    await ctx.defer(ephemeral=True, edit_origin=True)

@bot.component("leave_button")
async def player_leave(ctx: interactions.ComponentContext):
    q_id = int(ctx.message.embeds[0].footer.text.split(' ')[-1])

    try:
        await active_games[q_id].handle_join(ctx, "player_leave")
    except IndexError:
        await ctx.send(content="**Cannot leave the queue after it has popped.**\nPlease contact matchmaker if you need a sub.", ephemeral=True)

    await ctx.defer(ephemeral=True, edit_origin=True)

# TEMP: Admin Fill queue with random users
@bot.component("fill_button")
async def fill_players(ctx: interactions.ComponentContext):
    q_id = int(ctx.message.embeds[0].footer.text.split(' ')[-1])
    queue = active_games[q_id]

    guild = await ctx.get_guild()
    members = guild.get_members()
    members = await members.flatten()

    fills = queue.max_players - len(queue.players)
    added = 0
    while added < fills:
        member = random.choice(members)
        try:
            ctx.user = member.user
            await active_games[q_id].handle_join(ctx, "player_join")
            added += 1
        except IndexError:
            continue
    
    await ctx.defer(ephemeral=True, edit_origin=True)


##############

### Get Team Assignment from Admin ###

# @bot.component("make_team_1")
# async def make_team(ctx: interactions.ComponentContext, value):
#     q_id = int(ctx.message.embeds[0].footer.text.split(' ')[-1])

#     await active_games[q_id].make_teams(team1=value)

#     await ctx.defer(ephemeral=True, edit_origin=True)

##############

### Catch Player Map Vote ###

def is_queued_player(ctx: discord.Interaction) -> bool:

    q_id = int(ctx.message.embeds[0].footer.text.split(' ')[-1])
    return ctx.user in active_games[q_id].players

@bot.component("player_map_vote")
@discord.app_commands.check(is_queued_player)
async def player_map_vote(ctx: interactions.ComponentContext, value):
    q_id = int(ctx.message.embeds[0].footer.text.split(' ')[-1])

    await active_games[q_id].handle_vote(ctx.user, value[0])

    await ctx.defer(ephemeral=True, edit_origin=True)

##############

@bot.event()
async def on_start():
    print("Bot started")

def start():
    bot.start()