import aiohttp
import discord
import os

from discord.ext import commands

class Recipes(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.command(
        help="Get some recipes",
        aliases=["recipes", "dinner"]
    )
    async def recipe(self, ctx: commands.Context, *, search: str = commands.parameter(default="dinner", description="The search query")):
        id = os.getenv("EDAMAM_ID")
        key = os.getenv("EDAMAM_KEY")
        random = "true" if search == "dinner" else "false"

        async with aiohttp.ClientSession() as session:
            async with session.get(f"https://api.edamam.com/api/recipes/v2/?type=public&q={search}&app_id={id}&app_key={key}&random={random}&field=label&field=image&field=source&field=url&field=ingredientLines&field=totalTime") as response:
                if response.status == 200:
                    js = await response.json()

                    total = int(js["to"]) - int(js["from"]) + 1
                    embedMessage = Recipes.build_recipe_embed(js["hits"][0]["recipe"], 0, total)
                    buttons = PageButtons(total, js["hits"], {0: embedMessage})

                    buttons.message = await ctx.send(embed=embedMessage, view=buttons)

    def build_recipe_embed(recipeJs, index, total) -> discord.Embed:
        ingredients = "\n".join([ingredient for ingredient in recipeJs["ingredientLines"]])
        embedMessage = discord.Embed(title=recipeJs["label"], url=recipeJs["url"], color=discord.Color.green())
        embedMessage.set_author(name=recipeJs["source"])
        embedMessage.set_image(url=recipeJs["image"])
        embedMessage.set_footer(text=f"Result {index + 1} of {total}")
        embedMessage.add_field(name="Cook time", value=f'{int(recipeJs["totalTime"])} minutes', inline=False)
        embedMessage.add_field(name="Ingredients", value=ingredients, inline=False)

        return embedMessage
    
class PageButtons(discord.ui.View):
    def __init__(self, total: int, hits: dict, embeds: dict):
        super().__init__(timeout=120)
        self.total = total
        self.hits = hits
        self.embeds = embeds
        self.index = 0
        self.message = None
        self.__add_buttons()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)

    def getEmbed(self):
        if not self.index in self.embeds:
            embed = Recipes.build_recipe_embed(self.hits[self.index]["recipe"], self.index, self.total)

            self.embeds[self.index] = embed

        return self.embeds[self.index]

    @discord.ui.button(style=discord.ButtonStyle.red, emoji="⬅️", disabled=True, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1

        for child in self.children:
            child.disabled = False

        if self.index == 0:
            button.disabled = True

        embedMessage = self.getEmbed()

        await self.message.edit(embed=embedMessage, view=self)
        await interaction.response.defer()

    def __add_buttons(self):
        next = discord.ui.Button(style=discord.ButtonStyle.green, emoji="➡️", custom_id="next", disabled=(self.total == 1))

        async def next_button(interaction: discord.Interaction):
            self.index += 1

            for child in self.children:
                child.disabled = False

            if (self.index + 1) == self.total:
                next.disabled = True

            embedMessage = self.getEmbed()

            await self.message.edit(embed=embedMessage, view=self)
            await interaction.response.defer()

        next.callback = next_button

        self.add_item(next)


async def setup(bot: commands.Bot):
    await bot.add_cog(Recipes(bot))