import discord
from configparser import ConfigParser
import interactions

config = ConfigParser()
config.read('config.ini')

class GameModal(discord.ui.Modal, title="Create Game"):
    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.send_message(f'Creating game')
    pass

async def game_modal_comp():

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

