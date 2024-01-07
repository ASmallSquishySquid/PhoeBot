from helpers.database import Database

class AuthorizedUsers():
    users = set()
    UNAUTHORIZED_MESSAGE = "Sorry, I don't talk to strangers <:mmSweatUhhMocha:764772302403272704>"

    @classmethod
    def startup(cls):
        """Builds the authorized user cache"""
        user_ids = Database.select("id", "users")
        for user_id in user_ids:
            AuthorizedUsers.users.add(user_id[0])

    @classmethod
    def get_user_set(cls) -> set:
        """Get the authorized users in the cache

        Returns:
            set: The set of user IDs
        """
        return cls.users

    @classmethod
    def add_user(cls, user_id: int, username: str) -> None:
        """Add a user to the authorized users list

        Args:
            user_id (int): The user ID
            username (str): A recognizable username
        """
        if user_id in cls.users:
            return

        cls.users.add(user_id)
        Database.insert("users", f"""{user_id}, "{username}" """, True)

    @classmethod
    def remove_user(cls, user_id: int):
        """Removes a user from the authorized users list

        Args:
            user_id (int): the user ID
        """
        if not user_id in cls.users:
            return

        cls.users.remove(user_id)
        Database.delete("users", f"WHERE id={user_id}")

    @classmethod
    def is_authorized(cls, user_id: int) -> bool:
        """Checks if a user is authorized

        Args:
            user_id (int): The user ID

        Returns:
            bool: `True` if the user is authorized, `False` otherwise
        """
        return user_id in cls.users
