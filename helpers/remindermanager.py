import datetime

from helpers.database import Database

class ReminderManager():
    reminder_cache = []

    @classmethod
    def add_reminder(cls, reminder: str, date: datetime.datetime, author_id: int) -> int:
        """Stores a reminder.

        Args:
            reminder (str): The reminder
            date (datetime.datetime): The time
            author_id (int): The author

        Returns:
            int: The reminder ID
        """
        Database.insert(
            "reminders(userId, reminder, date)",
            f"""{author_id}, "{reminder}", "{date}" """)

        reminder_id = Database.select(
            "id", "reminders",
            f"""WHERE date = "{date}" AND reminder = "{reminder}" AND userId = {author_id}""")[0][0]

        if date < (datetime.datetime.now() + datetime.timedelta(days=1)):
            cls.reminder_cache.append((reminder_id, author_id, reminder, date))

        return reminder_id

    @classmethod
    def get_cache(cls) -> list:
        """Returns:
            list: The reminder cache
        """
        return cls.reminder_cache

    @staticmethod
    def get_reminder_page(user_id: int, time: datetime.datetime, count: int, index: int) -> list:
        """Get a page of reminders

        Args:
            user_id (int): The user's ID
            time (datetime.datetime): The minimum time
            count (int): The number of reminders per page
            index (int): The page number

        Returns:
            list: A list of reminders
        """
        return Database.select(
            "id, reminder, date", "reminders", 
            f"""WHERE userId = {user_id} AND date > "{time}" 
                ORDER BY date 
                LIMIT {count} OFFSET {index * count}
            """)

    @classmethod
    def get_all_upcoming_reminders(cls) -> list:
        """Gets the reminders coming up in the next minute

        Returns:
            list: The upcoming reminders
        """
        later = []
        upcoming = []
        for reminder in cls.reminder_cache:
            if reminder[3] < (datetime.datetime.now() + datetime.timedelta(minutes=1)):
                upcoming.append(reminder)
            else:
                later.append(reminder)

        cls.reminder_cache = later
        return upcoming

    @staticmethod
    def get_upcoming_reminders_count(user_id: int) -> int:
        """
        Args:
            user_id (int): The user's id

        Returns:
            int: The number of upcoming reminders
        """
        return Database.count(
            "reminders",
            f"""WHERE userId = {user_id} AND date > "{datetime.datetime.now()}" """)

    @classmethod
    def rebuild(cls):
        """rebuilds the reminder cache"""
        cls.reminder_cache = Database.select(
            "*", "reminders",
            """WHERE date >= datetime("now", "localtime") AND date < datetime("now", "localtime", "1 day")""")

    @classmethod
    def remove_reminder(cls, user_id: int, reminder_id: int) -> bool:
        """Remove a reminder.

        Args:
            reminder_id (int): The id of the reminder
        """
        reminders = Database.select(
            "*", "reminders",
            f"WHERE id = {reminder_id} and userId = {user_id}")
        if len(reminders) == 0:
            return False

        Database.delete("reminders", f"WHERE id = {reminder_id}")

        for i in range(len(cls.reminder_cache)):
            if cls.reminder_cache[i][0] == reminder_id:
                cls.reminder_cache.remove(cls.reminder_cache[i])
                break

        return True
