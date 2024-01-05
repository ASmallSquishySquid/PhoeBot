import discord
import os

from datetime import datetime
from discord.ext import commands

from helpers.authorizedusers import AuthorizedUsers

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return

        if not AuthorizedUsers.is_authorized(message.author.id):
            return

        elif message.content.lower().startswith("hi") or message.content.lower().startswith("hello") :
            await message.reply("Hello! <:charmanderawr:837344550804127774>", mention_author=True)

    @commands.Cog.listener()
    async def on_presence_update(self, before: discord.Member, after: discord.Member):
        if (before.id != int(os.getenv("SQIDJI_ID"))):
            return

        # Did I start/stop developing the bot?
        is_editing_before = any(activity.name == "Visual Studio Code" and activity.state and "PhoeBot" in activity.state for activity in before.activities)
        is_editing_after = any(activity.name == "Visual Studio Code" and activity.state and "PhoeBot" in activity.state for activity in after.activities)

        if (is_editing_before and not is_editing_after):
            await self.bot.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="you 👀"))

        if (not is_editing_before and is_editing_after):
            await self.bot.change_presence(activity=discord.CustomActivity(name="Under construction 🛠️"), status=discord.Status.dnd)

        # Ask to play OW or Val if I started playing
        if datetime.now() < datetime.now().replace(hour=19, minute=0) and datetime.now() > datetime.now().replace(hour=7, minute=0):
            channel = self.bot.get_channel(int(os.getenv("DUCK_CHANNEL_ID")))
            if channel is None:
                channel = await self.bot.fetch_channel(int(os.getenv("DUCK_CHANNEL_ID")))

            old_playing = [game.name for game in before.activities if str(game.type) == "ActivityType.playing"]
            new_playing = [game.name for game in after.activities if str(game.type) == "ActivityType.playing" and game.name not in old_playing]

            if "Overwatch 2" in new_playing:
                await channel.send("<@559828298973184011> want to do some watching over?")

            if "Valorant" in new_playing:
                await channel.send("<@559828298973184011> Val?")

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))