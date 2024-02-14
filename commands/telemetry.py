import hikari
import lightbulb
from influxdb_client import InfluxDBClient
import time
from datetime import datetime, timezone, timedelta
from utils import get_influxdb2_token


def telemetry_command(bot):
    influxdb2_token = get_influxdb2_token()

    @bot.command
    @lightbulb.command("telemetry", "Sends the telemetry of the room")
    @lightbulb.implements(lightbulb.SlashCommand)
    async def telemetry(ctx):
        client = InfluxDBClient(url="http://10.30.2.3:8087", token=influxdb2_token, org="myorg")

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


def setup(bot):
    telemetry_command(bot)
