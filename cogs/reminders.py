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
                    embedMessage = discord.Embed(title="Reminder! <:charmanderawr:837344550804127774>", description=reminder[2], color=discord.Color.og_blurple())
                    embedMessage.add_field(name="Time", value=reminder[3].strftime("%m/%d/%Y, %H:%M"))
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
        embedMessage.add_field(name="Scheduled Time", value=dateParam.strftime("%m/%d/%Y, %H:%M"))
        await ctx.send(embed=embedMessage)

    @remind.error
    async def remind_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('The remind command takes in a reminder string and a time. ex: !remind "Send email" 12:00 <:charmanderawr:837344550804127774>')
        else:
            await ctx.send('Please keep the reminder in one string and keep all time components separate. And no AM/PM! <:charmanderawr:837344550804127774>')

class SnoozeButtons(discord.ui.View):
    def __init__(self, reminderInstance, reminder):
        super().__init__(timeout=60)
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
        embedMessage.add_field(name="Scheduled Time", value=dateParam.strftime("%m/%d/%Y, %H:%M"))
        await interaction.user.send(embed=embedMessage)


async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))