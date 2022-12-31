import hikari
import lightbulb
from decimal import Decimal
import lichess.api
import random
import requests
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger


def read_token():
    with open("token.txt", "r") as f:
        lines = f.readlines()
        return lines[0].strip()


def read_warcraftlogsurl():
    with open("token.txt", "r") as f:
        lines = f.readlines()
        return lines[1].strip()


token = read_token()

warcraftlogsurl = read_warcraftlogsurl()

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
    # This event fires once, when the BotApp is fully started.
    bot.d.sched.add_job(mightytsuulogs, CronTrigger(minute="*/1"))


async def mightytsuulogs() -> None:
    url = warcraftlogsurl
    logsdata = requests.get(url)
    data = logsdata.content
    with open('logsdata.json', 'wb') as f:
        f.write(data)

    myjsonfile = open('logsdata.json', 'r')
    jsondata = myjsonfile.read()

    jsondict = json.loads(jsondata)
    first = list(jsondict)[0]
    logsid = (first['id'])
    f = open("previouslogsid.txt", "r")
    previouslogsid = f.read()

    if logsid != previouslogsid:
        title = (first['title'])
        owner = (first['owner'])
        starttime = (first['start'])
        startimestring = str(starttime)
        startimestring = startimestring[:-3]
        starttimeformatted = "<t:" + startimestring + ":R>"
        endtime = (first['end'])
        endtimestring = str(endtime)
        endtimestring = endtimestring[:-3]
        endtimestring.replace(" ", "").rstrip(endtimestring[-3:]).upper()
        endtimeformatted = "<t:" + endtimestring + ":R>"
        link = "https://www.warcraftlogs.com/reports/" + logsid

        embed = hikari.Embed(title="New Warcraft Logs has been uploaded", color=0x521705)
        embed.set_thumbnail("https://pbs.twimg.com/profile_images/1550453257947979784/U9D70T0S_400x400.jpg")
        embed.add_field(name="Title:", value=f'{title}', inline=True)
        embed.add_field(name="Author:", value=f'{owner}', inline=True)
        embed.add_field(name="‎", value=f'‎', inline=True)
        embed.add_field(name="Start time:", value=f'{starttimeformatted}', inline=True)
        embed.add_field(name="End time:", value=f'{endtimeformatted}', inline=True)
        embed.add_field(name="‎", value=f'‎', inline=True)
        embed.add_field(name="Link:", value=f'{link}', inline=False)
        await bot.rest.create_message(718877818137739392, embed)

        print("Latest logs has been announced ID: " + logsid)
        f = open("previouslogsid.txt", "w")
        f.write(logsid)
        f.close()

    else:
        print("Latest logs has already been announced ID: " + previouslogsid)


@bot.command
@lightbulb.command("pong", "Says ping and checks that the bot is alive")
@lightbulb.implements(lightbulb.SlashCommand)
async def pong(ctx):
    await ctx.respond("Ping!")


@bot.command
@lightbulb.command("cat", "Sends a picture of a cat")
@lightbulb.implements(lightbulb.SlashCommand)
async def cat(ctx):
    url = 'https://aws.random.cat/meow'
    r = requests.get(url)
    r_dict = r.json()
    await ctx.respond(r_dict['file'])


@bot.command
@lightbulb.command("telemetry", "Sends the telemetry of the room")
@lightbulb.implements(lightbulb.SlashCommand)
async def telemetry(ctx):
    url = 'https://osseyman.duckdns.org/Latest_Measurements.json'
    r = requests.get(url)
    r_temp = r.json()
    sensor = (r_temp['Sensor'])
    temperaturelong = Decimal(r_temp['Temperature'])
    humiditylong = Decimal(r_temp['Humidity'])
    pressurelong = Decimal(r_temp['Pressure'])

    timestamp_string = (r_temp['Time'])
    timestamp_string_formatted = "<t:" + timestamp_string + ":R>"

    temperature = round(temperaturelong, 1)
    humidity = round(humiditylong, 0)
    pressure = round(pressurelong, 2)

    embed = hikari.Embed(title="Telemetry from Osseys place", color=0xbc0057)
    embed.add_field(name="Sensor:", value=f'{sensor}', inline=False)
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


@bot.command
@lightbulb.command("jp", "Link to JP")
@lightbulb.implements(lightbulb.SlashCommand)
async def jp(ctx):
    await ctx.respond("https://vitsionline.com/jp.jpg")


bot.run()
