from helpers.database import Database

class AuthorizedUsers():
    users = set()
    UNAUTHORIZED_MESSAGE = "Sorry, I don't talk to strangers <:mmSweatUhhMocha:764772302403272704>"

    def startup():
        userIds = Database.select("id", "users")
        for userId in userIds:
            AuthorizedUsers.users.add(userId[0])

    def get_user_set() -> set:
        return AuthorizedUsers.users

    def add_user(userId: int, username: str) -> None:
        if userId in AuthorizedUsers.users:
            return

        AuthorizedUsers.users.add(userId)
        Database.insert("users", f"""{userId}, "{username}" """, True)
    
    def remove_user(userId: int):
        if not userId in AuthorizedUsers.users:
            return
        
        AuthorizedUsers.users.remove(userId)
        Database.delete("users", f"WHERE id={userId}")

    def is_authorized(userId: int) -> bool:
        return userId in AuthorizedUsers.users