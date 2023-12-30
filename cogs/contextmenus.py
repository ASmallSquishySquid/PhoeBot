import discord
import os

from discord import app_commands
from discord.ext import commands

from helpers.authorizedusers import AuthorizedUsers

class ContextMenus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.authorize_ctx_menu = app_commands.ContextMenu(
            name='Authorize',
            callback=self.authorize_context_menu,
        )
        self.unauthorize_ctx_menu = app_commands.ContextMenu(
            name='Unauthorize',
            callback=self.unauthorize_context_menu,
        )
        self.bot.tree.add_command(self.authorize_ctx_menu)
        self.bot.tree.add_command(self.unauthorize_ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(self.authorize_ctx_menu.name, type=self.authorize_ctx_menu.type)
        self.bot.tree.remove_command(self.unauthorize_ctx_menu.name, type=self.unauthorize_ctx_menu.type)

    def is_owner(interaction: discord.Interaction) -> bool:
        return interaction.user.id == int(os.getenv("SQIDJI_ID"))

    @app_commands.check(is_owner)
    async def authorize_context_menu(self, interaction: discord.Interaction, member: discord.Member) -> None:
        name = member.global_name
        if name is None:
            name = member.name

        AuthorizedUsers.add_user(member.id, name)

        await interaction.response.send_message(f"User {member.mention} is no longer a stranger <:charmanderawr:837344550804127774>")

    @app_commands.check(is_owner)
    async def unauthorize_context_menu(self, interaction: discord.Interaction, member: discord.Member) -> None:
        if member.id == self.bot.owner_id:
            await interaction.response.send_message("You can't unauthorize yourself!", ephemeral=True)
            return
        
        AuthorizedUsers.remove_user(member.id)

        await interaction.response.send_message(f"User {member.mention} is dead to me <:charmanderawr:837344550804127774>")

async def setup(bot: commands.Bot):
    await bot.add_cog(ContextMenus(bot))