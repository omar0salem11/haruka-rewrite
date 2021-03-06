from settings import *
from discord.ext import commands


@bot.command(
    name = "pause",
    description = "Pause the playing audio",
)
@commands.cooldown(1, 5, commands.BucketType.guild)
async def _pause(cmd):
    player = bot.node.get_player(cmd.guild)
    if player and player.is_playing:
        await player.pause()
        await cmd.send("Paused audio.")
    else:
        await cmd.send("No audio currently playing to pause.")