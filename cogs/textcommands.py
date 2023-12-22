import aiohttp
import datetime
import discord

from discord.ext import commands

from helpers.authorizedusers import AuthorizedUsers

class TextCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        help="Gets the current date and time",
        brief="Current date/time"
    )
    async def date(self, ctx: commands.Context):
        await ctx.send("Today is " + str(datetime.date.today().strftime('%m/%d/%Y')) + " <:charmanderawr:837344550804127774>")

    @commands.command(
        help="Hehehe boop"
    )
    async def heh(self, ctx: commands.Context):
        if not ctx.author.id == 274397067177361408:
            await ctx.send("Sorry, but you can't use this command <:charmanderawr:837344550804127774>")
            return

        josie = self.bot.get_user(559828298973184011)
        if josie is None:
            josie = await self.bot.fetch_user(559828298973184011)
        await josie.send("Boop <a:mmaPokeAnnoyLove:764772302680227890>")

    @commands.command(
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

    @commands.command(
        help="Gets the link to your currently playing song on Spotify",
        brief="Spotify now playing"
    )
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

    @commands.command(
        help="Authorize a user",
        hidden=True
    )
    async def authorize(self, ctx: commands.Context, user: discord.User = commands.parameter(description="The user being authorized")):
        name = user.global_name
        if name is None:
            name = user.name
        AuthorizedUsers.addUser(user.id, name)
        await ctx.send("User " + name + " is no longer a stranger <:charmanderawr:837344550804127774>")

    @commands.command(
        help="Get the sauce"
    )
    async def sauce(self, ctx: commands.Context):
        await ctx.send("https://github.com/ASmallSquishySquid/PhoeBot")

    
async def setup(bot: commands.Bot):
    await bot.add_cog(TextCommands(bot))