import datetime
import os
import random
import sys
import traceback

import aiohttp
import discord
from discord.ext import commands
from discord.ext import tasks
import feedparser

from helpers import constants

class Loops(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.bedtime.start()
        self.morning.start()
        self.apod.start()
        self.daily_good_news.start()

        if not (datetime.datetime.now() > datetime.datetime.now().replace(hour=9, minute=0, second=0) and datetime.datetime.now() < datetime.datetime.now().replace(hour=23, minute=30, second=0)):
            self.sleepy_time.start()
        else:
            self.drink_water.start()

    async def cog_unload(self):
        self.bedtime.cancel()
        self.morning.cancel()
        self.apod.cancel()
        self.daily_good_news.cancel()
        self.sleepy_time.cancel()
        self.drink_water.cancel()

    @tasks.loop(minutes=15)
    async def sleepy_time(self):
        guild_id = int(os.getenv(constants.TEST_SERVER_ENV))
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            guild = await self.bot.fetch_guild(guild_id)

        user_id = int(os.getenv("SQIDJI_ID"))
        sqidji = guild.get_member(user_id)
        if sqidji is None:
            sqidji = await guild.fetch_member(user_id)

        if sqidji.status==discord.Status.online:
            await sqidji.send(f"Go to sleep! {constants.DEFAULT_EMOTE}")

    @tasks.loop(minutes=30)
    async def drink_water(self):
        guild_id = int(os.getenv(constants.TEST_SERVER_ENV))
        guild = self.bot.get_guild(guild_id)
        if guild is None:
            guild = await self.bot.fetch_guild(guild_id)

        user_id = int(os.getenv("SQIDJI_ID"))
        sqidji = guild.get_member(user_id)
        if sqidji is None:
            sqidji = await guild.fetch_member(user_id)

        if sqidji.status==discord.Status.online:
            await sqidji.send(f"Drink some water! {constants.DEFAULT_EMOTE}")

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
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get("https://api.nasa.gov/planetary/apod?api_key=DEMO_KEY") as request:
                    if request.status == 200:
                        js = await request.json()
                        embed_message = discord.Embed(
                            title=js["title"],
                            description=js["explanation"],
                            url=js["hdurl"] if "hdurl" in js else js["url"],
                            color=discord.Color.og_blurple())
                        embed_message.set_author(
                            name="NASA",
                            url=f"https://apod.nasa.gov/apod/ap{''.join(date[-2:] for date in js['date'].split('-'))}.html",
                            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/e/e5/NASA_logo.svg/110px-NASA_logo.svg.png")

                        if js["media_type"] == "image":
                            embed_message.set_image(url=js["url"])
                        elif js["media_type"] == "video":
                            video_id = "mPcoBfQ5j-k"
                            if "youtu" in js["url"]:
                                video_id = js["url"].split("/")[-1].split("?")[0]
                            embed_message.set_image(
                                url=f"https://img.youtube.com/vi/{video_id}/maxresdefault.jpg")

                        user_id = int(os.getenv("SQIDJI_ID"))
                        sqidji = self.bot.get_user(user_id)
                        if sqidji is None:
                            sqidji = await self.bot.fetch_user(user_id)

                        await sqidji.send(embed=embed_message)

                    else:
                        print(f"Error getting APOD: {request.status}", file=sys.stderr)
                        sys.stderr.flush()

        except (aiohttp.ClientError, KeyError, discord.HTTPException, discord.NotFound) as error:
            print(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] APOD failed with exception:",
                file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            sys.stderr.flush()

    # 10:00 AM
    @tasks.loop(time=datetime.time(hour=18, minute=0))
    async def daily_good_news(self):
        base_url = "https://www.goodnewsnetwork.org/category/{}/feed/"
        feeds = ["USA", "Science", "Animals"]
        indices = random.sample(range(50), 3)
        stories = {}

        try:
            async with aiohttp.ClientSession() as session:
                for feed in feeds:
                    async with session.get(base_url.format(feed.lower())) as response:
                        if response.status == 200:
                            text = await response.text()
                            response_feed = feedparser.parse(text)
                            stories[feed] = [
                                (response_feed.entries[i].title, response_feed.entries[i].link)
                                for i in indices]

                        else:
                            print(
                                f"Error getting daily good news in {feed} category: {response.status}",
                                file=sys.stderr)
                            sys.stderr.flush()

            embed_message = discord.Embed(
                title="Your daily good news <:cutesmile:772176440330027038>",
                color=discord.Color.og_blurple(),
                timestamp=datetime.datetime.now())
            embed_message.set_author(
                name="Good News Network",
                url="https://www.goodnewsnetwork.org/",
                icon_url="https://www.goodnewsnetwork.org/wp-content/uploads/2021/01/cropped-GNN-Logo-Circles-2017-1-32x32.png"
            )
            for section, selected_stories in stories.items():
                formatted = "\n\n".join(
                    [f"[{story[0]}]({story[1]})" for story in selected_stories])
                embed_message.add_field(
                    name=f"__{section}__", value=formatted, inline=False)

            user_id = int(os.getenv("SQIDJI_ID"))
            sqidji = self.bot.get_user(user_id)
            if sqidji is None:
                sqidji = await self.bot.fetch_user(user_id)

            await sqidji.send(embed=embed_message)

        except (aiohttp.ClientError, IndexError, discord.HTTPException, discord.NotFound) as error:
            print(
                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] APOD failed with exception:",
                file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            sys.stderr.flush()

async def setup(bot: commands.Bot):
    await bot.add_cog(Loops(bot))
