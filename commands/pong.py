import lightbulb

loader = lightbulb.Loader()

@loader.command
class Pong(lightbulb.SlashCommand, name="pong", description="Responds with Ping!"):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        await ctx.respond("Ping!")
