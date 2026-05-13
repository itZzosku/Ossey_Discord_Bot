from typing import Union, Sequence
import hikari
import lightbulb
import json
from utils import read_json_file
import random
from .warcraftlogs import initialize_log_checks


def manage_logs_command(bot):
    @bot.command
    @lightbulb.command("managelogs", "Add or remove log sources")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def manage_logs(ctx):
        pass

    # Subcommand for adding guilds
    @manage_logs.child
    @lightbulb.option("channels", "Comma-separated list of channel names", type=str, autocomplete=True)
    @lightbulb.option("region", "The region of the guild", type=str, autocomplete=True)
    @lightbulb.option("realm", "The realm of the guild", type=str)
    @lightbulb.option("guild_name", "The name of the guild", type=str)
    @lightbulb.command("add_guild", "Add a guild")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def add_guild(ctx):
        guild_name = ctx.options.guild_name
        region = ctx.options.region
        realm = ctx.options.realm
        channels_input = ctx.options.channels

        url = f"https://www.warcraftlogs.com:443/v1/reports/guild/{guild_name}/{realm}/{region}"

        # Generate a random color
        random_color = "#{:06x}".format(random.randint(0, 0xFFFFFF))

        channels_list = [channel.strip() for channel in channels_input.split(',')]

        guild_data = {
            "url": url,
            "color": random_color,
            "filename": f"previouslogsid_{guild_name}.txt",
            "channels": channels_list
        }

        # Read the current config
        config = read_json_file('config.json')

        # Ensure 'log_sources' key exists and it's a dictionary
        if 'log_sources' not in config or not isinstance(config['log_sources'], dict):
            config['log_sources'] = {}

        # Add the guild data under 'log_sources'
        config['log_sources'][guild_name] = guild_data

        # Write back to config
        with open('config.json', 'w') as file:
            json.dump(config, file, indent=4)

        # After updating config, reinitialize log checks
        await initialize_log_checks(ctx.bot)

        channels_str = ", ".join(channels_list)
        response_message = f"Added guild '{guild_name}' in realm '{realm}' in region '{region}' to channels: {channels_str} under log sources."
        await ctx.respond(response_message)
        print(response_message)  # Debugging output

    @manage_logs.child
    @lightbulb.option("url", "The URL of the log source", type=str)
    @lightbulb.option("color", "Color for the log source", type=str)
    @lightbulb.option("log_source_name", "The name of the log source to add", type=str)
    @lightbulb.command("add", "Add a log source")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def add_log_source(ctx):
        log_source_name = ctx.options.log_source_name
        url = ctx.options.url
        color = ctx.options.color

        # Automatically generate the filename
        filename = f"previouslogsid_{log_source_name}.txt"

        # Read the current config
        config = read_json_file('config.json')

        # Add the log source
        config['log_sources'][log_source_name] = {
            "url": url,
            "color": color,
            "filename": filename
        }

        # Write back to config
        with open('config.json', 'w') as file:
            json.dump(config, file, indent=4)

        # After updating config, reinitialize log checks
        await initialize_log_checks(ctx.bot)

        response_message = f"Added log source '{log_source_name}' with filename '{filename}'."
        await ctx.respond(response_message)
        print(response_message)  # Debugging output

    @manage_logs.child
    @lightbulb.option("log_source_name", "The name of the log source to remove", type=str, autocomplete=True)
    @lightbulb.command("remove", "Remove a log source")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def remove_log_source(ctx):
        log_source_name = ctx.options.log_source_name

        # Read the current config
        config = read_json_file('config.json')

        # Remove the log source
        if log_source_name in config['log_sources']:
            del config['log_sources'][log_source_name]
            # Write back to config
            with open('config.json', 'w') as file:
                json.dump(config, file, indent=4)
            response_message = f"Removed log source '{log_source_name}'."
            await ctx.respond(response_message)
            print(response_message)  # Debugging output
        else:
            response_message = f"Log source '{log_source_name}' not found."
            await ctx.respond(response_message)
            print(response_message)  # Debugging output

    # Autocomplete function for removing log sources
    @remove_log_source.autocomplete("log_source_name")
    async def remove_log_source_autocomplete(
            opt: hikari.AutocompleteInteractionOption,
            inter: hikari.AutocompleteInteraction
    ) -> Union[
        str, Sequence[str], hikari.api.AutocompleteChoiceBuilder, Sequence[hikari.api.AutocompleteChoiceBuilder]]:
        config = read_json_file('config.json')
        log_sources = config['log_sources']

        # Find matches based on user input
        input_str = opt.value.lower()
        matches = [name for name in log_sources if input_str in name.lower()]

        # Create a list of autocomplete choices
        choices = [hikari.CommandChoice(name=name, value=name) for name in matches]

        # Respond with the matches
        return choices

    @add_guild.autocomplete("region")
    async def region_autocomplete(
            opt: hikari.AutocompleteInteractionOption,
            inter: hikari.AutocompleteInteraction
    ) -> Union[
        str, Sequence[str], hikari.api.AutocompleteChoiceBuilder, Sequence[hikari.api.AutocompleteChoiceBuilder]]:
        regions = ["us", "eu", "kr", "tw", "cn"]
        choices = [hikari.CommandChoice(name=region, value=region) for region in regions]
        return choices

    @add_guild.autocomplete("channels")
    async def channels_autocomplete(
            opt: hikari.AutocompleteInteractionOption,
            inter: hikari.AutocompleteInteraction
    ) -> Union[
        str, Sequence[str], hikari.api.AutocompleteChoiceBuilder, Sequence[hikari.api.AutocompleteChoiceBuilder]]:
        config = read_json_file('config.json')
        channel_ids = config.get('channel_ids', {})
        channel_names = list(channel_ids.keys())

        # Find matches based on user input
        input_str = opt.value.lower()
        matches = [name for name in channel_names if input_str in name.lower()]

        # Create a list of autocomplete choices
        choices = [hikari.CommandChoice(name=name, value=name) for name in matches]

        # Respond with the matches
        return choices


def setup(bot):
    manage_logs_command(bot)
