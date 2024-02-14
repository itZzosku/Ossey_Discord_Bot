from typing import Union, Sequence
import hikari
import lightbulb
import json
from utils import read_json_file


def manage_channel_command(bot):
    @bot.command
    @lightbulb.command("managechannel", "Add or remove a channel")
    @lightbulb.implements(lightbulb.SlashCommandGroup)
    async def manage_channel(ctx):
        pass

    @manage_channel.child
    @lightbulb.option("channel_id", "The ID of the channel to add", type=int)
    @lightbulb.option("channel_name", "The name of the channel to add", type=str)
    @lightbulb.command("add", "Add a channel")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def add_channel(ctx):
        user_provided_name = ctx.options.channel_name
        channel_id = ctx.options.channel_id

        # Prepend 'channel_' to the user-provided name
        channel_name = f"channel_{user_provided_name}"

        # Read the current config
        config = read_json_file('config.json')

        # Add the channel with the modified name
        config['channel_ids'][channel_name] = channel_id

        # Write back to config
        with open('config.json', 'w') as file:
            json.dump(config, file, indent=4)

        response_message = f"Added channel '{channel_name}' with ID {channel_id}."
        await ctx.respond(response_message)
        print(response_message)  # Debugging output

    @manage_channel.child
    @lightbulb.option("channel_name", "The name of the channel to remove", type=str, autocomplete=True)
    @lightbulb.command("remove", "Remove a channel")
    @lightbulb.implements(lightbulb.SlashSubCommand)
    async def remove_channel(ctx):
        channel_name = ctx.options.channel_name

        # Read the current config
        config = read_json_file('config.json')

        # Remove the channel
        if channel_name in config['channel_ids']:
            del config['channel_ids'][channel_name]
            # Write back to config
            with open('config.json', 'w') as file:
                json.dump(config, file, indent=4)
            response_message = f"Removed channel '{channel_name}'."
            await ctx.respond(response_message)
            print(response_message)  # Debugging output
        else:
            response_message = f"Channel '{channel_name}' not found."
            await ctx.respond(response_message)
            print(response_message)  # Debugging output

    @remove_channel.autocomplete("channel_name")
    async def remove_channel_autocomplete(
            opt: hikari.AutocompleteInteractionOption,
            inter: hikari.AutocompleteInteraction
    ) -> Union[
        str, Sequence[str], hikari.api.AutocompleteChoiceBuilder, Sequence[hikari.api.AutocompleteChoiceBuilder]]:

        config = read_json_file('config.json')
        channel_ids = config['channel_ids']

        # Find matches based on user input
        input_str = opt.value.lower()
        matches = [name for name in channel_ids if input_str in name.lower()]

        # Create a list of autocomplete choices
        choices = [hikari.CommandChoice(name=name, value=name) for name in matches]

        # Respond with the matches
        return choices


def setup(bot):
    manage_channel_command(bot)
