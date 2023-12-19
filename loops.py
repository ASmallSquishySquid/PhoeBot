import aiohttp
import discord
import datetime

from discord.ext import commands
from discord.ext import tasks

class Loops(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @tasks.loop(minutes=15)
    async def sleepyTime(self):
        if (self.bot.phoebe.status==discord.Status.online):
            await self.bot.phoebe.send("Go to sleep! <:charmanderawr:837344550804127774>")

    @tasks.loop(minutes=30)
    async def drinkWater(self):
        if (self.bot.phoebe.status==discord.Status.online):
            await self.bot.phoebe.send("Drink some water! <:charmanderawr:837344550804127774>")

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

    # 8:30 AM
    @tasks.loop(time=datetime.time(hour=16, minute=30))
    async def apod(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY") as request:
                if request.status == 200:
                    js = await request.json()
                    embedMessage = discord.Embed(title=js["title"], description=js["explanation"], url=js["url"], color=discord.Color.og_blurple())
                    embedMessage.set_author(name="NASA")
                    if js["media_type"] == "image":
                        embedMessage.set_image(url=js["url"])
                    elif js["media_type"] == "video":
                        embedMessage.set_image(url=js["thumbnail_url"])
                    await self.bot.phoebe.send(embed=embedMessage)

async def setup(bot: commands.Bot):
    await bot.add_cog(Loops(bot))