import lightbulb


async def setup(client: lightbulb.Client) -> None:
    await client.load_extensions(
        "commands.pong",
        "commands.rating",
        "commands.roll",
        "commands.chesstv",
        "commands.warcraftlogs",
        "commands.reddit_tracker",
    )
