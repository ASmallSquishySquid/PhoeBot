import os
from typing import List

import aiohttp
import discord
from discord import app_commands
from discord.app_commands import locale_str as _T
from discord.ext import commands

from helpers.pagebuttons import PageButtons

class Recipes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        description=_T("recipe"),
        help="Get some recipes",
        aliases=["recipes", "dinner"]
    )
    @app_commands.describe(
        search=_T("recipe-search")
    )
    async def recipe(self, ctx: commands.Context, *,
        search: str = commands.parameter(default="dinner", description="The search query")):

        app_id = os.getenv("EDAMAM_ID")
        app_key = os.getenv("EDAMAM_KEY")

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.edamam.com/api/recipes/v2/?type=public&q={search}&app_id={app_id}&app_key={app_key}&random=true&field=label&field=image&field=source&field=url&field=ingredientLines&field=totalTime") as response:
                if response.status == 200:
                    js = await response.json()

                    total = int(js["to"]) - int(js["from"]) + 1
                    embed_message = self.build_recipe_embed(js["hits"][0]["recipe"], 0, total)

                    def embed_builder_callback(index: int, total: int) -> discord.Embed:
                        return self.build_recipe_embed(js["hits"][index]["recipe"], index, total)

                    buttons = PageButtons(total, {0: embed_message}, embed_builder_callback)

                    buttons.message = await ctx.send(embed=embed_message, view=buttons)

    @recipe.autocomplete("search")
    async def recipe_autocomplete(
        self, interaction: discord.Interaction, current: str,) -> List[app_commands.Choice[str]]:
        cuisines = ["Chinese", "Pasta", "Potatoes", "Ground Turkey"]
        return [
            app_commands.Choice(name=cuisine, value=cuisine.lower())
            for cuisine in cuisines if current.lower() in cuisine.lower()
        ]

    def build_recipe_embed(self, recipe_js: dict, index: int, total: int) -> discord.Embed:
        ingredients = "\n".join(list(recipe_js["ingredientLines"]))
        embed_message = discord.Embed(
            title=recipe_js["label"],
            url=recipe_js["url"],
            color=discord.Color.green())
        embed_message.set_author(name=recipe_js["source"])
        embed_message.set_image(url=recipe_js["image"])
        embed_message.set_footer(text=f"Result {index + 1} of {total}")
        embed_message.add_field(
            name="Cook time",
            value=f'{int(recipe_js["totalTime"])} minutes',
            inline=False)
        embed_message.add_field(name="Ingredients", value=ingredients, inline=False)

        return embed_message

async def setup(bot: commands.Bot):
    await bot.add_cog(Recipes(bot))
