import hikari
import lightbulb


def chesstv_command(bot):
    @bot.command
    @lightbulb.command("chesstv", "Lichess TV links of the major players")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def chesstv(ctx):
        embed = hikari.Embed(title="Lichess TVs of the major players.", color=0xEFDAB5)
        embed.add_field(name="Trollit team page", value=f'{"https://lichess.org/team/trollit"}', inline=False)
        embed.add_field(name="JP", value=f'{"https://lichess.org/@/loctifas/tv"}', inline=False)
        embed.add_field(name="Ossey", value=f'{"https://lichess.org/@/itZzosku/tv"}', inline=False)
        embed.add_field(name="Rippe", value=f'{"https://lichess.org/@/RIPPEROONI/tv"}', inline=False)
        embed.add_field(name="Valte", value=f'{"https://lichess.org/@/valdote/tv"}', inline=False)
        embed.add_field(name="Vallu", value=f'{"https://lichess.org/@/Intoilija/tv"}', inline=False)
        embed.add_field(name="Ietu", value=f'{"https://lichess.org/@/ietu66/tv"}', inline=False)
        await ctx.respond(embed=embed)


def setup(bot):
    chesstv_command(bot)
