import discord
import os
import sys
import traceback

from discord import app_commands
from discord.ext import commands
from typing import List

from helpers.authorizedusers import AuthorizedUsers

class Admin(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    # Authorization commands

    @commands.hybrid_command(
        help="Authorize a user",
        hidden=True
    )
    @commands.is_owner()
    @commands.guild_only()
    async def authorize(self, ctx: commands.Context, user: discord.User = commands.parameter(description="The user being authorized")):
        name = user.global_name
        if name is None:
            name = user.name
        AuthorizedUsers.add_user(user.id, name)
        await ctx.send("User " + name + " is no longer a stranger <:charmanderawr:837344550804127774>")

    @commands.hybrid_command(
        help="Remove authorization from a user",
        hidden=True
    )
    @commands.is_owner()
    @commands.guild_only()
    async def unauthorize(self, ctx: commands.Context, user: discord.User = commands.parameter(description="The user to remove authorization from")):
        if user.id == int(os.getenv("SQIDJI_ID")):
            await ctx.send("You can't unauthorize yourself!")
            return

        AuthorizedUsers.remove_user(user.id)

        name = user.global_name
        if name is None:
            name = user.name
        await ctx.send("User " + name + " is dead to me <:charmanderawr:837344550804127774>")

    # Cog commands

    @commands.hybrid_command(
        name="load",
        help="Loads a cog",
        hidden=True
    )
    @commands.is_owner()
    async def load_cog(self, ctx: commands.Context, cog_name: str = commands.parameter(displayed_name="cog", description="The name of the extension to load")):
        await self.bot.load_extension("cogs." + cog_name)
        await ctx.send(f"Loaded {cog_name}")

    @commands.hybrid_command(
        name="reload",
        help="Reloads a cog",
        hidden=True
    )
    @commands.is_owner()
    async def reload_cog(self, ctx: commands.Context, cog_name: str = commands.parameter(displayed_name="cog", description="The name of the extension to reload")):
        await self.bot.reload_extension("cogs." + cog_name)
        await ctx.send(f"Reloaded {cog_name}")

    @load_cog.autocomplete("cog_name")
    @reload_cog.autocomplete("cog_name")
    async def reminder_autocomplete(self, interaction: discord.Interaction, current: str,) -> List[app_commands.Choice[str]]:
        cogs = ["textcommands", "loops", "events", "reminders", "recipes"]
        return [
            app_commands.Choice(name=cog, value=cog)
            for cog in cogs if current.lower() in cog.lower()
        ]

    @load_cog.error
    @reload_cog.error
    async def cog_error(self, ctx, error):
        if isinstance(error, commands.ExtensionAlreadyLoaded):
            await ctx.reply(f"{error.name} is already loaded! <:charmanderawr:837344550804127774>")
        elif isinstance(error, commands.ExtensionNotFound):
            await ctx.reply(f"Could not find a cog named {error.name} <:charmanderawr:837344550804127774>")
        elif isinstance(error, commands.ExtensionFailed):
            await ctx.reply(f"{error.name} failed. Please check the logs <:charmanderawr:837344550804127774>")
        elif isinstance(error, commands.NoEntryPointError):
            await ctx.reply(f"{error.name} is missing the setup() function <:charmanderawr:837344550804127774>")
        elif isinstance(error, commands.ExtensionNotLoaded):
            await ctx.reply(f"{error.name} hasn't been loaded yet! <:charmanderawr:837344550804127774>")
        else:
            print(f"Ignoring exception in command {ctx.command}:", file=sys.stderr)
            traceback.print_exception(type(error), error, error.__traceback__, file=sys.stderr)
            sys.stderr.flush()

    # Miscellaneous commands

    @commands.hybrid_command(
        help="Add the bot to your server",
        hidden=True
    )
    @commands.is_owner()
    async def invite(self, ctx: commands.Context):
        if ctx.guild is None:
            await ctx.send(f"https://discord.com/api/oauth2/authorize?client_id={os.getenv('CLIENT_ID')}&permissions=379904&scope=bot", ephemeral=True)

    @commands.hybrid_command(
        help="Syncs the slash command tree",
        hidden=True
    )
    @commands.is_owner()
    async def sync(self, ctx: commands.Context):
        synced = await ctx.bot.tree.sync()
        synced_names = [command.name for command in synced]
        await ctx.send(f"Synced {len(synced)} commands to the command tree <:charmanderawr:837344550804127774>.\nCommands: {synced_names}", ephemeral=True)

async def setup(bot: commands.Bot):
    await bot.add_cog(Admin(bot))