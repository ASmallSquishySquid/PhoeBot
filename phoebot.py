import discord
import os
import datetime

from discord.ext.commands import Bot
from discord.ext.commands import Context
from discord.ext import tasks

class PhoeBot(Bot):
    def __init__(self, command_prefix, intents: discord.Intents, activity):
        super().__init__(command_prefix=command_prefix, intents=intents, activity=activity)

    @tasks.loop(minutes=15)
    async def sleepyTime(self):
        if (self.phoebe.status==discord.Status.online):
            await self.phoebe.send("Go to sleep! <:charmanderawr:837344550804127774>")

    @tasks.loop(minutes=30)
    async def drinkWater(self):
        if (self.phoebe.status==discord.Status.online):
            await self.phoebe.send("Drink some water! <:charmanderawr:837344550804127774>")

    # 11:30 PM
    @tasks.loop(time=datetime.time(hour=7, minute=30))
    async def bedtime(self):
        await self.sleepyTime.start()
        await self.drinkWater.cancel()

    # 9:00 AM
    @tasks.loop(time=datetime.time(hour=17, minute=0))
    async def morning(self):
        await self.sleepyTime.cancel()
        await self.drinkWater.start()
    
       
bot = PhoeBot(command_prefix="!", intents=discord.Intents.all(), activity=discord.Activity(type=discord.ActivityType.watching, name="you 👀"))


@bot.event
async def on_ready():
    bot.bedtime.start()
    bot.morning.start()
    bot.drinkWater.start()
    bot.guild = bot.get_guild(712909571622043728)
    bot.phoebe = bot.guild.get_member(274397067177361408)
    print("We have logged in as {0.user}".format(bot))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.content.lower().startswith("hi") or message.content.lower().startswith("hello") :
        await message.reply("Hello! <:charmanderawr:837344550804127774>", mention_author=True)

    await bot.process_commands(message)

@bot.command()
async def date(ctx: Context):
    await ctx.send("Today is " + str(datetime.date.today().strftime('%m/%d/%Y')) + " <:charmanderawr:837344550804127774>")

@bot.command()
async def heh(ctx: Context):
    josie = bot.guild.get_member(559828298973184011)
    await josie.send("Boop <a:mmaPokeAnnoyLove:764772302680227890>")


bot.run(os.getenv("BOT_TOKEN"))