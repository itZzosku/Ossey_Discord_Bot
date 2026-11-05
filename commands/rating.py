from urllib.parse import quote

import aiohttp
import hikari
import lightbulb

LICHESS_USER_URL = "https://lichess.org/api/user/{}"

loader = lightbulb.Loader()


def format_perf(perfs: dict, key: str, count_label: str = "Games") -> str:
    perf = perfs.get(key)
    if not perf:
        return "No rated games"
    return f"**Rating:** {perf.get('rating', 'N/A')} **{count_label}:** {perf.get('games', 0)}"


@loader.command
class Rating(
    lightbulb.SlashCommand,
    name="rating",
    description="Sends the Lichess rating of the player",
):
    player = lightbulb.string("player", "Name of the player")

    @lightbulb.invoke
    async def invoke(self, ctx: lightbulb.Context) -> None:
        url = LICHESS_USER_URL.format(quote(self.player, safe=""))
        try:
            async with aiohttp.ClientSession(timeout=aiohttp.ClientTimeout(total=10)) as session:
                async with session.get(url, headers={"Accept": "application/json"}) as response:
                    if response.status == 404:
                        await ctx.respond(f"Player `{self.player}` not found on Lichess.")
                        return
                    response.raise_for_status()
                    user = await response.json()
        except (aiohttp.ClientError, TimeoutError) as e:
            print(f"[Lichess] Request failed for {self.player}: {type(e).__name__}")
            await ctx.respond("Couldn't reach Lichess right now, try again later.")
            return

        if user.get("disabled"):
            await ctx.respond(f"Player `{self.player}` has closed their Lichess account.")
            return

        perfs = user.get("perfs", {})
        name = user.get("username", self.player)

        embed = hikari.Embed(title=f"Ratings of the player {name}.", color=0xbc0057)
        embed.add_field(name="Blitz:", value=format_perf(perfs, "blitz"), inline=False)
        embed.add_field(name="Rapid:", value=format_perf(perfs, "rapid"), inline=False)
        embed.add_field(name="Puzzle:", value=format_perf(perfs, "puzzle", "Puzzles"), inline=False)

        await ctx.respond(embed=embed)
