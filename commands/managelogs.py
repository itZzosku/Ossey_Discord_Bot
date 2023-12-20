from typing import Union, Sequence
import hikari
import lightbulb
import json
from utils import read_json_file


def manage_logs_command(bot):
    @bot.command
    @lightbulb.command("managelogs", "Add or remove log sources")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def manage_logs(ctx):
        pass

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


def setup(bot):
    manage_logs_command(bot)
