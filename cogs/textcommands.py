import aiohttp
import datetime
import discord

from discord.ext import commands

class TextCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def date(self, ctx: commands.Context):
        await ctx.send("Today is " + str(datetime.date.today().strftime('%m/%d/%Y')) + " <:charmanderawr:837344550804127774>")

    @commands.command()
    async def heh(self, ctx: commands.Context):
        josie = self.bot.get_user(559828298973184011)
        await josie.send("Boop <a:mmaPokeAnnoyLove:764772302680227890>")

    @commands.command()
    async def catfact(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meowfacts.herokuapp.com/") as response:
                await ctx.send("https://http.cat/" + str(response.status))
                if response.status == 200:
                    js = await response.json()
                    await ctx.send(js["data"][0] + " <:lick:764398697596715014>")

    @commands.command()
    async def np(self, ctx: commands.Context):
        # Only works when sent in a server
        if isinstance(ctx.author, discord.Member):
            for activity in ctx.author.activities:
                if isinstance(activity, discord.Spotify):
                    await ctx.send("https://open.spotify.com/track/" + activity.track_id)
                    return
            await ctx.send("You are not currently listening to anything on Spotify <:charmanderawr:837344550804127774>")
        else:
            await ctx.send("Can not get user's Spotify status in DMs <:judgemental:748787284811186216>")

    
async def setup(bot: commands.Bot):
    await bot.add_cog(TextCommands(bot))