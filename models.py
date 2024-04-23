import discord
from configparser import ConfigParser
import interactions, json, asyncio, random

config = ConfigParser()
config.read('config.ini')

#Obtain login token from hidden file
with open('.env', 'r') as f:
    token = json.loads(f.read())['token']
bot = interactions.Client(token=token)

import discord
from discord.ext import commands

from utils import queue_message, start_game_msg
from utils import game_setup_comp, queue_join_comp
from utils import get_random_maps, map_vote_comp
from utils import assign_teams_comp


### Queue ###
#
# status indicating state of Queue:
# 0 -> created, no announcement made
# 1 -> announced, waiting for joins
# 2 -> queue popped, waiting for map votes and team creation
# 3 -> game in progress
# 4 -> game ended, results logged

class GameQueue:

    def __init__(self, q_id: int, q_ctx: interactions.CommandContext,):
        self.q_id = q_id
        self.q_ctx = q_ctx
        self.loop = asyncio.get_event_loop()

        self.status = 0
        
        # Options set by admin
        self.game_type = None
        self.team_type = None
        self.map_options = {}       # map: [Player,]
        self.num_votes = 0

        self.map = None
        
        self.players = []
        self.team1 = [] # Survivors
        self.team2 = [] # Infected
        self.subs = []
        self.max_players = 4

        self.game_modal = game_setup_comp(q_id)

        embed = interactions.Embed()
        embed.set_footer(text=f"ID: {self.q_id}")
        self.loop.create_task( self.q_ctx.send(components=self.game_modal, embeds=embed, ephemeral=True) )
    
    # Send out announcement message for joins
    async def announce_queue(self):
        self.status = 1

        try:
            self.q_message = queue_message(self.game_type)
        except ValueError:
            raise

        # Announcement Embed
        embed = interactions.Embed()
        embed.set_footer(text=f"ID: {self.q_id}")
        embed.set_author(name="queue_announcement")

        # Join Queue Buttons
        button_row = queue_join_comp()

        await self.q_ctx.send(content=self.q_message, embeds=embed, components=button_row)

    # Send message for map voting and make teams
    async def pop_queue(self):
        self.status = 2

        self.map_options = {m:[] for m in get_random_maps()}

        embed = interactions.Embed()
        embed.set_footer(text=f"ID: {self.q_id}")
        embed.set_author(name="Vote for a map")

        await self.q_ctx.send(embeds=embed, components=[map_vote_comp(self.map_options.keys())])
        await self.make_teams()

        # Wait for all players to vote, or N minutes after teams made
        async def wait_for_votes():
            while self.num_votes < self.max_players:
                await asyncio.sleep(5)
        
        try:
            await asyncio.wait_for(wait_for_votes(), timeout=10)
        except asyncio.TimeoutError:
            # Continue to start game
            pass

        await self.start_game()
    
    # Ping players with teams and vote results
    async def start_game(self):
        self.status = 3

        # Get winning map (longest list value in map_options)
        self.map = max(self.map_options, key=lambda k: len(self.map_options[k]))

        embed = interactions.Embed()
        embed.set_footer(text=f"ID: {self.q_id}")

        await self.q_ctx.send(content=start_game_msg(self) , embeds=embed)

    
    # Update announcement message with list/count of queued players
    async def update_announcement(self, announcement_msg: discord.Message):

        # Players embed
        embed = interactions.Embed()
        embed.set_footer(text=f"ID: {self.q_id}")
        embed.set_author(name="queue_announcement")

        embed.add_field(name=f"Players ({len(self.players)})", value='\n'.join([user.username for user in self.players]), inline=True)
        embed.add_field(name=f"Subs ({len(self.subs)})", value='\n'.join([user.username for user in self.subs]), inline=True)

        button_row = queue_join_comp()

        await announcement_msg.edit(embeds=embed, components=button_row)

    # Process interactions with buttons on the announcement message
    async def handle_join(self, ctx: interactions.ComponentContext, join_type: str):

        if join_type == "player_join":
            
            # Check if queue is joinable
            if self.status != 1 or len(self.players) >= self.max_players:
                raise IndexError
            
            # Resolve silently if player already in queue
            if ctx.user in self.players:
                return
            
            # If already in subs, remove from sub list
            if ctx.user in self.subs:
                self.subs.remove(ctx.user)
            
            self.players.append(ctx.user)
            await self.update_announcement(ctx.message)

            if len(self.players) >= self.max_players:
                # Queue popped
                await self.pop_queue()

        elif join_type == "sub_join":
            
            # Don't allow players already in primary queue to sub
            if ctx.user in self.players:
                raise IndexError
            
            self.subs.append(ctx.user)
            await self.update_announcement(ctx.message)

        elif join_type == "player_leave":

            # Prevent primary player leaves after queue pops
            if self.status > 1 and ctx.user in self.players:
                raise IndexError
            
            try:
                self.players.remove(ctx.user)
            except ValueError:
                pass
            
            try:
                self.subs.remove(ctx.user)
            except ValueError:
                pass
            
            await self.update_announcement(ctx.message)

    
    # Random: shuffle list of players and split teams on half
    # Selected: send component for admin to select half of the players
    #           to be on Team 1 (Survivors)           
    async def make_teams(self):

        if self.team_type == "random":
            randomized_players = self.players
            random.shuffle(randomized_players)
            self.team1 = randomized_players[:4]
            self.team2 = randomized_players[4:]
        
        elif self.team_type == "selected":
            
            embed = interactions.Embed(title="Select players to assign to Survivors. Infected will be filled with remaining players.")
            embed.set_footer(f"ID: {self.q_id}")

            await self.q_ctx.send(embeds=embed, components=[assign_teams_comp(self)], ephemeral=True)

            ctx = await self.q_ctx.client.wait_for_component("make_team_1")

            # Send user objects to assigned teams
            for user in self.players:
                # Put in team 1 (survivors) if selected by admin
                if user.username in ctx.data.values:
                    self.team1.append(user)
                else:
                    self.team2.append(user)
                
            await ctx.defer(ephemeral=True, edit_origin=True)
        


    # Process Select Menu input from player
    async def handle_vote(self, user: interactions.User, vote: str):

        # Check queue state in voting stage
        if not self.status == 2:
            return
        
        # Check if user vote already counted
        for m in self.map_options.keys():
            vote_list = self.map_options[m]
            if user in vote_list:
                vote_list.remove(user)
                self.map_options[m] = vote_list
                self.num_votes -= 1
        
        # Add user vote
        self.num_votes += 1
        self.map_options[vote].append(user)


    # Record data from scores [team1, team2]
    async def end_match(self, scores):
        pass

