import aiohttp
import datetime
import discord
import os

from discord.ext import commands

class TextCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        help="Gets the current date and time",
        brief="Current date/time"
    )
    async def date(self, ctx: commands.Context):
        await ctx.send("Today is " + str(datetime.date.today().strftime('%m/%d/%Y')) + " <:charmanderawr:837344550804127774>")

    @commands.hybrid_command(
        help="Hehehe boop",
        aliases=["boop"],
        hidden=True
    )
    @commands.is_owner()
    async def heh(self, ctx: commands.Context):
        user_id = int(os.getenv("BLIST_ID"))
        josie = self.bot.get_user(user_id)
        if josie is None:
            josie = await self.bot.fetch_user(user_id)
        await josie.send("Boop <a:mmaPokeAnnoyLove:764772302680227890>")
        await ctx.send("Tactical boop launched <a:mmaDanceGrooveMilk:764678198637101083>")

    @commands.hybrid_command(
        help="Get a random cat fact",
        brief="Cat fact"
    )
    async def catfact(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meowfacts.herokuapp.com/") as response:
                await ctx.send("https://http.cat/" + str(response.status))
                if response.status == 200:
                    js = await response.json()
                    await ctx.send(js["data"][0] + " <:lick:764398697596715014>")

    @commands.hybrid_command(
        help="Gets the link to your currently playing song on Spotify",
        brief="Spotify now playing",
        aliases=["spotify"]
    )
    @commands.guild_only()
    async def np(self, ctx: commands.Context):
        # Only works when sent in a server
        for activity in ctx.author.activities:
            if isinstance(activity, discord.Spotify):
                await ctx.send("https://open.spotify.com/track/" + activity.track_id)
                return
        await ctx.send("You are not currently listening to anything on Spotify <:charmanderawr:837344550804127774>")

    @commands.hybrid_command(
        help="Get the sauce",
        aliases=["source"]
    )
    async def sauce(self, ctx: commands.Context):
        await ctx.send("https://github.com/ASmallSquishySquid/PhoeBot")
    
async def setup(bot: commands.Bot):
    await bot.add_cog(TextCommands(bot))