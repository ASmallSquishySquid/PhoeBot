import datetime
import discord
import os
import sys
import traceback

from discord.ext import commands
from discord.ext.commands import Bot

from helpers.authorizedusers import AuthorizedUsers

sys.stdout = open("../phoebot_logs/{}.log".format(datetime.datetime.now().strftime("%m:%d:%Y-%H:%M")), 'w')
sys.stderr = sys.stdout

cogs = ["admin", "contextmenus", "crochet", "textcommands", "loops", "events", "reminders", "recipes"]

class PhoeBot(Bot):
    def __init__(self, command_prefix, intents: discord.Intents, activity):
        super().__init__(command_prefix=command_prefix, intents=intents, activity=activity, owner_id=int(os.getenv("SQIDJI_ID")))

bot = PhoeBot(command_prefix="!", intents=discord.Intents.all(), activity=discord.Activity(type=discord.ActivityType.watching, name="you 👀"))

@bot.event
async def on_ready():
    print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] We have logged in as {bot.user}", flush=True)
    AuthorizedUsers.startup()
    for cog in cogs:
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
        await ctx.reply("That's not a command <:charmanderawr:837344550804127774>")

    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send(f"{ctx.command} can not be used in DMs <:judgemental:748787284811186216>")

    elif isinstance(error, commands.NotOwner):
        await ctx.reply("You're not authorized to use that command <:charmanderawr:837344550804127774>")

    else:
        print(f"Ignoring exception in command {ctx.command}:", file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        sys.stderr.flush()


bot.run(os.getenv("BOT_TOKEN"))