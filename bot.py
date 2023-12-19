import os.path
import hikari
import lightbulb
from decimal import Decimal
import lichess.api
import random
import requests
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from influxdb_client import InfluxDBClient, Point, Dialect
from influxdb_client.client.write_api import SYNCHRONOUS
import time
from datetime import datetime, timezone, timedelta

# Constants
LOGS_BASE_URL = "https://www.warcraftlogs.com/reports/"
THUMBNAIL_URL = "https://pbs.twimg.com/profile_images/1550453257947979784/U9D70T0S_400x400.jpg"


def read_json_file(filename):
    with open(filename, 'r') as file:
        return json.load(file)


# Read the configuration and tokens
config = read_json_file('config.json')
tokens = read_json_file('token.json')

# Assign variables from the JSON files
token = tokens['token']
influxdb2_token = tokens['influxdb2_token']
warcraft_logs_token = tokens['warcraft_logs_token']

bot = lightbulb.BotApp(
    token=token,
    prefix="/",
    intents=hikari.Intents.ALL,
    default_enabled_guilds=411182531254288385
)


@bot.listen(hikari.StartingEvent)
async def on_starting(_: hikari.StartingEvent) -> None:
    # This event fires once, while the BotApp is starting.
    bot.d.sched = AsyncIOScheduler()
    bot.d.sched.start()
    print("Bot has started!")


@bot.listen(hikari.StartedEvent)
async def on_started(_: hikari.StartedEvent) -> None:
    for name, source in config['log_sources'].items():
        formatted_url = f"{source['url']}?api_key={warcraft_logs_token}"
        color_int = int(source['color'].lstrip('#'), 16)
        schedule_log_check(name, formatted_url, f"logs/{source['filename']}", color_int)


def schedule_log_check(job_id, url, filename, color):
    bot.d.sched.add_job(check_and_announce_logs, CronTrigger(minute="*/2"),
                        args=[url, filename, color, job_id],
                        misfire_grace_time=None, id=job_id)


def hex_to_int(hex_color):
    return int(hex_color.lstrip('#'), 16)


async def check_and_announce_logs(url, filename, color, log_source_name):
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
            await announce_new_logs(first_log, logs_id, filename, color, log_source_name)
        else:
            print(f"Latest logs has already been announced ID: {previous_logs_id}")

    except Exception as e:
        print(f"Error occurred: {e}")


async def announce_new_logs(log, logs_id, filename, color, log_source_name):
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

    for channel_id in config['channel_ids'].values():
        await bot.rest.create_message(channel_id, embed)

    with open(filename, "w") as f:
        f.write(logs_id)


def create_log_embed(title, owner, starttimeformatted, endtimeformatted, link, color, log_source_name):
    embed = hikari.Embed(title="New Warcraft Logs has been uploaded", color=color)
    embed.set_thumbnail(THUMBNAIL_URL)
    embed.add_field(name="Title:", value=f'{title}', inline=True)
    embed.add_field(name="Author:", value=f'{owner}', inline=True)
    embed.add_field(name="Log source:", value=f'{log_source_name}', inline=True)
    embed.add_field(name="Start time:", value=f'{starttimeformatted}', inline=True)
    embed.add_field(name="End time:", value=f'{endtimeformatted}', inline=True)
    embed.add_field(name="‎", value=f'‎', inline=True)
    embed.add_field(name="Link:", value=f'{link}', inline=False)
    return embed


@bot.command
@lightbulb.command("pong", "Says ping and checks that the bot is alive")
@lightbulb.implements(lightbulb.SlashCommand)
async def pong(ctx):
    await ctx.respond("Ping!")


@bot.command
@lightbulb.command("telemetry", "Sends the telemetry of the room")
@lightbulb.implements(lightbulb.SlashCommand)
async def telemetry(ctx):
    client = InfluxDBClient(url="http://192.168.1.22:8087", token=influxdb2_token, org="myorg")

    # Get the query API
    query_api = client.query_api()

    # Define the Flux query
    # Here, I've replaced v.windowPeriod with a literal duration value '1m' for aggregateWindow function.
    flux_query = '''
        from(bucket: "House Telemetry")
        |> range(start: -60m)
        |> filter(fn: (r) => r["_measurement"] == "ESP32")
        |> filter(fn: (r) => r["Name"] == "Telemetry")
        |> filter(fn: (r) => r["_field"] == "Pressure" or r["_field"] == "Humidity" or r["_field"] == "Sensor" or r["_field"] == "Temperature")
        |> aggregateWindow(every: 10s, fn: last, createEmpty: false)
        |> last()
        '''

    # Execute the query
    tables = query_api.query(flux_query)

    # Variables to hold the last values of each field, including the timestamp
    last_timestamp = None
    last_temperature = None
    last_pressure = None
    last_humidity = None
    last_sensor = None
    timestamp_string = None

    # Iterate through the tables
    for table in tables:
        # Iterate through the records in each table
        for record in table.records:
            # Extract the field and value
            field = record.get_field()
            value = record.get_value()
            time_obj = record.get_time()

            # Convert and store the value based on the field type
            if field == 'Temperature':
                last_temperature = float(value) if value is not None else None
            elif field == 'Pressure':
                last_pressure = float(value) if value is not None else None
            elif field == 'Humidity':
                last_humidity = float(value) if value is not None else None
            elif field == 'Sensor':
                last_sensor = str(value) if value is not None else None

            # Store the timestamp as an integer (seconds since epoch)
            if time_obj:
                last_timestamp = int(time.mktime(time_obj.timetuple()))

    # Close the client
    client.close()

    # Convert the timestamp to UTC
    if last_timestamp is not None:
        # Replace 'your_timezone_offset' with your actual timezone offset
        # For example, if your timezone is UTC+2, use timedelta(hours=2)
        your_timezone_offset = timedelta(hours=-2)  # Adjust this to your timezone offset
        local_time = datetime.fromtimestamp(last_timestamp, timezone.utc) - your_timezone_offset
        utc_timestamp = int(local_time.replace(tzinfo=timezone.utc).timestamp())

        timestamp_string_formatted = f"<t:{utc_timestamp}:R>"
    else:
        timestamp_string_formatted = "N/A"

    temperature = round(last_temperature, 1)
    humidity = round(last_humidity, 0)
    pressure = round(last_pressure, 2)

    embed = hikari.Embed(title="Telemetry from Osseys place", color=0xbc0057)
    embed.add_field(name="Sensor:", value=f'{last_sensor}', inline=False)
    embed.add_field(name="Temperature:", value=f'{temperature} °C', inline=True)
    embed.add_field(name="Humidity:", value=f'{humidity} %', inline=True)
    embed.add_field(name="Pressure:", value=f'{pressure} hPa', inline=True)
    embed.add_field(name="Time from measurement:", value=f'{timestamp_string_formatted}', inline=False)
    await ctx.respond(embed=embed)


@bot.command
@lightbulb.option("player", "Name of the player", type=str, required=True)
@lightbulb.command("rating", "Sends the Lichess rating of the player")
@lightbulb.implements(lightbulb.SlashCommand)
async def rating(ctx):
    user1 = lichess.api.user(ctx.options.player)
    blitz_rating1 = (user1['perfs']['blitz']['rating'])
    blitz_games1 = (user1['perfs']['blitz']['games'])
    rapid_rating1 = (user1['perfs']['rapid']['rating'])
    rapid_games1 = (user1['perfs']['rapid']['games'])
    puzzle_rating1 = (user1['perfs']['puzzle']['rating'])
    puzzle_games1 = (user1['perfs']['puzzle']['games'])

    embed = hikari.Embed(title=f'Ratings of the player {ctx.options.player}.', color=0xbc0057)
    embed.add_field(name="Blitz:", value=f'**Rating:** {blitz_rating1} **Games:** {blitz_games1}', inline=False)
    embed.add_field(name="Rapid:", value=f'**Rating:** {rapid_rating1} **Games:** {rapid_games1}', inline=False)
    embed.add_field(name="Puzzle:", value=f'**Rating:** {puzzle_rating1} **Puzzles:** {puzzle_games1}', inline=False)
    await ctx.respond(embed=embed)


@bot.command
@lightbulb.command("roll", "rolls a number between 1 and 999")
@lightbulb.implements(lightbulb.SlashCommand)
async def roll(ctx):
    n = random.randint(1, 999)
    await ctx.respond(n)


@bot.command
@lightbulb.command("chesstv", "Lichess TV links of the major players")
@lightbulb.implements(lightbulb.SlashCommand)
async def chesstv(ctx):
    embed = hikari.Embed(title="Lichess TVs of the major players.", color=0xEFDAB5)
    embed.add_field(name="Trollit team page", value=f'{"https://lichess.org/team/trollit"}', inline=False)
    embed.add_field(name="JP", value=f'{"https://lichess.org/@/loctifas/tv"}', inline=False)
    embed.add_field(name="Ossey", value=f'{"https://lichess.org/@/itZzosku/tv"}', inline=False)
    embed.add_field(name="Rippe", value=f'{"https://lichess.org/@/RIPPEROONI/tv"}', inline=False)
    embed.add_field(name="Valte", value=f'{"https://lichess.org/@/valdote/tv"}', inline=False)
    embed.add_field(name="Vallu", value=f'{"https://lichess.org/@/Intoilija/tv"}', inline=False)
    embed.add_field(name="Ietu", value=f'{"https://lichess.org/@/ietu66/tv"}', inline=False)
    await ctx.respond(embed=embed)


bot.run()
