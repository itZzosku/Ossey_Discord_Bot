from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import hikari
import lightbulb
import aiohttp
import os
import os.path
import asyncio
from utils import hex_to_int, get_warcraft_logs_token, get_config

LOGS_BASE_URL = "https://www.warcraftlogs.com/reports/"
THUMBNAIL_URL = "https://pbs.twimg.com/profile_images/1550453257947979784/U9D70T0S_400x400.jpg"

loader = lightbulb.Loader()


@loader.listener(hikari.StartedEvent)
async def on_started(event: hikari.StartedEvent, bot: hikari.GatewayBot, sched: AsyncIOScheduler) -> None:
    await run_checks_once(bot)
    await initialize_log_checks(bot, sched)


async def initialize_log_checks(bot: hikari.GatewayBot, sched: AsyncIOScheduler):
    warcraft_logs_token = get_warcraft_logs_token()
    config = get_config()
    channel_ids = config['channel_ids']

    for name, source in config['log_sources'].items():
        formatted_url = f"{source['url']}?api_key={warcraft_logs_token}"
        color_int = hex_to_int(source['color'])
        channels = [channel_ids[ch] for ch in source['channels']]
        cron_schedule = source.get('cron_schedule', '*/5')

        sched.add_job(
            check_and_announce_logs,
            CronTrigger.from_crontab(cron_schedule),
            args=[formatted_url, f"logs/{source['filename']}", color_int, name, channels, bot],
            misfire_grace_time=None,
            replace_existing=True,
            id=name
        )


async def run_checks_once(bot: hikari.GatewayBot):
    config = get_config()
    semaphore = asyncio.Semaphore(config.get("log_check_concurrency", 5))

    async def sem_check(source_name, source_info):
        async with semaphore:
            formatted_url = f"{source_info['url']}?api_key={get_warcraft_logs_token()}"
            color_int = hex_to_int(source_info['color'])
            channels = [config['channel_ids'][ch] for ch in source_info['channels']]
            filename = f"logs/{source_info['filename']}"
            await check_and_announce_logs(formatted_url, filename, color_int, source_name, channels, bot)

    await asyncio.gather(*(sem_check(name, source) for name, source in config['log_sources'].items()))


async def check_and_announce_logs(url, filename, color, log_source_name, channels, bot):
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                response.raise_for_status()
                data = await response.json()
                first_log = data[0]
                logs_id = first_log['id']

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        previous_logs_ids = []
        if os.path.exists(filename):
            with open(filename, "r") as f:
                previous_logs_ids = f.read().splitlines()

        if logs_id not in previous_logs_ids:
            await announce_new_logs(bot, first_log, logs_id, filename, color, log_source_name, channels)
        else:
            print(f"Latest logs have already been announced ID: {logs_id}")

    except aiohttp.ClientError as e:
        print(f"HTTP request error: {e}")
    except Exception as e:
        print(f"Error occurred: {e}")


async def announce_new_logs(bot, log, logs_id, filename, color, log_source_name, channels):
    title = log['title']
    owner = log['owner']
    starttimeformatted = f"<t:{str(log['start'])[:-3]}:R>"
    endtimeformatted = f"<t:{str(log['end'])[:-3]}:R>"
    link = LOGS_BASE_URL + logs_id

    embed = create_log_embed(title, owner, starttimeformatted, endtimeformatted, link, color, log_source_name)

    for channel_id in channels:
        await bot.rest.create_message(channel_id, embed)

    previous_logs_ids = []
    if os.path.exists(filename):
        with open(filename, "r") as f:
            previous_logs_ids = f.read().splitlines()

    previous_logs_ids.append(logs_id)
    with open(filename, "w") as f:
        f.writelines("\n".join(previous_logs_ids[-5:]))


def create_log_embed(title, owner, starttimeformatted, endtimeformatted, link, color, log_source_name):
    embed = hikari.Embed(title=f"{log_source_name} has uploaded new Warcraft Logs", color=color)
    embed.set_thumbnail(THUMBNAIL_URL)
    embed.add_field(name="Title:", value=title, inline=True)
    embed.add_field(name="Author:", value=owner, inline=True)
    embed.add_field(name="Log source:", value=log_source_name, inline=True)
    embed.add_field(name="Start time:", value=starttimeformatted, inline=True)
    embed.add_field(name="End time:", value=endtimeformatted, inline=True)
    embed.add_field(name="‎", value="‎", inline=True)
    embed.add_field(name="Link:", value=link, inline=False)
    return embed
