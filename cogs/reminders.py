import asyncio
import datetime
import discord
import os

import helpers.constants as constants

from discord import app_commands
from discord.ext import commands
from helpers.database import Database
from typing import List
from helpers.pagebuttons import PageButtons
from discord.ext import tasks

class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminder_cache = []
        self.lock = asyncio.Lock()
        self.get_reminders.start()

    def cog_unload(self):
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

                    embed_message = discord.Embed(title=f"Reminder! {constants.DEFAULT_EMOTE}", description=reminder[2], color=discord.Color.og_blurple())
                    embed_message.add_field(name="Time", value=reminder[3].strftime("%m/%d/%Y at %H:%M"))
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
        count="Number of reminders per page"
    )
    async def reminders(self, ctx: commands.Context, count: int = commands.parameter(default=10, description="Number of reminders per page")):
        now = datetime.datetime.now()
        total = Database.count("reminders", f"""WHERE userId = {ctx.author.id} AND date > "{now}" """)

        if total == 0:
            await ctx.send(f"There are no upcoming reminders {constants.DEFAULT_EMOTE}")
            return

        embed_message = self.build_reminders_embed(ctx.author.id, now, count, 0, total)

        if total <= count:
            await ctx.send(embed=embed_message)
            return

        def embed_builder_callback(index: int, total: int) -> discord.Embed:
            return self.build_reminders_embed(ctx.author.id, now, count, index, total)

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
        when: str = commands.parameter(displayed_name="time", description="When do you want to be reminded?", default="1h")
    ):
        time_arg = "".join(when)
        date_param = datetime.datetime.now()

        components = time_arg.split()
        for component in components:
            lower_component = component.lower()
            if ":" in lower_component:
                parts = lower_component.split(":")
                date_param = date_param.replace(hour=int(parts[0]), minute=int(parts[1]))
                if (len(parts) == 3):
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

                if (len(parts) == 3):
                    year=int(parts[2])
                    # Fix two digit years
                    if len(parts[2]) == 2:
                        year += 2000
                    date_param = date_param.replace(year=year)
            elif lower_component.endswith("d"):
                date_param = date_param + datetime.timedelta(days=int(lower_component[:-1]))
            elif lower_component.endswith("h"):
                date_param = date_param + datetime.timedelta(hours=int(lower_component[:-1]))
            elif lower_component.endswith("m"):
                date_param = date_param + datetime.timedelta(minutes=int(lower_component[:-1]))
            elif lower_component.endswith("s"):
                date_param = date_param + datetime.timedelta(seconds=int(lower_component[:-1]))

        Database.insert("reminders(userId, reminder, date)", f"""{ctx.author.id}, "{reminder}", "{date_param}" """)

        id = Database.select("id", "reminders", f"""WHERE date = "{date_param}" AND reminder = "{reminder}" AND userId = {ctx.author.id}""")[0][0]

        if date_param < (datetime.datetime.now() + datetime.timedelta(days=1)):
            async with self.lock:
                self.reminder_cache.append((id, ctx.author.id, reminder, date_param))

        embed_message = discord.Embed(title=f"Reminder created {constants.DEFAULT_EMOTE}", description=reminder, color=discord.Color.og_blurple())
        embed_message.add_field(name="Scheduled Time", value=date_param.strftime("%m/%d/%Y at %H:%M"))
        buttons = DeleteButton(self, embed_message, id)
        buttons.message = await ctx.send(embed=embed_message, view=buttons)

    @set.autocomplete("when")
    async def reminder_autocomplete(self, interaction: discord.Interaction, current: str,) -> List[app_commands.Choice[str]]:
        times = ["10:00", "1d", "1h", "15m"]
        matched_times = [
            app_commands.Choice(name=time, value=time)
            for time in times if current.lower() in time.lower()
        ]

        days = {
            "tomorrow": (datetime.datetime.now().replace(hour=10, minute=0) + datetime.timedelta(days=1)), 
            "tonight": (datetime.datetime.now().replace(hour=20, minute=0) + datetime.timedelta(days=(1 if (datetime.datetime.now().hour >= 20) else 0))),
            "midnight": (datetime.datetime.now().replace(hour=0, minute=0) + datetime.timedelta(days=1)),
            "noon": (datetime.datetime.now().replace(hour=12, minute=0) + datetime.timedelta(days=(1 if (datetime.datetime.now().hour >= 12) else 0)))
        }
        matched_times.extend([
            app_commands.Choice(name=time, value=days[time].strftime("%m/%d %H:%M"))
            for time in days if current.lower() in time.lower()
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
        id="The ID of the reminder being deleted"
    )
    async def delete(self, ctx: commands.Context, id: int = commands.parameter(description="The ID of the reminder being deleted")):
        reminders = Database.select("*", "reminders", f"WHERE id = {id} and userId = {ctx.author.id}")
        if len(reminders) == 0:
            await ctx.send(f"You can't delete reminders that aren't yours! {constants.DEFAULT_EMOTE}")
            return

        Database.delete("reminders", f"WHERE id = {id}")

        await self.remove_from_reminders(id)

        await ctx.send(f"Ok, deleted reminder {id} {constants.DEFAULT_EMOTE}")

    async def remove_from_reminders(self, id: int):
        """Removes the reminder with the provided id from the cache

        Args:
            id (int): The reminder ID
        """        
        async with self.lock:
            for i in range(len(self.reminder_cache)):
                if self.reminder_cache[i][0] == id:
                    self.reminder_cache.remove(self.reminder_cache[i])
                    break

    def build_reminders_embed(self, userId: int, time_now: datetime.datetime, count: int, index: int, total:int) -> discord.Embed:
        # Don't want to load math module into memory for one function
        num_pages = int(total / count) + (1 if total % count != 0 else 0)

        reminder_page = Database.select(
            "id, reminder, date", "reminders", 
            f"""WHERE userId = {userId} AND date > "{time_now}" 
                ORDER BY date 
                LIMIT {count} OFFSET {index * count}
            """)

        page = "\n".join([f'{reminder[0]}: Reminder "{reminder[1]}" set for {reminder[2].strftime("%m/%d/%Y at %H:%M")}' for reminder in reminder_page])
        embed = discord.Embed(title=f"Upcoming reminders {constants.DEFAULT_EMOTE}", description=page, color=discord.Color.og_blurple())
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

    @discord.ui.button(label="15 minutes", style=discord.ButtonStyle.primary, emoji="<a:mochaSleep:764675744819314738>")
    async def delay_15_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.__add_time(interaction, 15)

    @discord.ui.button(label="30 minutes", style=discord.ButtonStyle.secondary, emoji="⏰")
    async def delay_30_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.__add_time(interaction, 30)

    @discord.ui.button(label="1 hour", style=discord.ButtonStyle.secondary, emoji="⏰")
    async def delay_60_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.__add_time(interaction, 60)

    async def __add_time(self: discord.ui.View, interaction: discord.Interaction, delay: int):
        for child in self.children:
            child.disabled = True

        date_param = datetime.datetime.now() + datetime.timedelta(minutes=delay)

        Database.insert("reminders(userId, reminder, date)", f"""{interaction.user.id}, "{self.reminder}", "{date_param}" """)

        id = Database.select("id", "reminders", f"""WHERE date = "{date_param}" AND reminder = "{self.reminder}" AND userId = {interaction.user.id}""")[0][0]

        if date_param < (datetime.datetime.now() + datetime.timedelta(days=1)):
            self.reminder_instance.reminder_cache.append((id, interaction.user.id, self.reminder, date_param))

        embed_message = discord.Embed(title=f"Reminder snoozed {constants.DEFAULT_EMOTE}", description=self.reminder, color=discord.Color.og_blurple())
        embed_message.add_field(name="Scheduled Time", value=date_param.strftime("%m/%d/%Y at %H:%M"))
        await interaction.response.edit_message(view=self, embed=embed_message)

class DeleteButton(discord.ui.View):
    def __init__(self, reminder_instance: Reminders, embed_message: discord.Embed, id: int):
        super().__init__(timeout=60)
        self.reminder_instance = reminder_instance
        self.embed_message = embed_message
        self.id = id

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)

    @discord.ui.button(label="Delete", style=discord.ButtonStyle.red, emoji="<:romani_nervous:746062766825013269>")
    async def delete_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        button.disabled = True

        Database.delete("reminders", f"WHERE id = {self.id}")

        await self.reminder_instance.remove_from_reminders(self.id)

        self.embed_message.title = "Reminder DELETED <:romani_nervous:746062766825013269>"
        await interaction.response.edit_message(embed=self.embed_message, view=self)

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))
