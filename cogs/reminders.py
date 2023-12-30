import asyncio
import datetime
import discord

from discord.ext import commands
from discord.ext import tasks

from helpers.database import Database

class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminder_cache = []
        self.lock = asyncio.Lock()
        self.get_reminders.start()

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

                    embed_message = discord.Embed(title="Reminder! <:charmanderawr:837344550804127774>", description=reminder[2], color=discord.Color.og_blurple())
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
    async def reminders(self, ctx: commands.Context, count: int = commands.parameter(default=10, description="Number of reminders per page")):
        now = datetime.datetime.now()
        total = Database.count("reminders", f"""WHERE userId = {ctx.author.id} AND date > "{now}" """)

        if total == 0:
            await ctx.send("There are no upcoming reminders <:charmanderawr:837344550804127774>")
            return

        first = Database.select("id, reminder, date", "reminders", f"""WHERE userId = {ctx.author.id} AND date > "{now}" ORDER BY date LIMIT {count}""")

        display = "\n".join([f'{reminder[0]}: Reminder "{reminder[1]}" set for {reminder[2].strftime("%m/%d/%Y at %H:%M")}' for reminder in first])
        embed_message = discord.Embed(title="Upcoming reminders <:charmanderawr:837344550804127774>", description=display, color=discord.Color.og_blurple())

        if total <= count:
            await ctx.send(embed=embed_message)
            return

        buttons = PageButtons(total, count, now, ctx.author.id, {0: display}, embed_message)
        buttons.message = await ctx.send(embed=embed_message, view=buttons)

    @reminders.command(
        help="Set a reminder",
        aliases=["reminder"]
    )
    async def set(self, ctx: commands.Context, 
        reminder: str = commands.parameter(description="What do you want to be reminded of?"), *, 
        args: str = commands.parameter(displayed_name="time", description="When do you want to be reminded?", default="1h")
    ):
        time_arg = "".join(args)
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

        embed_message = discord.Embed(title="Reminder created <:charmanderawr:837344550804127774>", description=reminder, color=discord.Color.og_blurple())
        embed_message.add_field(name="Scheduled Time", value=date_param.strftime("%m/%d/%Y at %H:%M"))
        buttons = DeleteButton(self, embed_message, id)
        buttons.message = await ctx.send(embed=embed_message, view=buttons)

    @set.error
    async def remind_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('The remind command takes in a reminder string and a time. ex: !remind "Send email" 12:00 <:charmanderawr:837344550804127774>')
        else:
            await ctx.send('Please keep the reminder in one string and keep all time components separate. And no AM/PM! <:charmanderawr:837344550804127774>')

    @reminders.command(
        help="Get the contents of the internal reminder list",
        hidden=True
    )
    async def debug(self, ctx: commands.Context):
        await ctx.send(self.reminder_cache)

    @reminders.command(
        help="Delete a reminder"
    )
    async def delete(self, ctx: commands.Context, id: int = commands.parameter(description="The ID of the reminder being deleted")):
        reminders = Database.select("*", "reminders", f"WHERE id = {id} and userId = {ctx.author.id}")
        if len(reminders) == 0:
            await ctx.send("You can't delete reminders that aren't yours! <:charmanderawr:837344550804127774>")
            return

        Database.delete("reminders", f"WHERE id = {id}")

        await self.remove_from_reminders(id)

        await ctx.send(f"Ok, deleted reminder {id} <:charmanderawr:837344550804127774>")

    async def remove_from_reminders(self, id):
        async with self.lock:
            for i in range(len(self.reminder_cache)):
                if self.reminder_cache[i][0] == id:
                    self.reminder_cache.remove(self.reminder_cache[i])
                    break


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

        embed_message = discord.Embed(title="Reminder snoozed <:charmanderawr:837344550804127774>", description=self.reminder, color=discord.Color.og_blurple())
        embed_message.add_field(name="Scheduled Time", value=date_param.strftime("%m/%d/%Y at %H:%M"))
        await interaction.response.edit_message(view=self, embed=embed_message)

class PageButtons(discord.ui.View):
    def __init__(self, total: int, count: int, now: datetime, id: int, pages: dict, embed: discord.Embed):
        super().__init__(timeout=60)
        self.userId = id
        self.total = total
        self.count = count
        self.now = now
        self.index = 0
        self.pages = pages
        self.embed = embed
        self.message = None
        self.__add_buttons()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)

    def get_page(self):
        if not self.index in self.pages:
            reminders = Database.select(
                "reminder, date", "reminders", 
                f"""WHERE userId = {self.userId} AND date > "{self.now}" 
                    ORDER BY date 
                    LIMIT {self.count} OFFSET {self.index * self.count}
                """)

            page = "\n".join([f'Reminder "{reminder[0]}" set for {reminder[1].strftime("%m/%d/%Y at %H:%M")}' for reminder in reminders])

            self.pages[self.index] = page

        return self.pages[self.index]

    @discord.ui.button(style=discord.ButtonStyle.red, emoji="⬅️", disabled=True, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1

        for child in self.children:
            child.disabled = False

        if self.index == 0:
            button.disabled = True

        self.embed.description = self.get_page()

        await self.message.edit(embed=self.embed, view=self)
        await interaction.response.defer()

    def __add_buttons(self):
        next = discord.ui.Button(style=discord.ButtonStyle.green, emoji="➡️", custom_id="next", disabled=(self.total <= self.count))

        async def next_button(interaction: discord.Interaction):
            self.index += 1

            for child in self.children:
                child.disabled = False

            if self.count * (self.index + 1) >= self.total:
                next.disabled = True

            self.embed.description = self.get_page()

            await self.message.edit(embed=self.embed, view=self)
            await interaction.response.defer()
        next.callback = next_button

        self.add_item(next)

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
