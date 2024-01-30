import datetime
import os

import aiohttp
import discord
from discord.app_commands import locale_str as _T
from discord.ext import commands

from helpers import constants

class TextCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        description=_T("date"),
        help="Get the current date and time",
        brief="Current date/time"
    )
    async def date(self, ctx: commands.Context):
        await ctx.send(
            f"Today is {discord.utils.format_dt(datetime.datetime.today(), style='d')} {constants.DEFAULT_EMOTE}")

    @commands.hybrid_command(
        description=_T("heh"),
        help="Hehehe boop",
        aliases=["boop"]
    )
    @commands.is_owner()
    async def heh(self, ctx: commands.Context):
        user_id = int(os.getenv("BLIST_ID"))
        josie = self.bot.get_user(user_id)
        if josie is None:
            josie = await self.bot.fetch_user(user_id)
        await josie.send("Boop <a:mmaPokeAnnoyLove:764772302680227890>")
        await ctx.send("Tactical boop launched <a:mmaDanceGrooveMilk:764678198637101083>")

    @commands.command(
        hidden=True
    )
    async def catfact(self, ctx: commands.Context):
        await ctx.send(
            "This command has been depricated. Please use !fact cat instead <:mmMilkSorry:764772302289109003>")

    @commands.hybrid_command(
        description=_T("np"),
        help="Get the link to your currently playing song on Spotify",
        brief="Spotify now playing",
        aliases=["spotify"]
    )
    @commands.guild_only()
    async def np(self, ctx: commands.Context):
        # Only works when sent in a server
        activities = ctx.author.activities
        if len(activities) == 0:
            member = ctx.guild.get_member(ctx.author.id)
            if member:
                activities = member.activities
        for activity in activities:
            if isinstance(activity, discord.Spotify):
                await ctx.send("https://open.spotify.com/track/" + activity.track_id)
                return
        await ctx.send(
            f"You are not currently listening to anything on Spotify {constants.DEFAULT_EMOTE}")

    @commands.hybrid_command(
        description=_T("sauce"),
        help="Get the sauce",
        aliases=["source"]
    )
    async def sauce(self, ctx: commands.Context):
        await ctx.send("https://github.com/ASmallSquishySquid/PhoeBot")

    @commands.hybrid_group(
        description=_T("fact"),
        help="Get a random fact",
        fallback="random"
    )
    async def fact(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://uselessfacts.jsph.pl/api/v2/facts/random") as response:
                if response.status == 200:
                    js = await response.json()
                    await ctx.send(f"{js['text']} <:yes:742975819735105577>")

    @fact.command(
        description=_T("cat"),
        help="Get a random cat fact",
        brief="Cat fact"
    )
    async def cat(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meowfacts.herokuapp.com/") as response:
                await ctx.send(f"https://http.cat/{response.status}")
                if response.status == 200:
                    js = await response.json()
                    await ctx.send(f"{js['data'][0]} <:lick:764398697596715014>")

    @fact.command(
        description=_T("dog"),
        help="Get a random dog fact",
        brief="Dog fact"
    )
    async def dog(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://dog-api.kinduff.com/api/facts") as response:
                await ctx.send(f"https://http.dog/{response.status}.jpg")
                if response.status == 200:
                    js = await response.json()
                    await ctx.send(f"{js['facts'][0]} 🐶")

    @fact.command(
        description=_T("number"),
        help="Get a random number fact",
        brief="Number fact"
    )
    async def number(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get("http://numbersapi.com/random/trivia") as response:
                if response.status == 200:
                    text = await response.text()
                    await ctx.send(f"{text} <:yes:742975819735105577>")

async def setup(bot: commands.Bot):
    await bot.add_cog(TextCommands(bot))
