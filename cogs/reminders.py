import asyncio
import datetime
import discord
import os
import sqlite3

from discord.ext import commands
from discord.ext import tasks

class Reminders(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.reminders = []
        self.lock = asyncio.Lock()
        self.getReminders.start()

    # every day, on startup time
    @tasks.loop(hours=24)
    async def getReminders(self):
        package_dir = os.path.abspath(os.path.dirname(__file__))
        database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
        connection = sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cursor = connection.cursor()
        cursor.execute("""SELECT * FROM reminders WHERE date >= datetime("now", "localtime") AND date < datetime("now", "localtime", "1 day");""")

        async with self.lock:
            self.reminders = cursor.fetchall()

        cursor.close()
        connection.close()

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
                    await requester.send(embed=embedMessage)
                else:
                    later.append(reminder)
            self.reminders = later

    @commands.command()
    async def remind(self, ctx: commands.Context, reminder, *, args):
        package_dir = os.path.abspath(os.path.dirname(__file__))
        database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
        connection = sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        cursor = connection.cursor()

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

        insert = """INSERT INTO reminders(userId, reminder, date) VALUES ({}, "{}", "{}");""".format(ctx.author.id, reminder, dateParam)

        cursor.execute(insert)
        connection.commit()

        cursor.close()
        connection.close()

        if dateParam < (datetime.datetime.now() + datetime.timedelta(days=1)):
            self.reminders.append((0, ctx.author.id, reminder, dateParam))

        embedMessage = discord.Embed(title="Reminder created <:charmanderawr:837344550804127774>", description=reminder, color=discord.Color.og_blurple())
        embedMessage.add_field(name="Time", value=timeArg)
        await ctx.author.send(embed=embedMessage)

    @remind.error
    async def remind_error(self, ctx, error):
        if isinstance(error, commands.errors.MissingRequiredArgument):
            await ctx.send('The remind command takes in a reminder string and a time. ex: !remind "Send email" 12:00 <:charmanderawr:837344550804127774>')
        else:
            await ctx.send('Please keep the reminder in one string and keep all time components separate. And no AM/PM! <:charmanderawr:837344550804127774>')

async def setup(bot: commands.Bot):
    await bot.add_cog(Reminders(bot))