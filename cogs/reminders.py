import datetime
import os
from typing import List, Optional

import discord
from discord import app_commands
from discord.app_commands import locale_str as _T
from discord.ext import commands
from discord.ext import tasks

from helpers import constants
from helpers.pagebuttons import PageButtons
from helpers.remindermanager import ReminderManager

class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.get_reminders.start()

    async def cog_unload(self):
        self.get_reminders.cancel()
        self.send_reminders.cancel()

    # every day, on startup time
    @tasks.loop(hours=24)
    async def get_reminders(self):
        ReminderManager.rebuild()

        if not self.send_reminders.is_running():
            self.send_reminders.start()

    @tasks.loop(minutes=1)
    async def send_reminders(self):
        upcoming = ReminderManager.get_all_upcoming_reminders()

        for reminder in upcoming:
            requester = self.bot.get_user(reminder[1])
            if requester is None:
                requester = await self.bot.fetch_user(reminder[1])

            embed_message = discord.Embed(
                title=f"Reminder! {constants.DEFAULT_EMOTE}",
                description=reminder[2],
                color=discord.Color.og_blurple())
            embed_message.add_field(
                name="Time",
                value=discord.utils.format_dt(reminder[3], style="R"))

            buttons = SnoozeButtons(self, reminder[2])
            buttons.message = await requester.send(embed=embed_message, view=buttons)

    @commands.hybrid_group(
        description=_T("reminders"),
        help="Get your future reminders",
        fallback="get"
    )
    @app_commands.rename(
        show_id=_T("ids")
    )
    @app_commands.describe(
        count=_T("reminders-count"),
        show_id=_T("reminders-ids")
    )
    async def reminders(self, ctx: commands.Context,
        count: Optional[int] =
            commands.parameter(default=10, description="Number of reminders per page"),
        show_id: bool =
            commands.parameter(
                displayed_name="ids",
                default=False,
                description="Whether to show the reminder IDs")):

        now = datetime.datetime.now()
        total = ReminderManager.get_upcoming_reminders_count(ctx.author.id)

        if total == 0:
            await ctx.send(f"There are no upcoming reminders {constants.DEFAULT_EMOTE}")
            return

        embed_message = self.build_reminders_embed(ctx.author.id, now, count, 0, total, show_id)

        if total <= count:
            await ctx.send(embed=embed_message)
            return

        def embed_builder_callback(index: int, total: int) -> discord.Embed:
            return self.build_reminders_embed(ctx.author.id, now, count, index, total, show_id)

        buttons = PageButtons(total, {0: embed_message}, embed_builder_callback, count)
        buttons.message = await ctx.send(embed=embed_message, view=buttons)

    @reminders.command(
        description=_T("set"),
        help="Set a reminder"
    )
    @app_commands.describe(
        reminder=_T("set-reminder"),
        when=_T("set-when")
    )
    async def set(self, ctx: commands.Context,
        reminder: str = commands.parameter(description="What do you want to be reminded of?"), *,
        when: str = commands.parameter(
            displayed_name="time",
            description="When do you want to be reminded?",
            default="1h")
    ):
        time_arg = "".join(when)
        date_param = datetime.datetime.now()

        components = time_arg.split()
        for component in components:
            lower_component = component.lower()
            if ":" in lower_component:
                parts = lower_component.split(":")
                date_param = date_param.replace(hour=int(parts[0]), minute=int(parts[1]))
                if len(parts) == 3:
                    date_param = date_param.replace(second=int(parts[2]))

                # Check if the time was meant for tomorrow
                if date_param < datetime.datetime.now() and len(components) == 1:
                    date_param = date_param + datetime.timedelta(days=1)

            elif "/" in lower_component:
                parts = lower_component.split("/")
                new_date = date_param.replace(month=int(parts[0]), day=int(parts[1]))

                # Check if the date is meant for next year
                if new_date < date_param:
                    new_date = new_date.replace(year=new_date.year + 1)

                date_param = new_date

                if len(parts) == 3:
                    year=int(parts[2])
                    # Fix two digit years
                    if len(parts[2]) == 2:
                        year += 2000
                    date_param = date_param.replace(year=year)
                if len(components) == 1:
                    date_param = date_param.replace(hour=10, minute=0)

            elif lower_component.endswith("d"):
                date_param = date_param + datetime.timedelta(days=int(lower_component[:-1]))
            elif lower_component.endswith("h"):
                date_param = date_param + datetime.timedelta(hours=int(lower_component[:-1]))
            elif lower_component.endswith("m"):
                date_param = date_param + datetime.timedelta(minutes=int(lower_component[:-1]))
            elif lower_component.endswith("s"):
                date_param = date_param + datetime.timedelta(seconds=int(lower_component[:-1]))

        reminder_id = ReminderManager.add_reminder(reminder, date_param, ctx.author.id)

        embed_message = discord.Embed(
            title=f"Reminder created {constants.DEFAULT_EMOTE}",
            description=reminder,
            color=discord.Color.og_blurple())
        embed_message.add_field(
            name="Scheduled Time",
            value=discord.utils.format_dt(date_param))

        buttons = DeleteButton(embed_message, reminder_id)
        buttons.message = await ctx.send(embed=embed_message, view=buttons)

    @set.autocomplete("when")
    async def reminder_autocomplete(self, interaction: discord.Interaction,
        current: str,) -> List[app_commands.Choice[str]]:

        times = ["10:00", "1d", "1h", "15m"]
        matched_times = [
            app_commands.Choice(name=time, value=time)
            for time in times if current.lower() in time.lower()
        ]

        days = {
            "tomorrow": "1d 10:00",
            "tonight": "0d 20:00",
            "midnight": "0:00",
            "noon": "12:00"
        }
        matched_times.extend([
            app_commands.Choice(name=day, value=time)
            for day, time in days.items() if current.lower() in day.lower()
        ])

        return matched_times

    @set.error
    async def remind_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send(f'The remind command takes in a reminder string and a time. ex: !reminders set "Send email" 12:00 {constants.DEFAULT_EMOTE}')
        else:
            await ctx.send(f'Please keep the reminder in one string and keep all time components separate. And no AM/PM! {constants.DEFAULT_EMOTE}')

    @reminders.command(
        description=_T("debug"),
        help="Get the contents of the internal reminder list"
    )
    @commands.is_owner()
    @app_commands.default_permissions()
    @app_commands.guilds(int(os.getenv(constants.TEST_SERVER_ENV)))
    async def debug(self, ctx: commands.Context):
        await ctx.send(ReminderManager.get_cache())

    @reminders.command(
        description=_T("delete"),
        help="Delete a reminder"
    )
    @app_commands.describe(
        reminder_id=_T("delete-reminder_id")
    )
    async def delete(self, ctx: commands.Context,
        reminder_id: int = commands.parameter(
            displayed_name="reminder ID",
            description="The ID of the reminder being deleted")):

        if not ReminderManager.remove_reminder(ctx.author.id, reminder_id):
            await ctx.send(f"You can't delete reminders that aren't yours! {constants.DEFAULT_EMOTE}")
            return

        await ctx.send(f"Ok, deleted reminder {reminder_id} {constants.DEFAULT_EMOTE}")

    @delete.autocomplete("reminder_id")
    async def delete_autocomplete(self, interaction: discord.Interaction,
        current: int,) -> List[app_commands.Choice[int]]:
        top_5 = ReminderManager.get_reminder_page(
            interaction.user.id, datetime.datetime.now(), 5, 0)

        matched = [
            app_commands.Choice(name=reminder[0], value=reminder[0])
            for reminder in top_5 if str(current) in str(reminder[0])
        ]

        return matched

    def build_reminders_embed(self, user_id: int,
        time_now: datetime.datetime, count: int,
        index: int, total:int, show_id: bool) -> discord.Embed:

        # Don't want to load math module into memory for one function
        num_pages = int(total / count) + (1 if total % count != 0 else 0)

        reminder_page = ReminderManager.get_reminder_page(user_id, time_now, count, index)

        if show_id:
            ids = "\n".join([str(reminder[0]) for reminder in reminder_page])
        reminder_texts = "\n".join([reminder[1] for reminder in reminder_page])
        times = "\n".join([discord.utils.format_dt(reminder[2]) for reminder in reminder_page])

        embed = discord.Embed(
            title=f"Upcoming reminders {constants.DEFAULT_EMOTE}",
            color=discord.Color.og_blurple(),
            timestamp=datetime.datetime.now())
        if show_id:
            embed.add_field(name="ID", value=ids)
        embed.add_field(name="Reminder", value=reminder_texts)
        embed.add_field(name="Time", value=times)
        embed.set_footer(text=f"Page {index + 1} of {num_pages}")

        return embed

class SnoozeButtons(discord.ui.View):
    def __init__(self, reminder_instance: Reminders, reminder: str):
        super().__init__(timeout=120)
        self.reminder_instance = reminder_instance
        self.reminder = reminder

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)

    @discord.ui.button(
        label="15 minutes",
        style=discord.ButtonStyle.primary,
        emoji="<a:mochaSleep:764675744819314738>")
    async def delay_15_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.__add_time(interaction, 15)

    @discord.ui.button(
        label="30 minutes",
        style=discord.ButtonStyle.secondary,
        emoji="⏰")
    async def delay_30_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.__add_time(interaction, 30)

    @discord.ui.button(
        label="1 hour",
        style=discord.ButtonStyle.secondary,
        emoji="⏰")
    async def delay_60_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.__add_time(interaction, 60)

    async def __add_time(self: discord.ui.View, interaction: discord.Interaction, delay: int):
        for child in self.children:
            child.disabled = True

        date_param = datetime.datetime.now() + datetime.timedelta(minutes=delay)

        ReminderManager.add_reminder(self.reminder, date_param, interaction.user.id)

        embed_message = discord.Embed(
            title=f"Reminder snoozed {constants.DEFAULT_EMOTE}",
            description=self.reminder,
            color=discord.Color.og_blurple())
        embed_message.add_field(
            name="Scheduled Time",
            value=discord.utils.format_dt(date_param))
        await interaction.response.edit_message(view=self, embed=embed_message)

class DeleteButton(discord.ui.View):
    def __init__(self, embed_message: discord.Embed, reminder_id: int):
        super().__init__(timeout=60)
        self.embed_message = embed_message
        self.id = reminder_id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)

    @discord.ui.button(
        label="Delete",
        style=discord.ButtonStyle.red,
        emoji="<:romani_nervous:746062766825013269>")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True

        if ReminderManager.remove_reminder(interaction.user.id, self.id):
            self.embed_message.title = "Reminder DELETED <:romani_nervous:746062766825013269>"
            await interaction.response.edit_message(embed=self.embed_message, view=self)

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
