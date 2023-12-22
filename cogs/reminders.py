import asyncio
import datetime
import discord

from discord.ext import commands
from discord.ext import tasks

from helpers.database import Database

class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminders = []
        self.lock = asyncio.Lock()
        self.getReminders.start()

    # every day, on startup time
    @tasks.loop(hours=24)
    async def getReminders(self):
        async with self.lock:
            self.reminders = Database.select("""SELECT * FROM reminders WHERE date >= datetime("now", "localtime") AND date < datetime("now", "localtime", "1 day");""")

        if not self.sendReminders.is_running():
            self.sendReminders.start()

    @tasks.loop(minutes=1)
    async def sendReminders(self):
        later = []
        async with self.lock:
            for reminder in self.reminders:
                if reminder[3] < (datetime.datetime.now() + datetime.timedelta(minutes=1)):
                    requester = self.bot.get_user(reminder[1])
                    if requester is None:
                        requester = await self.bot.fetch_user(reminder[1])

                    embedMessage = discord.Embed(title="Reminder! <:charmanderawr:837344550804127774>", description=reminder[2], color=discord.Color.og_blurple())
                    embedMessage.add_field(name="Time", value=reminder[3].strftime("%m/%d/%Y at %H:%M"))
                    buttons = SnoozeButtons(self, reminder[2])
                    buttons.message = await requester.send(embed=embedMessage, view=buttons)
                else:
                    later.append(reminder)
            self.reminders = later

    @commands.command()
    async def remind(self, ctx: commands.Context, reminder, *, args):
        timeArg = "".join(args)
        dateParam = datetime.datetime.now()

        components = timeArg.split()
        for component in components:
            lowerComponent = component.lower()
            if ":" in lowerComponent:
                parts = lowerComponent.split(":")
                dateParam = dateParam.replace(hour=int(parts[0]), minute=int(parts[1]))
                if (len(parts) == 3):
                    dateParam = dateParam.replace(second=int(parts[2]))
            elif "/" in lowerComponent:
                parts = lowerComponent.split("/")
                dateParam = dateParam.replace(month=int(parts[0]), day=int(parts[1]))
                if (len(parts) == 3):
                    dateParam = dateParam.replace(year=int(parts[2]))
            elif lowerComponent.endswith("d"):
                dateParam = dateParam + datetime.timedelta(days=int(lowerComponent[:-1]))
            elif lowerComponent.endswith("h"):
                dateParam = dateParam + datetime.timedelta(hours=int(lowerComponent[:-1]))
            elif lowerComponent.endswith("m"):
                dateParam = dateParam + datetime.timedelta(minutes=int(lowerComponent[:-1]))
            elif lowerComponent.endswith("s"):
                dateParam = dateParam + datetime.timedelta(seconds=int(lowerComponent[:-1]))

        Database.insert("""INSERT INTO reminders(userId, reminder, date) VALUES ({}, "{}", "{}");""".format(ctx.author.id, reminder, dateParam))

        if dateParam < (datetime.datetime.now() + datetime.timedelta(days=1)):
            self.reminders.append((0, ctx.author.id, reminder, dateParam))

        embedMessage = discord.Embed(title="Reminder created <:charmanderawr:837344550804127774>", description=reminder, color=discord.Color.og_blurple())
        embedMessage.add_field(name="Scheduled Time", value=dateParam.strftime("%m/%d/%Y at %H:%M"))
        await ctx.send(embed=embedMessage)

    @remind.error
    async def remind_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('The remind command takes in a reminder string and a time. ex: !remind "Send email" 12:00 <:charmanderawr:837344550804127774>')
        else:
            await ctx.send('Please keep the reminder in one string and keep all time components separate. And no AM/PM! <:charmanderawr:837344550804127774>')

    @commands.command()
    async def reminders(self, ctx: commands.Context, count=10):
        total = Database.count("reminders", """WHERE userId = {} AND date > "{}" """.format(ctx.author.id, datetime.datetime.now()))

        if total == 0:
            await ctx.send("There are no upcoming reminders <:charmanderawr:837344550804127774>")
            return

        first = Database.select("""
            SELECT reminder, date
            FROM reminders
            WHERE userId = {} AND date > "{}"
            ORDER BY date
            LIMIT {};
            """.format(ctx.author.id, datetime.datetime.now(), count))
        
        display = "\n".join(['Reminder "{}" set for {}'.format(reminder[0], reminder[1].strftime("%m/%d/%Y at %H:%M")) for reminder in first])
        embedMessage = discord.Embed(title="Upcoming reminders <:charmanderawr:837344550804127774>", description=display, color=discord.Color.og_blurple())

        if total <= count:
            await ctx.send(embed=embedMessage)
            return

        buttons = PageButtons(total, count, ctx.author.id, {0: display}, embedMessage)
        buttons.message = await ctx.send(embed=embedMessage, view=buttons)

class SnoozeButtons(discord.ui.View):
    def __init__(self, reminderInstance, reminder):
        super().__init__(timeout=120)
        self.reminderInstance = reminderInstance
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

    @discord.ui.button(label="1 hour",style=discord.ButtonStyle.secondary,emoji="⏰")
    async def delay_60_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        await self.__add_time(interaction, 60)

    async def __add_time(self: discord.ui.View, interaction: discord.Interaction, delay: int):
        for child in self.children:
            child.disabled = True

        dateParam = datetime.datetime.now() + datetime.timedelta(minutes=delay)

        Database.insert("""INSERT INTO reminders(userId, reminder, date) VALUES ({}, "{}", "{}");""".format(interaction.user.id, self.reminder, dateParam))

        if dateParam < (datetime.datetime.now() + datetime.timedelta(days=1)):
            self.reminderInstance.reminders.append((0, interaction.user, self.reminder, dateParam))

        await interaction.response.edit_message(view=self)

        embedMessage = discord.Embed(title="Reminder snoozed <:charmanderawr:837344550804127774>", description=self.reminder, color=discord.Color.og_blurple())
        embedMessage.add_field(name="Scheduled Time", value=dateParam.strftime("%m/%d/%Y at %H:%M"))
        await interaction.user.send(embed=embedMessage)

class PageButtons(discord.ui.View):
    def __init__(self, total, count, id, pages, embed: discord.Embed):
        super().__init__(timeout=60)
        self.userId = id
        self.total = total
        self.count = count
        self.index = 0
        self.pages = pages
        self.embed = embed
        self.message = None
        self.__add_buttons()

    async def on_timeout(self):
        for child in self.children:
            child.disabled = True

        await self.message.edit(view=self)

    def getPage(self):
        if not self.index in self.pages:
            reminders = Database.select("""
                SELECT reminder, date
                FROM reminders
                WHERE userId = {} AND date > "{}"
                ORDER BY date
                LIMIT {} OFFSET {};
                """.format(self.userId, datetime.datetime.now(), self.count, self.index * self.count))

            page = "\n".join(['Reminder "{}" set for {}'.format(reminder[0], reminder[1].strftime("%m/%d/%Y at %H:%M")) for reminder in reminders])

            self.pages[self.index] = page

        return self.pages[self.index]

    @discord.ui.button(style=discord.ButtonStyle.red, emoji="⬅️", disabled=True, custom_id="prev")
    async def prev_button(self, interaction: discord.Interaction, button: discord.ui.Button):
        self.index -= 1

        for child in self.children:
            child.disabled = False

        if self.index == 0:
            button.disabled = True

        self.embed.description = self.getPage()

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

            self.embed.description = self.getPage()

            await self.message.edit(embed=self.embed, view=self)
            await interaction.response.defer()
        next.callback = next_button

        self.add_item(next)


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))