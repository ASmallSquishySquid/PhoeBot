from datetime import datetime
import os
import sys
import traceback

import discord
from discord.ext import commands
from discord.ext.commands import Bot

from helpers import constants
from helpers.authorizedusers import AuthorizedUsers

sys.stdout = open(
    file=f"../phoebot_logs/{datetime.now().strftime('%m:%d:%Y-%H:%M')}.log",
    mode="w",
    encoding="utf-8")
sys.stderr = sys.stdout

class PhoeBot(Bot):
    def __init__(self, command_prefix, intents: discord.Intents, activity):
        super().__init__(
            command_prefix=command_prefix,
            intents=intents,
            activity=activity,
            owner_id=int(os.getenv(constants.OWNER_ENV)))

bot = PhoeBot(
    command_prefix="!",
    intents=discord.Intents.all(),
    activity=constants.DEFAULT_ACTIVITY)

@bot.event
async def on_ready():
    print(
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] We have logged in as {bot.user}",
        flush=True)
    AuthorizedUsers.startup()
    for cog in constants.COGS:
        await bot.load_extension("cogs." + cog)

@bot.check
async def block_unauthorized_users(ctx: discord.ext.commands.Context):
    if ctx.author == bot.user:
        return

    allowed = AuthorizedUsers.is_authorized(ctx.author.id)
    if not allowed:
        await ctx.reply(AuthorizedUsers.UNAUTHORIZED_MESSAGE)
    return allowed

# Based on https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612
@bot.event
async def on_command_error(ctx, error):
    command = ctx.command
    if command and command.has_error_handler():
        return

    cog = ctx.cog
    if cog and cog.has_error_handler():
        return

    error = getattr(error, "original", error)

    if isinstance(error, commands.CommandNotFound):
        await ctx.reply(f"That's not a command {constants.DEFAULT_EMOTE}")

    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send(f"{ctx.command} can not be used in DMs <:judgemental:748787284811186216>")

    elif isinstance(error, commands.NotOwner):
        await ctx.reply(f"You're not authorized to use that command {constants.DEFAULT_EMOTE}")

    else:
        print(
            f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ignoring exception in command {ctx.command}:",
            file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        sys.stderr.flush()


bot.run(os.getenv("BOT_TOKEN"))
