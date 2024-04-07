import discord
from configparser import ConfigParser
import interactions, json, asyncio

config = ConfigParser()
config.read('config.ini')

#Obtain login token from hidden file
with open('.env', 'r') as f:
    token = json.loads(f.read())['token']
bot = interactions.Client(token=token)

import discord
from discord.ext import commands

from utils import queue_message, gamemode_strs

def game_setup_comp(q_id: int):

    # Game mode
    gamemode = interactions.SelectMenu(
        placeholder = "Game mode selection",
        custom_id = "gameconf_game_mode",
        options = [
            interactions.SelectOption(label=values['title'], value=f"{key}_{q_id}") for key, values in gamemode_strs.items()
            ],
    )


    # How teams are selected
    random = interactions.SelectMenu(
        placeholder = "Team selection",
        custom_id = "gameconf_team_type",
        options = [
            interactions.SelectOption(label="Random", value=f"random_{q_id}"),
            interactions.SelectOption(label="Selected", value=f"selected_{q_id}"),
            ],
    )

    # Maps available
    maps = interactions.SelectMenu(
        placeholder = "Map choice",
        custom_id = "gameconf_maps",
        min_values=3,
        max_values=3,
        options = [
            interactions.SelectOption(label=map_name, value=f"{map_name}_{q_id}") for map_name in config['GameOptions']['maps'].split(',')
        ]
    )

    component = interactions.spread_to_rows(gamemode, random, maps)

    return component

### Queue ###
#
# status indicating state of Queue:
# 0 -> created, no announcement made
# 1 -> announced, waiting for joins
# 2 -> queue popped, waiting for map votes
# 3 -> game in progress
# 4 -> game ended, results logged

class GameQueue:

    def __init__(self, q_id: int, q_ctx: interactions.CommandContext,):
        self.q_id = q_id
        self.q_ctx = q_ctx
        self.loop = asyncio.get_event_loop()

        try:
            self.q_message = ""
        except ValueError:
            raise

        self.announcement_msg = ""
        self.status = 0
        
        self.game_type = ""
        self.players = []
        self.team1 = []
        self.team2 = []

        self.game_modal = game_setup_comp(q_id)
        self.loop.create_task( self.q_ctx.send(components=self.game_modal, ephemeral=True) )
    
        

    async def handle_reaction():
        pass

    # Record data from scores [team1, team2]
    async def log_match(scores):
        pass

