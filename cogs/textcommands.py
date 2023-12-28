import os
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
        help="Hehehe boop",
        hidden=True
    )
    @commands.is_owner()
    async def heh(self, ctx: commands.Context):
        userId = int(os.getenv("BLIST_ID"))
        josie = self.bot.get_user(userId)
        if josie is None:
            josie = await self.bot.fetch_user(userId)
        await josie.send("Boop <a:mmaPokeAnnoyLove:764772302680227890>")
        await ctx.send("Tactical boop launched <a:mmaDanceGrooveMilk:764678198637101083>")

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
    @commands.guild_only()
    async def np(self, ctx: commands.Context):
        # Only works when sent in a server
        for activity in ctx.author.activities:
            if isinstance(activity, discord.Spotify):
                await ctx.send("https://open.spotify.com/track/" + activity.track_id)
                return
        await ctx.send("You are not currently listening to anything on Spotify <:charmanderawr:837344550804127774>")

    @commands.command(
        help="Authorize a user",
        hidden=True
    )
    @commands.is_owner()
    @commands.guild_only()
    async def authorize(self, ctx: commands.Context, user: discord.User = commands.parameter(description="The user being authorized")):
        name = user.global_name
        if name is None:
            name = user.name
        AuthorizedUsers.addUser(user.id, name)
        await ctx.send("User " + name + " is no longer a stranger <:charmanderawr:837344550804127774>")

    @commands.command(
        help="Remove authorization from a user",
        hidden=True
    )
    @commands.is_owner()
    @commands.guild_only()
    async def unauthorize(self, ctx: commands.Context, user: discord.User = commands.parameter(description="The user to remove authorization from")):
        if user.id == 274397067177361408:
            await ctx.send("You can't unauthorize yourself!")
            return

        AuthorizedUsers.removeUser(user.id)

        name = user.global_name
        if name is None:
            name = user.name
        await ctx.send("User " + name + " is dead to me <:charmanderawr:837344550804127774>")

    @commands.command(
        help="Get the sauce"
    )
    async def sauce(self, ctx: commands.Context):
        await ctx.send("https://github.com/ASmallSquishySquid/PhoeBot")

    @commands.command(
        help="Add the bot to your server",
        hidden=True
    )
    @commands.is_owner()
    async def invite(self, ctx: commands.Context):
        await ctx.author.send("https://discord.com/api/oauth2/authorize?client_id=874820032968921209&permissions=379904&scope=bot")

    
async def setup(bot: commands.Bot):
    await bot.add_cog(TextCommands(bot))