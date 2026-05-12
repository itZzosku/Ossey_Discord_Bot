import hikari
import lightbulb
import lichess.api


def rating_command(bot):
    @bot.command
    @lightbulb.option("player", "Name of the player", type=str, required=True)
    @lightbulb.command("rating", "Sends the Lichess rating of the player")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def rating(ctx):
        user1 = lichess.api.user(ctx.options.player)
        blitz_rating1 = (user1['perfs']['blitz']['rating'])
        blitz_games1 = (user1['perfs']['blitz']['games'])
        rapid_rating1 = (user1['perfs']['rapid']['rating'])
        rapid_games1 = (user1['perfs']['rapid']['games'])
        puzzle_rating1 = (user1['perfs']['puzzle']['rating'])
        puzzle_games1 = (user1['perfs']['puzzle']['games'])

        embed = hikari.Embed(title=f'Ratings of the player {ctx.options.player}.', color=0xbc0057)
        embed.add_field(name="Blitz:", value=f'**Rating:** {blitz_rating1} **Games:** {blitz_games1}', inline=False)
        embed.add_field(name="Rapid:", value=f'**Rating:** {rapid_rating1} **Games:** {rapid_games1}', inline=False)
        embed.add_field(name="Puzzle:", value=f'**Rating:** {puzzle_rating1} **Puzzles:** {puzzle_games1}',
                        inline=False)
        await ctx.respond(embed=embed)


def setup(bot):
    rating_command(bot)
