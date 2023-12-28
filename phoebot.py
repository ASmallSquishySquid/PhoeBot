import sys
import discord
import os
import datetime
import traceback

from discord.ext import commands
from discord.ext.commands import Bot

from helpers.authorizedusers import AuthorizedUsers

sys.stdout = open("../phoebot_logs/{}.log".format(datetime.datetime.now().strftime("%m:%d:%Y-%H:%M")), 'w')
sys.stderr = sys.stdout

cogs = ["textcommands", "loops", "events", "reminders"]

class PhoeBot(Bot):
    def __init__(self, command_prefix, intents: discord.Intents, activity):
        super().__init__(command_prefix=command_prefix, intents=intents, activity=activity, owner_id=int(os.getenv("SQIDJI_ID")))


bot = PhoeBot(command_prefix="!", intents=discord.Intents.all(), activity=discord.Activity(type=discord.ActivityType.watching, name="you 👀"))

@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
    AuthorizedUsers.startup()
    for cog in cogs:
        await bot.load_extension("cogs." + cog)

@bot.check
async def blockUnauthorizedUsers(ctx: discord.ext.commands.Context):
    if ctx.author == bot.user:
        return

    allowed = AuthorizedUsers.isAuthorized(ctx.author.id)
    if not allowed:
        await ctx.reply(AuthorizedUsers.unauthorizedMessage)
    return allowed

# Based on https://gist.github.com/EvieePy/7822af90858ef65012ea500bcecf1612
@bot.event
async def on_command_error(ctx, error):
    if hasattr(ctx.command, "on_error"):
        return

    cog = ctx.cog
    if cog and cog._get_overridden_method(cog.cog_command_error) is not None:
        return

    error = getattr(error, "original", error)

    if isinstance(error, commands.CommandNotFound):
        await ctx.reply("That's not a command <:charmanderawr:837344550804127774>")

    elif isinstance(error, commands.NoPrivateMessage):
        await ctx.send(f"{ctx.command} can not be used in DMs <:judgemental:748787284811186216>")

    else:
        print(f"Ignoring exception in command {ctx.command}:", file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)


bot.run(os.getenv("BOT_TOKEN"))