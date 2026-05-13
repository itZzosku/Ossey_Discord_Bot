import hikari
import lightbulb
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import get_discord_token
from commands import setup
from dotenv import load_dotenv

load_dotenv()

bot = hikari.GatewayBot(
    token=get_discord_token(),
    intents=hikari.Intents.ALL,
)

client = lightbulb.client_from_app(
    bot,
    default_enabled_guilds=(411182531254288385, 117961133083721731, 1216424565136298025,),
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


bot.run()
