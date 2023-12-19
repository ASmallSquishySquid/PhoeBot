import discord
import os

from discord.ext.commands import Bot

cogs = ["textcommands", "loops", "events"]

class PhoeBot(Bot):
    def __init__(self, command_prefix, intents: discord.Intents, activity):
        super().__init__(command_prefix=command_prefix, intents=intents, activity=activity)
    
       
bot = PhoeBot(command_prefix="!", intents=discord.Intents.all(), activity=discord.Activity(type=discord.ActivityType.watching, name="you 👀"))

@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))
    for cog in cogs:
        await bot.load_extension(cog)


bot.run(os.getenv("BOT_TOKEN"))