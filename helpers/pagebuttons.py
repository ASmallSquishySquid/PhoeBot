import discord

from typing import Callable

class PageButtons(discord.ui.View):
    def __init__(self, total: int, embeds: dict, embed_builder: Callable[[int, int], discord.Embed], count: int = 1):
        super().__init__(timeout=120)
        self.total = total
        self.count = count
        self.embeds = embeds
        self.embed_builder = embed_builder
        self.index = 0
        self.message = None
        self.__add_buttons()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)

    def get_embed(self):
        if not self.index in self.embeds:
            embed = self.embed_builder(self.index, self.total)

            self.embeds[self.index] = embed

        return self.embeds[self.index]

    @discord.ui.button(style=discord.ButtonStyle.red, emoji="⬅️", disabled=True, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1

        for child in self.children:
            child.disabled = False

        if self.index == 0:
            button.disabled = True

        embed_message = self.get_embed()

        await self.message.edit(embed=embed_message, view=self)
        await interaction.response.defer()

    def __add_buttons(self):
        next = discord.ui.Button(style=discord.ButtonStyle.green, emoji="➡️", custom_id="next", disabled=(self.total == 1))

        async def next_button(interaction: discord.Interaction):
            self.index += 1

            for child in self.children:
                child.disabled = False

            if self.count * (self.index + 1) >= self.total:
                next.disabled = True

            embed_message = self.get_embed()

            await self.message.edit(embed=embed_message, view=self)
            await interaction.response.defer()

        next.callback = next_button

        self.add_item(next)