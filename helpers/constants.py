import discord

COGS = {"admin", "contextmenus", "crochet", "events",
        "loops", "recipes", "reminders", "tasks", "textcommands"}
DEFAULT_ACTIVITY = discord.Activity(type=discord.ActivityType.watching, name="you 👀")
DEFAULT_EMOTE = "<:charmanderawr:837344550804127774>"
DEFAULT_LOCALE = discord.Locale.american_english
OWNER_ENV = "SQIDJI_ID"
RESOURCE_FOLDER = "phoebot_resources"
SUPPORTED_LOCALES = {discord.Locale.american_english, discord.Locale.spain_spanish}
TEST_SERVER_ENV = "DUCK_SERVER_ID"
