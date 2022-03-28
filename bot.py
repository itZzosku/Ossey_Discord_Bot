import hikari
import lightbulb
import requests
import datetime
from decimal import Decimal
import lichess.api
import random


def read_token():
    with open("token.txt", "r") as f:
        lines = f.readlines()
        return lines[0].strip()


token = read_token()

bot = lightbulb.BotApp(
    token=token,
    prefix="/",
    default_enabled_guilds=(411182531254288385)
)


@bot.listen(hikari.StartedEvent)
async def on_stared(event):
    print("Bot has started!")


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
    timestamp_object = int(timestamp_string)

    cutime = datetime.datetime.now()
    seconds_since_epoch = int(cutime.timestamp())

    dtime = seconds_since_epoch - timestamp_object

    temperature = round(temperaturelong, 1)
    humidity = round(humiditylong, 0)
    pressure = round(pressurelong, 2)

    embed = hikari.Embed(title="Telemetry from Osseys place", color=0xbc0057)
    embed.add_field(name="Sensor:", value=f'{sensor}', inline=False)
    embed.add_field(name="Temperature:", value=f'{temperature} °C', inline=True)
    embed.add_field(name="Humidity:", value=f'{humidity} %', inline=True)
    embed.add_field(name="Pressure:", value=f'{pressure} hPa', inline=True)
    embed.add_field(name="Time from measurement:", value=f'{dtime} Seconds', inline=False)
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
