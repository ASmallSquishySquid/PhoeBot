import sys
import discord
import os
import datetime

from discord.ext.commands import Bot

from helpers.authorizedusers import AuthorizedUsers

sys.stdout = open("../phoebot_logs/{}.log".format(datetime.datetime.now().strftime("%m:%d:%Y-%H:%M")), 'w')
sys.stderr = sys.stdout

cogs = ["textcommands", "loops", "events", "reminders"]

class PhoeBot(Bot):
    def __init__(self, command_prefix, intents: discord.Intents, activity):
        super().__init__(command_prefix=command_prefix, intents=intents, activity=activity, owner_id=274397067177361408)


bot = PhoeBot(command_prefix="!", intents=discord.Intents.all(), activity=discord.Activity(type=discord.ActivityType.watching, name="you 👀"))

@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
    for cog in cogs:
        await bot.load_extension("cogs." + cog)

@bot.check
async def blockUnauthorizedUsers(ctx: discord.ext.commands.Context):
    allowed = AuthorizedUsers.isAuthorized(ctx.author.id)
    if not allowed:
        await ctx.send(AuthorizedUsers.unauthorizedMessage)
    return allowed


bot.run(os.getenv("BOT_TOKEN"))