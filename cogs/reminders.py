import datetime
import os
from typing import List, Optional

import asyncio
import discord
from discord import app_commands
from discord.ext import commands
from discord.ext import tasks

from helpers import constants
from helpers.database import Database
from helpers.pagebuttons import PageButtons

class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminder_cache = []
        self.lock = asyncio.Lock()
        self.get_reminders.start()

    async def cog_unload(self):
        self.get_reminders.cancel()
        self.send_reminders.cancel()

    # every day, on startup time
    @tasks.loop(hours=24)
    async def get_reminders(self):
        async with self.lock:
            self.reminder_cache = Database.select("*", "reminders", """WHERE date >= datetime("now", "localtime") AND date < datetime("now", "localtime", "1 day")""")

        if not self.send_reminders.is_running():
            self.send_reminders.start()

    @tasks.loop(minutes=1)
    async def send_reminders(self):
        later = []
        async with self.lock:
            for reminder in self.reminder_cache:
                if reminder[3] < (datetime.datetime.now() + datetime.timedelta(minutes=1)):
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
                else:
                    later.append(reminder)
            self.reminder_cache = later

    @commands.hybrid_group(
        help="Get your future reminders",
        fallback="get"
    )
    @app_commands.describe(
        count="Number of reminders per page",
        show_id="Whether to show the reminder ID"
    )
    async def reminders(self, ctx: commands.Context,
        count: Optional[int] =
            commands.parameter(default=10, description="Number of reminders per page"),
        show_id: bool =
            commands.parameter(default=False, description="Whether to show the reminder ID")):

        now = datetime.datetime.now()
        total = Database.count(
            "reminders",
            f"""WHERE userId = {ctx.author.id} AND date > "{now}" """)

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
        help="Set a reminder"
    )
    @app_commands.describe(
        reminder="What do you want to be reminded of?",
        when="When do you want to be reminded?"
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

        Database.insert(
            "reminders(userId, reminder, date)",
            f"""{ctx.author.id}, "{reminder}", "{date_param}" """)

        reminder_id = Database.select(
            "id", "reminders",
            f"""WHERE date = "{date_param}" AND reminder = "{reminder}" AND userId = {ctx.author.id}""")[0][0]

        if date_param < (datetime.datetime.now() + datetime.timedelta(days=1)):
            async with self.lock:
                self.reminder_cache.append((reminder_id, ctx.author.id, reminder, date_param))

        embed_message = discord.Embed(
            title=f"Reminder created {constants.DEFAULT_EMOTE}",
            description=reminder,
            color=discord.Color.og_blurple())
        embed_message.add_field(
            name="Scheduled Time",
            value=discord.utils.format_dt(date_param))

        buttons = DeleteButton(self, embed_message, reminder_id)
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
            "tomorrow": 
                datetime.datetime.now().replace(hour=10, minute=0) +
                datetime.timedelta(days=1),
            "tonight":
                datetime.datetime.now().replace(hour=20, minute=0) +
                datetime.timedelta(days=(1 if (datetime.datetime.now().hour >= 20) else 0)),
            "midnight":
                datetime.datetime.now().replace(hour=0, minute=0) +
                datetime.timedelta(days=1),
            "noon":
                datetime.datetime.now().replace(hour=12, minute=0) +
                datetime.timedelta(days=(1 if (datetime.datetime.now().hour >= 12) else 0))
        }
        matched_times.extend([
            app_commands.Choice(name=day, value=time.strftime("%x %X"))
            for day, time in days.items() if current.lower() in day.lower()
        ])

        return matched_times

    @set.error
    async def remind_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send(f'The remind command takes in a reminder string and a time. ex: !remind "Send email" 12:00 {constants.DEFAULT_EMOTE}')
        else:
            await ctx.send(f'Please keep the reminder in one string and keep all time components separate. And no AM/PM! {constants.DEFAULT_EMOTE}')

    @reminders.command(
        help="Get the contents of the internal reminder list"
    )
    @commands.is_owner()
    @app_commands.default_permissions()
    @app_commands.guilds(int(os.getenv(constants.TEST_SERVER_ENV)))
    async def debug(self, ctx: commands.Context):
        await ctx.send(self.reminder_cache)

    @reminders.command(
        help="Delete a reminder"
    )
    @app_commands.describe(
        reminder_id="The ID of the reminder being deleted"
    )
    async def delete(self, ctx: commands.Context,
        reminder_id: int = commands.parameter(description="The ID of the reminder being deleted")):

        reminders = Database.select(
            "*", "reminders",
            f"WHERE id = {reminder_id} and userId = {ctx.author.id}")
        if len(reminders) == 0:
            await ctx.send(f"You can't delete reminders that aren't yours! {constants.DEFAULT_EMOTE}")
            return

        Database.delete("reminders", f"WHERE id = {reminder_id}")

        await self.remove_from_reminders(reminder_id)

        await ctx.send(f"Ok, deleted reminder {reminder_id} {constants.DEFAULT_EMOTE}")

    @delete.autocomplete("reminder_id")
    async def delete_autocomplete(self, interaction: discord.Interaction,
        current: int,) -> List[app_commands.Choice[int]]:

        top_5_ids = Database.select(
            "id", "reminders",
            f"""WHERE userId = {interaction.user.id} AND date > "{datetime.datetime.now()}" 
                ORDER BY date 
                LIMIT 5
            """)

        matched = [
            app_commands.Choice(name=reminder_id[0], value=reminder_id[0])
            for reminder_id in top_5_ids if str(current) in str(reminder_id[0])
        ]

        return matched

    async def remove_from_reminders(self, reminder_id: int):
        """Removes the reminder with the provided id from the cache

        Args:
            id (int): The reminder ID
        """
        async with self.lock:
            for i in range(len(self.reminder_cache)):
                if self.reminder_cache[i][0] == reminder_id:
                    self.reminder_cache.remove(self.reminder_cache[i])
                    break

    def build_reminders_embed(self, user_id: int,
        time_now: datetime.datetime, count: int,
        index: int, total:int, show_id: bool) -> discord.Embed:

        # Don't want to load math module into memory for one function
        num_pages = int(total / count) + (1 if total % count != 0 else 0)

        reminder_page = Database.select(
            "id, reminder, date", "reminders", 
            f"""WHERE userId = {user_id} AND date > "{time_now}" 
                ORDER BY date 
                LIMIT {count} OFFSET {index * count}
            """)

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

        Database.insert(
            "reminders(userId, reminder, date)",
            f"""{interaction.user.id}, "{self.reminder}", "{date_param}" """)

        reminder_id = Database.select(
            "id", "reminders",
            f"""WHERE date = "{date_param}" 
            AND reminder = "{self.reminder}" 
            AND userId = {interaction.user.id}""")[0][0]

        if date_param < (datetime.datetime.now() + datetime.timedelta(days=1)):
            self.reminder_instance.reminder_cache.append(
                (reminder_id, interaction.user.id, self.reminder, date_param))

        embed_message = discord.Embed(
            title=f"Reminder snoozed {constants.DEFAULT_EMOTE}",
            description=self.reminder,
            color=discord.Color.og_blurple())
        embed_message.add_field(
            name="Scheduled Time",
            value=discord.utils.format_dt(date_param))
        await interaction.response.edit_message(view=self, embed=embed_message)

class DeleteButton(discord.ui.View):
    def __init__(self, reminder_instance: Reminders, embed_message: discord.Embed, reminder_id: int):
        super().__init__(timeout=60)
        self.reminder_instance = reminder_instance
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

        Database.delete("reminders", f"WHERE id = {self.id}")

        await self.reminder_instance.remove_from_reminders(self.id)

        self.embed_message.title = "Reminder DELETED <:romani_nervous:746062766825013269>"
        await interaction.response.edit_message(embed=self.embed_message, view=self)

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
