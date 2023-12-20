import lightbulb


def pong_command(bot):
    @bot.command
    @lightbulb.command("pong", "Responds with Ping!")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def pong(ctx):
        await ctx.respond("Ping!")


def setup(bot):
    pong_command(bot)
