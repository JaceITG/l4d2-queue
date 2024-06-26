from configparser import ConfigParser
import json, random
import interactions

config = ConfigParser()
config.read('config.ini')

# TODO: generate a unique incremental q_id respecting existing database entities
next_available_id = 0
async def gen_q_id():
    global next_available_id

    next_available_id += 1
    return next_available_id-1

# Check that game setup variables have been set and prompt queue to advance
async def announce_if_ready(queue):
    if queue.status != 0:
        raise ValueError("Queue not in correct state to announce")

    queue_is_ready = (
        queue.game_type is not None and
        queue.team_type is not None
        #len(queue.map_options) >= 3    NOTICE: deprecated for random+cooldown map selection method
    )

    if queue_is_ready:
        await queue.announce_queue()


### Queue Interaction Components ###

def game_setup_comp(q_id: int):

    # Game mode
    gamemode = interactions.SelectMenu(
        placeholder = "Game mode selection",
        custom_id = "gameconf_game_mode",
        options = [
            interactions.SelectOption(label=values['title'], value=f"{key}") for key, values in gamemode_strs.items()
            ],
    )


    # How teams are selected
    random = interactions.SelectMenu(
        placeholder = "Team selection",
        custom_id = "gameconf_team_type",
        options = [
            interactions.SelectOption(label="Random", value=f"random"),
            interactions.SelectOption(label="Selected", value=f"selected"),
            ],
    )

    # Maps available
    # NOTICE: deprecated for random+cooldown map selection method
    maps = interactions.SelectMenu(
        placeholder = "Map choice",
        custom_id = "gameconf_maps",
        min_values=3,
        max_values=3,
        options = [
            interactions.SelectOption(label=map_name, value=f"{map_name}") for map_name in config['GameOptions']['maps'].split(',')
        ]
    )

    component = interactions.spread_to_rows(gamemode, random)

    return component

# Buttons for players to join as player or sub
def queue_join_comp():

    join_button = interactions.Button(
        custom_id="join_button",
        label="Join Queue",
        style=interactions.ButtonStyle.SUCCESS
    )

    join_sub_button = interactions.Button(
        custom_id="sub_button",
        label="Join Queue As Sub",
        style=interactions.ButtonStyle.SECONDARY
    )

    leave_button = interactions.Button(
        custom_id="leave_button",
        label="Leave Queue",
        style=interactions.ButtonStyle.DANGER
    )

    # TEMP
    fill_button = interactions.Button(
        custom_id="fill_button",
        label="Fill Queue",
        style=interactions.ButtonStyle.DANGER
    )

    component = interactions.ActionRow(components=[join_button, join_sub_button, leave_button, fill_button])
    
    return component

# Menu sent to queued players to vote for available maps
def map_vote_comp(maps):

    maps = interactions.SelectMenu(
        placeholder = "Vote for a map",
        custom_id = "player_map_vote",
        min_values=1,
        max_values=1,
        options = [
            interactions.SelectOption(label=map_name, value=f"{map_name}") for map_name in maps
        ]
    )

    return maps

# Prompt to join as sub when queue unjoinable as player
def queue_unjoinable_comp():
    sub_button = interactions.Button(
        custom_id="sub_button",
        label="Join Queue As Sub Instead",
        style=interactions.ButtonStyle.SECONDARY
    )
    
    return sub_button

# Menus for assigning queued players to team
#   Players are assigned to Team 1 (Survivors); Team 2 will be filled with remaining
#
# FIXME: address potential issue of users with identical usernames when addressing players by username
def assign_teams_comp(queue):

    team1 = interactions.SelectMenu(
        placeholder = "Survivors",
        custom_id = "make_team_1",
        min_values=queue.max_players/2,
        max_values=queue.max_players/2,
        options = [
            interactions.SelectOption(label=user.username, value=f"{user.username}") for user in queue.players
        ]
    )

    return team1
    

##############

# Retreive 3 vanilla/custom maps each according to timeout values
def get_random_maps():

    with open("./campaign_maps.json", 'r') as f:
        map_json = json.load(f)

        available_vanilla = [m['name'] for m in map_json['vanilla'] if int(m['timeout']) == 0]
        available_custom = [m['name'] for m in map_json['custom'] if int(m['timeout']) == 0]

    vote_options = random.sample(available_vanilla, 3)
    vote_options += random.sample(available_custom, 3)
    return vote_options

def start_game_msg(queue):
    msg = "**Voting has finished and teams have been selected!**\n"
    msg += f"Map {queue.map} has won the vote\n\n"
    msg += "**__Survivors__**\n"
    msg += '\n'.join([user.mention for user in queue.team1])
    msg += "\n**__Infected__**\n"
    msg += '\n'.join([user.mention for user in queue.team2])

    return msg

# Generate string used in queue announcement message
gamemode_strs = {
        "standard": {"title": "Standard Vanilla+", "desc": "Minor QoL and balance plugins; see ⁠dedicated-server-info for more information!"},
        "realism" : {"title": "Realism", "desc": "Survivors can't see player or item outlines; common infected are more resilient; Witches kill instantly!"},
        "survival": {"title": "Survival", "desc": "Survivors hold out in a small arena; teams swap; the Survivor team with the longest time alive wins!"},
        "jockey"  : {"title": "Riding My Survivor", "desc": "Jockeys are the only Special Infected; Jockey HP, DMG, and speed are significantly increased!"},
        "scavenge": {"title": "Scavenge", "desc": "Survivors collect gas cans in a small arena; teams swap; the Survivor team with the most gas cans wins!"},
        "bleed"   : {"title": "Bleed Out", "desc": "Survivors only have temporary HP; First Aid Kits are replaced with Adrenaline and Pain Pills!"},
        "tank"    : {"title": "Taaannnkk!", "desc": "Only Tanks spawn; First Aid Kits are replaced with Adrenaline and Pain Pills!"},
        "hpack"   : {"title": "Healthpackalypse!", "desc": "All health items are removed from spawn pools!"},
        "confogl" : {"title": "Confogl", "desc": "First Aid Kits are removed; more Adrenaline and Pain Pills spawn; only Tier-1 weapons!"},
        "l4d1"    : {"title": "Left 4 Dead 1", "desc": "This queue is for Left 4 Dead 1, NOT L4D2!"},
        "l4d2"    : {"title": "unmodded L4D2", "desc": "No plugins or alterations of any kind; this is pure vanilla Left 4 Dead 2!"},
    }
def queue_message(gamemode):

    if gamemode not in gamemode_strs.keys():
        raise ValueError

    # Fill in template with attributes for selected game type
        # f"{carriers_role.mention} {ksobs_role.mention}\n" #FIXME: Remove or change mentions for new server
    return (
f"""A **__{gamemode_strs[gamemode]['title']}__** versus game is being set up for 8 players!
{("No Charger, Jockey, or Spitter, but Boomers can vomit instantly after spawning/while being shoved, Hunters deal damage faster, and Smokers are"
    "hitscan.  Tanks throw rocks quicker and move faster when on fire.  Witches kill downed Survivors faster."
    "Small firearm arsenal, superior pistols, no melee weapons, generally faster-paced than L4D2 Versus with less camping/baiting. The score is" 
    "determined by Survivor HP at the end of a level and a per-map difficulty modifier.") if gamemode == "l4d1" else ""}
({gamemode_strs[gamemode]['desc']})\n
Use the buttons below to join this queue as a player or sub\n
Once 8 players have joined, maps will be voted upon, and teams will be assigned.
Note:  If 8 players have not joined in two hours, this queue will be remade.  **Do not queue unless you {"own Left 4 Dead 1 and" if gamemode=="l4d1" else ""} have at least two hours available.**\n
Please report any issues to the owner/developers"""
    )
