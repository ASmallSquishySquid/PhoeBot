import os

import discord
from discord import app_commands
from discord.ext import commands

from helpers import constants
from helpers.authorizedusers import AuthorizedUsers

class ContextMenus(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.authorize_ctx_menu = app_commands.ContextMenu(
            name="Authorize",
            callback=self.authorize_context_menu,
        )
        self.unauthorize_ctx_menu = app_commands.ContextMenu(
            name="Unauthorize",
            callback=self.unauthorize_context_menu,
        )
        self.reminder_ctx_menu = app_commands.ContextMenu(
            name="Remind me",
            callback=self.reminder_context_menu,
        )
        self.bot.tree.add_command(self.authorize_ctx_menu)
        self.bot.tree.add_command(self.unauthorize_ctx_menu)
        self.bot.tree.add_command(self.reminder_ctx_menu)

    async def cog_unload(self) -> None:
        self.bot.tree.remove_command(
            self.authorize_ctx_menu.name,
            type=self.authorize_ctx_menu.type)
        self.bot.tree.remove_command(
            self.unauthorize_ctx_menu.name,
            type=self.unauthorize_ctx_menu.type)
        self.bot.tree.remove_command(
            self.reminder_ctx_menu.name,
            type=self.reminder_ctx_menu.type)

    def is_owner(interaction: discord.Interaction) -> bool:
        return interaction.user.id == int(os.getenv(constants.OWNER_ENV))

    @app_commands.check(is_owner)
    @app_commands.default_permissions()
    async def authorize_context_menu(self,
        interaction: discord.Interaction, member: discord.Member) -> None:

        name = member.global_name
        if name is None:
            name = member.name

        AuthorizedUsers.add_user(member.id, name)

        await interaction.response.send_message(
            f"User {member.mention} is no longer a stranger {constants.DEFAULT_EMOTE}")

    @app_commands.check(is_owner)
    @app_commands.default_permissions()
    async def unauthorize_context_menu(self,
        interaction: discord.Interaction, member: discord.Member) -> None:

        if member.id == self.bot.owner_id:
            await interaction.response.send_message(
                "You can't unauthorize yourself!",
                ephemeral=True)
            return

        AuthorizedUsers.remove_user(member.id)

        await interaction.response.send_message(
            f"User {member.mention} is dead to me {constants.DEFAULT_EMOTE}")

    async def reminder_context_menu(self,
        interaction: discord.Interaction, message: discord.Message) -> None:

        context = await self.bot.get_context(interaction)
        set_reminder_command = self.bot.get_command("reminders set")

        view = DropdownView(message.jump_url, context, set_reminder_command)

        await interaction.response.send_message(
            "When would you like me to remind you?",
            view=view,
            ephemeral=True)

        view.message = await interaction.original_response()

class DropdownView(discord.ui.View):
    def __init__(self, message_url: str,
        ctx: commands.Context, reminder_command: commands.Command):

        self.message_url = message_url
        self.ctx = ctx
        self.reminder_command = reminder_command
        self.message = None
        super().__init__(timeout=60)

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)

    @discord.ui.select(
        cls=discord.ui.Select,
        placeholder="Please select a time",
        options=[
            discord.SelectOption(
                label="Tomorrow", description="Tomorrow morning at 10 AM", emoji="🌄",
                value="1d 10:00"),
            discord.SelectOption(
                label="Tonight", description="Tonight at 8 PM", emoji="🌒",
                value="0d 20:00"),
            discord.SelectOption(
                label="In one hour", description="One hour from now", emoji="🕐",
                value="1h")
        ]
    )
    async def select_time(self, interaction: discord.Interaction, select: discord.ui.Select):
        select.disabled =  True

        await self.ctx.invoke(
            self.reminder_command,
            reminder=self.message_url,
            when=select.values[0])

        await interaction.response.edit_message(view=self)

async def setup(bot: commands.Bot):
    await bot.add_cog(ContextMenus(bot))
