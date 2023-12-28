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
            self.sleepy_time.start()
        else:
            self.drink_water.start()

    @tasks.loop(minutes=15)
    async def sleepy_time(self):
        guild_id = int(os.getenv("DUCK_SERVER_ID"))
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            guild = await self.bot.fetch_guild(guild_id)

        user_id = int(os.getenv("SQIDJI_ID"))
        sqidji = guild.get_member(user_id)
        if sqidji is None:
            sqidji = await guild.fetch_member(user_id)

        if (sqidji.status==discord.Status.online):
            await sqidji.send("Go to sleep! <:charmanderawr:837344550804127774>")

    @tasks.loop(minutes=30)
    async def drink_water(self):
        guild_id = int(os.getenv("DUCK_SERVER_ID"))
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            guild = await self.bot.fetch_guild(guild_id)

        user_id = int(os.getenv("SQIDJI_ID"))
        sqidji = guild.get_member(user_id)
        if sqidji is None:
            sqidji = await guild.fetch_member(user_id)

        if (sqidji.status==discord.Status.online):
            await sqidji.send("Drink some water! <:charmanderawr:837344550804127774>")

    # 11:30 PM
    @tasks.loop(time=datetime.time(hour=7, minute=30))
    async def bedtime(self):
        self.sleepy_time.start()
        self.drink_water.cancel()

    # 9:00 AM
    @tasks.loop(time=datetime.time(hour=17, minute=0))
    async def morning(self):
        self.sleepy_time.cancel()
        self.drink_water.start()

    # 8:30 AM
    @tasks.loop(time=datetime.time(hour=16, minute=30))
    async def apod(self):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY") as request:
                if request.status == 200:
                    js = await request.json()
                    embed_message = discord.Embed(title=js["title"], description=js["explanation"], url=js["url"], color=discord.Color.og_blurple())
                    embed_message.set_author(name="NASA")
                    embed_message.set_thumbnail(url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/110px-NASA_logo.svg.png")
                    if js["media_type"] == "image":
                        embed_message.set_image(url=js["url"])
                    elif js["media_type"] == "video":
                        embed_message.set_image(url=js["thumbnail_url"])

                    user_id = int(os.getenv("SQIDJI_ID"))
                    sqidji = self.bot.get_user(user_id)
                    if sqidji is None:
                        sqidji = await self.bot.fetch_user(user_id)

                    await sqidji.send(embed=embed_message)

async def setup(bot: commands.Bot):
    await bot.add_cog(Loops(bot))
