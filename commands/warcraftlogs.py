from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
import hikari
import lightbulb
import requests
import json
import os
import os.path

from utils import read_json_file, hex_to_int, get_warcraft_logs_token, get_config

# Constants
LOGS_BASE_URL = "https://www.warcraftlogs.com/reports/"
THUMBNAIL_URL = "https://pbs.twimg.com/profile_images/1550453257947979784/U9D70T0S_400x400.jpg"


async def initialize_log_checks(bot):
    warcraft_logs_token = get_warcraft_logs_token()
    config = get_config()
    channel_ids = config['channel_ids']
    for name, source in config['log_sources'].items():
        formatted_url = f"{source['url']}?api_key={warcraft_logs_token}"
        color_int = hex_to_int(source['color'])
        channels = [channel_ids[ch] for ch in source['channels']]
        schedule_log_check(bot, name, formatted_url, f"logs/{source['filename']}", color_int, channels)


def schedule_log_check(bot, job_id, url, filename, color, channels):
    bot.d.sched.add_job(check_and_announce_logs, CronTrigger(minute="*/2"),
                        args=[url, filename, color, job_id, channels, bot],
                        misfire_grace_time=None, replace_existing=True, id=job_id)


def setup_warcraft_logs(bot):
    @bot.listen(hikari.StartedEvent)
    async def on_started(_: hikari.StartedEvent) -> None:
        await initialize_log_checks(bot)


async def check_and_announce_logs(url, filename, color, log_source_name, channels, bot):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.content
        first_log = json.loads(data)[0]
        logs_id = first_log['id']

        os.makedirs(os.path.dirname(filename), exist_ok=True)

        if not os.path.exists(filename):
            with open(filename, "w") as f:
                f.write("")

        with open(filename, "r") as f:
            previous_logs_id = f.read()

        if logs_id != previous_logs_id:
            await announce_new_logs(bot, first_log, logs_id, filename, color, log_source_name, channels)
        else:
            print(f"Latest logs has already been announced ID: {previous_logs_id}")

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

    with open(filename, "w") as f:
        f.write(logs_id)


def create_log_embed(title, owner, starttimeformatted, endtimeformatted, link, color, log_source_name):
    embed = hikari.Embed(title=f"New Warcraft Logs has been uploaded by {log_source_name}", color=color)
    embed.set_thumbnail(THUMBNAIL_URL)
    embed.add_field(name="Title:", value=f'{title}', inline=True)
    embed.add_field(name="Author:", value=f'{owner}', inline=True)
    embed.add_field(name="Log source:", value=f'{log_source_name}', inline=True)
    embed.add_field(name="Start time:", value=f'{starttimeformatted}', inline=True)
    embed.add_field(name="End time:", value=f'{endtimeformatted}', inline=True)
    embed.add_field(name="‎", value=f'‎', inline=True)
    embed.add_field(name="Link:", value=f'{link}', inline=False)
    return embed
