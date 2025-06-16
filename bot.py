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
from commands.reddit_tracker import setup_reddit_tracker
from commands.guild_ranks import setup_guild_rank_tracker

from dotenv import load_dotenv

load_dotenv()

token = get_discord_token()

bot = lightbulb.BotApp(
    token=get_discord_token(),
    prefix="/",
    intents=hikari.Intents.ALL,
    default_enabled_guilds=411182531254288385,
)

if not hasattr(bot, "d") or bot.d is None:
    bot.d = type('', (), {})()

bot.d.sched = AsyncIOScheduler()


@bot.listen(hikari.StartingEvent)
async def on_starting(event):
    # Now event loop is running, start scheduler here
    bot.d.sched.start()
    print("APScheduler started")

    # Setup jobs here or before starting bot (safe if scheduler started now)
    # If your setup functions require scheduler started, you can call them here or earlier but schedule jobs after start
    # For example, you can move setup_guild_rank_tracker(bot) here if it adds jobs

# Setup your commands, etc.
# But don't call sched.start() yet — it will be started in the event listener
setup_telemetry(bot)
setup_rating(bot)
setup_roll(bot)
setup_chesstv(bot)
setup_manage_channel(bot)
setup_manage_logs(bot)
setup_warcraft_logs(bot)
setup_reddit_tracker(bot)
setup_guild_rank_tracker(bot)

bot.run()
