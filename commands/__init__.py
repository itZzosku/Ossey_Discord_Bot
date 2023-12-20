from .pong import pong_command
from .telemetry import telemetry_command
from .rating import rating_command
from .roll import roll_command
from .chesstv import chesstv_command
from .managechannel import manage_channel_command
from .managelogs import manage_logs_command


def setup_commands(bot):
    bot.add_command(pong)
    bot.add_command(telemetry)
    bot.add_command(rating)
    bot.add_command(roll)
    bot.add_command(chesstv)
    bot.add_command(managechannel)
    bot.add_command(managelogs)
