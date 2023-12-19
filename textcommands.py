import datetime
import aiohttp
from discord.ext import commands

class TextCommands(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command()
    async def date(self, ctx: commands.Context):
        await ctx.send("Today is " + str(datetime.date.today().strftime('%m/%d/%Y')) + " <:charmanderawr:837344550804127774>")

    @commands.command()
    async def heh(self, ctx: commands.Context):
        await self.bot.josie.send("Boop <a:mmaPokeAnnoyLove:764772302680227890>")

    @commands.command()
    async def catfact(self, ctx: commands.Context):
        async with aiohttp.ClientSession() as session:
            async with session.get("https://meowfacts.herokuapp.com/") as response:
                await ctx.send("https://http.cat/" + str(response.status))
                if response.status == 200:
                    js = await response.json()
                    await ctx.send(js["data"][0] + " <:lick:764398697596715014>")
    
async def setup(bot: commands.Bot):
    await bot.add_cog(TextCommands(bot))