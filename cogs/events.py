from discord.ext import commands
from datetime import datetime

from helpers.authorizedusers import AuthorizedUsers

class Events(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    @commands.Cog.listener()
    async def on_message(self, message):
        if message.author == self.bot.user:
            return
        
        if not AuthorizedUsers.isAuthorized(message.author.id):
            return

        elif message.content.lower().startswith("hi") or message.content.lower().startswith("hello") :
            await message.reply("Hello! <:charmanderawr:837344550804127774>", mention_author=True)

    @commands.Cog.listener()
    async def on_presence_update(self, before, after):
        # Ask to play OW or Val if I started playing
        if (before.id != 274397067177361408) or datetime.now() > datetime.now().replace(hour=19, minute=0) or datetime.now() < datetime.now().replace(hour=7, minute=0):
            return
        
        oldPlaying = [game.name for game in before.activities if str(game.type) == "ActivityType.playing"]
        newPlaying = [game.name for game in after.activities if str(game.type) == "ActivityType.playing" and game.name not in oldPlaying]
        
        channel = self.bot.get_channel(874822355334094858)
        if channel is None:
            channel = await self.bot.fetch_channel(874822355334094858)

        if "Overwatch 2" in newPlaying:
            await channel.send("<@559828298973184011> want to do some watching over?")
        if "Valorant" in newPlaying:
            await channel.send("<@559828298973184011> Val?")

async def setup(bot: commands.Bot):
    await bot.add_cog(Events(bot))