from helpers.database import Database

class AuthorizedUsers():
    users = set()
    UNAUTHORIZED_MESSAGE = "Sorry, I don't talk to strangers <:mmSweatUhhMocha:764772302403272704>"

    def startup():
        """Builds the authorized user cache"""
        userIds = Database.select("id", "users")
        for userId in userIds:
            AuthorizedUsers.users.add(userId[0])

    def get_user_set() -> set:
        """Get the authorized users in the cache

        Returns:
            set: The set of user IDs
        """
        return AuthorizedUsers.users

    def add_user(userId: int, username: str) -> None:
        """Add a user to the authorized users list

        Args:
            userId (int): The user ID
            username (str): A recognizable username
        """
        if userId in AuthorizedUsers.users:
            return

        AuthorizedUsers.users.add(userId)
        Database.insert("users", f"""{userId}, "{username}" """, True)
    
    def remove_user(userId: int):
        """Removes a user from the authorized users list

        Args:
            userId (int): the user ID
        """
        if not userId in AuthorizedUsers.users:
            return
        
        AuthorizedUsers.users.remove(userId)
        Database.delete("users", f"WHERE id={userId}")

    def is_authorized(userId: int) -> bool:
        """Checks if a user is authorized

        Args:
            userId (int): The user ID

        Returns:
            bool: `True` if the user is authorized, `False` otherwise
        """
        return userId in AuthorizedUsers.users