import lightbulb

loader = lightbulb.Loader()


@loader.command
class Pong(lightbulb.SlashCommand, name="pong", description="Checks the bot is alive"):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond("Ping!")