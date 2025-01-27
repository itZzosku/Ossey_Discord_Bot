import hikari
import lightbulb
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from utils import get_discord_token

from commands.telemetry import setup as setup_telemetry
from commands.rating import setup as setup_rating
from commands.roll import setup as setup_roll
from commands.chesstv import setup as setup_chesstv
from commands.managechannel import setup as setup_manage_channel
from commands.managelogs import setup as setup_manage_logs
from commands.warcraftlogs import setup_warcraft_logs

# Import your new reddit_tracker setup
from commands.reddit_tracker import setup_reddit_tracker
from dotenv import load_dotenv

load_dotenv()  # now os.getenv will see those variables

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
setup_warcraft_logs(bot)


# Initialize the shared APScheduler instance once
@bot.listen(hikari.StartingEvent)
async def on_starting(_: hikari.StartingEvent) -> None:
    bot.d.sched = AsyncIOScheduler()
    bot.d.sched.start()
    print("Bot has started, APScheduler is running...")


# Now call your reddit_tracker setup
setup_reddit_tracker(bot)

bot.run()
