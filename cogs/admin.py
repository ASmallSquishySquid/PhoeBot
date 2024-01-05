import datetime
import discord
import os
import sys
import traceback

from discord import app_commands
from discord.ext import commands
from typing import List, Literal

import helpers.constants as constants
from helpers.authorizedusers import AuthorizedUsers

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Authorization commands

    @commands.hybrid_command(
        help="Authorize a user"
    )
    @commands.is_owner()
    @commands.guild_only()
    @app_commands.describe(
        user="The user being authorized"
    )
    @app_commands.default_permissions()
    async def authorize(self, ctx: commands.Context, user: discord.User = commands.parameter(description="The user being authorized")):
        name = user.global_name
        if name is None:
            name = user.name
        AuthorizedUsers.add_user(user.id, name)
        await ctx.send(f"User {user.mention} is no longer a stranger {constants.DEFAULT_EMOTE}")

    @commands.hybrid_command(
        help="Remove authorization from a user"
    )
    @commands.is_owner()
    @commands.guild_only()
    @app_commands.describe(
        user="The user to remove authorization from"
    )
    @app_commands.default_permissions()
    async def unauthorize(self, ctx: commands.Context, user: discord.User = commands.parameter(description="The user to remove authorization from")):
        if user.id == self.bot.owner_id:
            await ctx.send("You can't unauthorize yourself!")
            return

        AuthorizedUsers.remove_user(user.id)

        name = user.global_name
        if name is None:
            name = user.name
        await ctx.send(f"User {user.mention} is dead to me {constants.DEFAULT_EMOTE}")

    @commands.hybrid_command(
        help="Get the list of authorized user IDs"
    )
    @commands.is_owner()
    @app_commands.default_permissions()
    @app_commands.guilds(int(os.getenv(constants.TEST_SERVER_ENV)))
    async def users(self, ctx: commands.Context):
        await ctx.send(AuthorizedUsers.get_user_set(), ephemeral=True)

    # Cog commands

    @commands.hybrid_command(
        name="load",
        help="Loads a cog"
    )
    @commands.is_owner()
    @app_commands.describe(
        cog_name="The name of the extension to load"
    )
    @app_commands.default_permissions()
    @app_commands.guilds(int(os.getenv(constants.TEST_SERVER_ENV)))
    async def load_cog(self, ctx: commands.Context, cog_name: str = commands.parameter(displayed_name="cog", description="The name of the extension to load")):
        await self.bot.load_extension("cogs." + cog_name)
        await ctx.send(f"Loaded {cog_name}")

    @commands.hybrid_command(
        name="reload",
        help="Reloads a cog"
    )
    @commands.is_owner()
    @app_commands.describe(
        cog_name="The name of the extension to reload"
    )
    @app_commands.default_permissions()
    @app_commands.guilds(int(os.getenv(constants.TEST_SERVER_ENV)))
    async def reload_cog(self, ctx: commands.Context, cog_name: str = commands.parameter(displayed_name="cog", description="The name of the extension to reload")):
        await self.bot.reload_extension("cogs." + cog_name)
        await ctx.send(f"Reloaded {cog_name}")

    @load_cog.autocomplete("cog_name")
    @reload_cog.autocomplete("cog_name")
    async def cogs_autocomplete(self, interaction: discord.Interaction, current: str,) -> List[app_commands.Choice[str]]:
        return [
            app_commands.Choice(name=cog, value=cog)
            for cog in constants.COGS if current.lower() in cog.lower()
        ]

    @load_cog.error
    @reload_cog.error
    async def cog_error(self, ctx, error):
        if isinstance(error, commands.CommandInvokeError):
            error = error.original

        if isinstance(error, commands.ExtensionAlreadyLoaded):
            await ctx.reply(f"{error.name} is already loaded! {constants.DEFAULT_EMOTE}")
        elif isinstance(error, commands.ExtensionNotFound):
            await ctx.reply(f"Could not find a cog named {error.name} {constants.DEFAULT_EMOTE}")
        elif isinstance(error, commands.ExtensionFailed):
            await ctx.reply(f"{error.name} failed. Please check the logs {constants.DEFAULT_EMOTE}")
        elif isinstance(error, commands.NoEntryPointError):
            await ctx.reply(f"{error.name} is missing the setup() function {constants.DEFAULT_EMOTE}")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.reply(f"{error.name} hasn't been loaded yet! {constants.DEFAULT_EMOTE}")

        print(f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Ignoring exception in command {ctx.command}:", file=sys.stderr)
        traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
        sys.stderr.flush()

    # Miscellaneous commands

    @commands.hybrid_command(
        help="Add the bot to your server"
    )
    @commands.is_owner()
    @app_commands.default_permissions()
    async def invite(self, ctx: commands.Context):
        client_id = os.getenv('CLIENT_ID')
        if ctx.guild:
            await ctx.author.send(f"https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions=379904&scope=bot")
            await ctx.send("Sent the invite link in DMs", ephemeral=True)
        else:
            await ctx.send(f"https://discord.com/api/oauth2/authorize?client_id={client_id}&permissions=379904&scope=bot")

    @commands.hybrid_command(
        help="Syncs the slash command tree"
    )
    @commands.is_owner()
    @app_commands.describe(
        which="Which tree do you want to sync?"
    )
    @app_commands.default_permissions()
    @app_commands.guilds(int(os.getenv(constants.TEST_SERVER_ENV)))
    async def sync(self, ctx: commands.Context, which: str = commands.parameter(default="*", converter=Literal["*", "test", "~"])):
        test_guild = await commands.GuildConverter().convert(ctx, os.getenv(constants.TEST_SERVER_ENV))

        if which == "*":
            #  Sync everything
            synced = await ctx.bot.tree.sync()
            synced.extend(await ctx.bot.tree.sync(guild=test_guild))
        elif which == "test":
            # Sync everything only to the test guild
            ctx.bot.tree.copy_global_to(guild=test_guild)
            synced = await ctx.bot.tree.sync(guild=test_guild)
        elif which == "~":
            # Sync the test guild
            synced = await ctx.bot.tree.sync(guild=test_guild)

        synced_names = [command.name for command in synced]
        await ctx.send(f"Synced {len(synced)} commands to the command tree {constants.DEFAULT_EMOTE}.\nCommands: {synced_names}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))