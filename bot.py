import hikari
import lightbulb
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import read_json_file, get_discord_token

from commands.telemetry import setup as setup_telemetry
from commands.rating import setup as setup_rating
from commands.roll import setup as setup_roll
from commands.chesstv import setup as setup_chesstv
from commands.managechannel import setup as setup_manage_channel
from commands.managelogs import setup as setup_manage_logs
from commands.warcraftlogs import setup_warcraft_logs


token = get_discord_token()

bot = lightbulb.BotApp(
    token=token,
    prefix="/",
    intents=hikari.Intents.ALL,
    default_enabled_guilds=411182531254288385
)

# Setup commands
setup_telemetry(bot)
setup_rating(bot)
setup_roll(bot)
setup_chesstv(bot)
setup_manage_channel(bot)
setup_manage_logs(bot)

# Setup Warcraft Logs functionality
setup_warcraft_logs(bot)


@bot.listen(hikari.StartingEvent)
async def on_starting(_: hikari.StartingEvent) -> None:
    # This event fires once, while the BotApp is starting.
    bot.d.sched = AsyncIOScheduler()
    bot.d.sched.start()
    print("Bot has started!")


bot.run()
