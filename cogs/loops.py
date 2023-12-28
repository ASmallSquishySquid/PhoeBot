import os
import aiohttp
import discord
import datetime

from discord.ext import commands
from discord.ext import tasks

class Loops(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bedtime.start()
        self.morning.start()
        self.apod.start()

        if not (datetime.datetime.now() > datetime.datetime.now().replace(hour=9, minute=0, second=0) and datetime.datetime.now() < datetime.datetime.now().replace(hour=23, minute=30, second=0)):
            self.sleepyTime.start()
        else:
            self.drinkWater.start()

    @tasks.loop(minutes=15)
    async def sleepyTime(self):
        guildId = int(os.getenv("DUCK_SERVER_ID"))
        guild = self.bot.get_guild(guildId)
        if guild is None:
            guild = await self.bot.fetch_guild(guildId)

        userId = int(os.getenv("SQIDJI_ID"))
        sqidji = guild.get_member(userId)
        if sqidji is None:
            sqidji = await guild.fetch_member(userId)

        if (sqidji.status==discord.Status.online):
            await sqidji.send("Go to sleep! <:charmanderawr:837344550804127774>")

    @tasks.loop(minutes=30)
    async def drinkWater(self):
        guildId = int(os.getenv("DUCK_SERVER_ID"))
        guild = self.bot.get_guild(guildId)
        if guild is None:
            guild = await self.bot.fetch_guild(guildId)

        userId = int(os.getenv("SQIDJI_ID"))
        sqidji = guild.get_member(userId)
        if sqidji is None:
            sqidji = await guild.fetch_member(userId)

        if (sqidji.status==discord.Status.online):
            await sqidji.send("Drink some water! <:charmanderawr:837344550804127774>")

    # 11:30 PM
    @tasks.loop(time=datetime.time(hour=7, minute=30))
    async def bedtime(self):
        self.sleepyTime.start()
        self.drinkWater.cancel()

    # 9:00 AM
    @tasks.loop(time=datetime.time(hour=17, minute=0))
    async def morning(self):
        self.sleepyTime.cancel()
        self.drinkWater.start()

    # 8:30 AM
    @tasks.loop(time=datetime.time(hour=16, minute=30))
    async def apod(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY") as request:
                if request.status == 200:
                    js = await request.json()
                    embedMessage = discord.Embed(title=js["title"], description=js["explanation"], url=js["url"], color=discord.Color.og_blurple())
                    embedMessage.set_author(name="NASA")
                    embedMessage.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/110px-NASA_logo.svg.png")
                    if js["media_type"] == "image":
                        embedMessage.set_image(url=js["url"])
                    elif js["media_type"] == "video":
                        embedMessage.set_image(url=js["thumbnail_url"])

                    userId = int(os.getenv("SQIDJI_ID"))
                    sqidji = self.bot.get_user(userId)
                    if sqidji is None:
                        sqidji = await self.bot.fetch_user(userId)

                    await sqidji.send(embed=embedMessage)

async def setup(bot: commands.Bot):
    await bot.add_cog(Loops(bot))
