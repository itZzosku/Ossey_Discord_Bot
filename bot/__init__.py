import asyncio
import os
import types
from dotenv import load_dotenv
import hikari
import lightbulb

from bot.extensions.warcraftlogs import initialize_log_checks
from utils import get_discord_token  # your helper to read token
from bot import extensions  # your commands/extensions package
import apscheduler.schedulers.asyncio

load_dotenv()

token = get_discord_token()


class MyBot(hikari.GatewayBot):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.d = types.SimpleNamespace()


bot = MyBot(token)

client = lightbulb.client_from_app(bot)


@bot.listen(hikari.StartedEvent)
async def on_started(event):
    # Setup the scheduler first
    bot.d.sched = apscheduler.schedulers.asyncio.AsyncIOScheduler()
    bot.d.sched.start()

    # Now initialize your log checks, which will use bot.d.sched
    await initialize_log_checks(bot)


async def main():
    await bot.start()  # Start the GatewayBot event loop


if __name__ == "__main__":
    asyncio.run(main())
