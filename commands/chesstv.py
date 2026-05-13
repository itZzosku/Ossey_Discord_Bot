import hikari
import lightbulb

loader = lightbulb.Loader()

@loader.command
class ChessTV(lightbulb.SlashCommand, name="chesstv", description="Lichess TV links of the major players"):
    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        embed = hikari.Embed(title="Lichess TVs of the major players.", color=0xEFDAB5)
        embed.add_field(name="Trollit team page", value="https://lichess.org/team/trollit", inline=False)
        embed.add_field(name="JP", value="https://lichess.org/@/loctifas/tv", inline=False)
        embed.add_field(name="Ossey", value="https://lichess.org/@/itZzosku/tv", inline=False)
        embed.add_field(name="Rippe", value="https://lichess.org/@/RIPPEROONI/tv", inline=False)
        embed.add_field(name="Valte", value="https://lichess.org/@/valdote/tv", inline=False)
        embed.add_field(name="Vallu", value="https://lichess.org/@/Intoilija/tv", inline=False)
        embed.add_field(name="Ietu", value="https://lichess.org/@/ietu66/tv", inline=False)
        await ctx.respond(embed=embed)
