import hikari
import lightbulb
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import get_discord_token, get_config
from commands import setup
from dotenv import load_dotenv

load_dotenv()

bot = hikari.GatewayBot(
    token=get_discord_token(),
    # Slash commands + REST only; no privileged intents needed.
    intents=hikari.Intents.GUILDS,
)

client = lightbulb.client_from_app(
    bot,
    default_enabled_guilds=tuple(get_config().get("guild_ids", [])),
)

bot.subscribe(hikari.StoppingEvent, client.stop)

sched = AsyncIOScheduler()
client.di.registry_for(lightbulb.di.Contexts.DEFAULT).register_value(
    AsyncIOScheduler, sched
)


@bot.listen(hikari.StartingEvent)
async def on_starting(event: hikari.StartingEvent) -> None:
    sched.start()
    print("APScheduler started")
    await setup(client)  # load extensions first
    await client.start(event)  # then start the client so it syncs with commands already loaded


@bot.listen(hikari.StoppingEvent)
async def on_stopping(event: hikari.StoppingEvent) -> None:
    sched.shutdown(wait=False)


if __name__ == "__main__":
    bot.run()
