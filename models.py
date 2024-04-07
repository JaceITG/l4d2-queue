import discord
from configparser import ConfigParser
import interactions

config = ConfigParser()
config.read('config.ini')

import discord
from discord.ext import commands

from utils import queue_message

async def game_setup_comp():

    # How teams are selected
    random = interactions.SelectMenu(
        placeholder = "Team selection",
        custom_id = "gameconf_team_type",
        options = [
            interactions.SelectOption(label="Random", value="random"),
            interactions.SelectOption(label="Selected", value="selected"),
            ],
    )

    # Maps available
    maps = interactions.SelectMenu(
        placeholder = "Map choice",
        custom_id = "gameconf_maps",
        min_values=3,
        max_values=3,
        options = [
            interactions.SelectOption(label=map_name, value=map_name) for map_name in config['GameOptions']['maps'].split(',')
        ]
    )

    component = interactions.spread_to_rows(random, maps)

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

    async def __init__(self, q_id: int, q_ctx: interactions.CommandContext, game_type: str):
        self.q_id = q_id
        self.q_ctx
        self.game_type = game_type

        try:
            self.q_message = queue_message(self.game_type)
        except ValueError:
            raise

        self.announcement_msg = ""
        self.status = 0
        
        self.players = []
        self.team1 = []
        self.team2 = []

        game_modal = await game_setup_comp()
        await self.q_ctx.send(components=game_modal)
        

    async def handle_reaction():
        pass

    # Record data from scores [team1, team2]
    async def log_match(scores):
        pass

