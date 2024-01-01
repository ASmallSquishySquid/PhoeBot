import aiohttp
import discord
import os

from discord.ext import commands
from helpers.pagebuttons import PageButtons
from typing import Optional


class Crochet(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        help="Get some crochet patterns"
    )
    async def pattern(self, ctx: commands.Context, free: Optional[bool] = commands.parameter(default=True, description="Only show free patterns"), *, search: str = commands.parameter(description="The search query")):
        username = os.getenv("RAVELRY_USER")
        password = os.getenv("RAVELRY_PASS")
        free_filter = "&availability=free"

        async with aiohttp.ClientSession(auth=aiohttp.BasicAuth(login=username, password=password)) as session:
            async with session.get(f"https://api.ravelry.com//patterns/search.json?query={search}&page_size=20&craft=crochet&photo=yes&crochet-terminology=2{free_filter if free else ''}") as response:
                if response.status == 200:
                    js = await response.json()

                    total = min(int(js["paginator"]["page_size"]), int(js["paginator"]["results"]))
                    if total > 0:
                        embed_message = self.build_pattern_embed(js["patterns"][0], 0, total)

                        def embed_builder_callback(index: int, total: int) -> discord.Embed:
                            return self.build_pattern_embed(js["patterns"][index], index, total)

                        buttons = PageButtons(total, {0: embed_message}, embed_builder_callback)

                        buttons.message = await ctx.send(embed=embed_message, view=buttons)
                    else:
                        await ctx.send(f"There are no {'free ' if free else ''}patterns for '{search}'")

    def build_pattern_embed(self, pattern_js: dict, index: int, total: int) -> discord.Embed:
        embed_message = discord.Embed(title=pattern_js["name"], url=f"https://www.ravelry.com/patterns/library/{pattern_js['permalink']}", color=discord.Color.from_str("#EE6E62"))
        embed_message.set_author(
            name=pattern_js["designer"]["name"], 
            url=f"https://www.ravelry.com/designers/{pattern_js['designer']['permalink']}", 
            icon_url=(None if len(pattern_js["designer"]["users"]) == 0 else pattern_js["designer"]["users"][0]["photo_url"]))
        embed_message.set_image(url=pattern_js["first_photo"]["medium_url"])
        embed_message.set_footer(text=f"Result {index + 1} of {total}", icon_url="https://cdn.discordapp.com/attachments/1186231213216768060/1191222619454836806/RavelrySecondaryLogo2020-Color.png")

        return embed_message

async def setup(bot: commands.Bot):
    await bot.add_cog(Crochet(bot))