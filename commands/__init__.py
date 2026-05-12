import lightbulb

async def setup(client: lightbulb.Client) -> None:
    await client.load_extensions(
        "commands.pong",
        "commands.telemetry",
        "commands.rating",
        "commands.roll",
        "commands.chesstv",
        "commands.managechannel",
        "commands.managelogs",
        "commands.warcraftlogs",
        "commands.reddit_tracker",
        "commands.guild_ranks",
    )
