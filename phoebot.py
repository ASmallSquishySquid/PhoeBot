import discord
import os
from datetime import date

from discord.ext.commands import Bot

intents = discord.Intents.all()
bot = Bot(command_prefix="!", intents=intents)

@bot.event
async def on_ready():
    print("We have logged in as {0.user}".format(bot))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content.lower().startswith("hi"):
       await message.channel.send("Hello!")

@bot.command()
async def time(ctx):
    await ctx.send(date.today())
       

bot.run(os.getenv("BOT_TOKEN"))