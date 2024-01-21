from typing import List

import discord
from discord import app_commands
from discord.app_commands import locale_str as _T
from discord.ext import commands

import helpers.constants as constants
from helpers.google import Google, Task

class Tasks(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.hybrid_command(
        description=_T("tasks"),
        help="Get your tasks"
    )
    @app_commands.describe(
        task_list=_T("tasks-task_list")
    )
    @commands.is_owner()
    @app_commands.default_permissions()
    async def tasks(self, ctx: commands.Context, *,
        task_list: str = commands.parameter(default=None, description="The task list")):

        list_id = None
        name = None
        tasklists = Google.tasklists()

        if not task_list:
            list_id = tasklists[0].id
            name = tasklists[0].title
        else:
            tasklist = next((tasklist for tasklist in tasklists
                if task_list == tasklist.id or task_list in tasklist.title.lower()), None)

            if not tasklist:
                await ctx.send(f"That task list does not exist {constants.DEFAULT_EMOTE}")
                return

            list_id = tasklist.id
            name = tasklist.title

        tasks = Google.tasks(list_id)

        await ctx.send(embed=self.build_tasks_embed(tasks, name))

    @tasks.autocomplete("task_list")
    async def tasks_autocomplete(
        self, interaction: discord.Interaction, current: str,) -> List[app_commands.Choice[str]]:
        tasklists = Google.tasklists()
        return [
            app_commands.Choice(name=tasklist.title, value=tasklist.id)
            for tasklist in tasklists if current.lower() in tasklist.title.lower()
        ]

    def build_tasks_embed(self, tasks: List[Task], name: str) -> discord.Embed:
        embed_message = discord.Embed(
            title=name,
            description="\n".join([f"☐ {task.title}" for task in tasks]),
            color=discord.Color.blue())
        embed_message.set_author(
            name="Google Tasks",
            icon_url="https://upload.wikimedia.org/wikipedia/commons/thumb/5/5b/Google_Tasks_2021.svg/527px-Google_Tasks_2021.svg.png")

        return embed_message

async def setup(bot: commands.Bot):
    await bot.add_cog(Tasks(bot))
