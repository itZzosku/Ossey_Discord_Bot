import lightbulb
import random


def roll_command(bot):
    @bot.command
    @lightbulb.command("roll", "rolls a number between 1 and 999")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def roll(ctx):
        n = random.randint(1, 999)
        await ctx.respond(n)


def setup(bot):
    roll_command(bot)
