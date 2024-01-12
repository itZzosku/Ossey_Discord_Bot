from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import hikari
import lightbulb
import aiohttp
import json
import os
import os.path

from utils import read_json_file, hex_to_int, get_warcraft_logs_token, get_config

# Constants
LOGS_BASE_URL = "https://www.warcraftlogs.com/reports/"
THUMBNAIL_URL = "https://pbs.twimg.com/profile_images/1550453257947979784/U9D70T0S_400x400.jpg"


def setup_warcraft_logs(bot):
    @bot.listen(hikari.StartedEvent)
    async def on_started(_: hikari.StartedEvent) -> None:
        await run_checks_once(bot)
        await initialize_log_checks(bot)


async def initialize_log_checks(bot):
    warcraft_logs_token = get_warcraft_logs_token()
    config = get_config()
    channel_ids = config['channel_ids']

    for name, source in config['log_sources'].items():
        formatted_url = f"{source['url']}?api_key={warcraft_logs_token}"
        color_int = hex_to_int(source['color'])
        channels = [channel_ids[ch] for ch in source['channels']]
        cron_schedule = source.get('cron_schedule', '*/5')  # Default to every 5 minutes if not specified
        schedule_log_check(bot, name, formatted_url, f"logs/{source['filename']}", color_int, channels, cron_schedule)


def schedule_log_check(bot, job_id, url, filename, color, channels, cron_schedule):
    bot.d.sched.add_job(check_and_announce_logs, CronTrigger(minute=cron_schedule),
                        args=[url, filename, color, job_id, channels, bot],
                        misfire_grace_time=None, replace_existing=True, id=job_id)


async def run_checks_once(bot):
    config = get_config()
    for name, source in config['log_sources'].items():
        formatted_url = f"{source['url']}?api_key={get_warcraft_logs_token()}"
        color_int = hex_to_int(source['color'])
        channels = [config['channel_ids'][ch] for ch in source['channels']]
        filename = f"logs/{source['filename']}"
        await check_and_announce_logs(formatted_url, filename, color_int, name, channels, bot)


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
    starttime = log['start']
    startimestring = str(starttime)[:-3]
    starttimeformatted = "<t:" + startimestring + ":R>"
    endtime = log['end']
    endtimestring = str(endtime)[:-3]
    endtimeformatted = "<t:" + endtimestring + ":R>"
    link = LOGS_BASE_URL + logs_id

    embed = create_log_embed(title, owner, starttimeformatted, endtimeformatted, link, color, log_source_name)

    for channel_id in channels:
        await bot.rest.create_message(channel_id, embed)

    # Read existing log IDs or initialize an empty list
    if os.path.exists(filename):
        with open(filename, "r") as f:
            previous_logs_ids = f.read().splitlines()
    else:
        previous_logs_ids = []

    # Add the new ID to the list and keep only the last 5
    previous_logs_ids.append(logs_id)
    with open(filename, "w") as f:
        f.writelines("\n".join(previous_logs_ids[-5:]))  # Save only the last 5 IDs


def create_log_embed(title, owner, starttimeformatted, endtimeformatted, link, color, log_source_name):
    embed = hikari.Embed(title=f"{log_source_name} has uploaded new Warcraft Logs", color=color)
    embed.set_thumbnail(THUMBNAIL_URL)
    embed.add_field(name="Title:", value=f'{title}', inline=True)
    embed.add_field(name="Author:", value=f'{owner}', inline=True)
    embed.add_field(name="Log source:", value=f'{log_source_name}', inline=True)
    embed.add_field(name="Start time:", value=f'{starttimeformatted}', inline=True)
    embed.add_field(name="End time:", value=f'{endtimeformatted}', inline=True)
    embed.add_field(name="‎", value=f'‎', inline=True)
    embed.add_field(name="Link:", value=f'{link}', inline=False)
    return embed
