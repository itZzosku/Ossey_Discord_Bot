import lightbulb
import random

loader = lightbulb.Loader()


@loader.command
class Roll(lightbulb.SlashCommand, name="roll", description="Rolls a number between 1 and 999"):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        n = random.randint(1, 999)
        await ctx.respond(n)
