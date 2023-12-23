from helpers.database import Database

class AuthorizedUsers():
    users = set()
    numAdded = 0

    def getUserSet() -> set:
        # Pull from the database if we haven't yet
        if (len(AuthorizedUsers.users) == AuthorizedUsers.numAdded):
            userIds = Database.select("id", "users")
            for userId in userIds:
                AuthorizedUsers.users.add(userId[0])

        return AuthorizedUsers.users

    def addUser(userId: int, username: str) -> None:
        if userId in AuthorizedUsers.users:
            return

        AuthorizedUsers.users.add(userId)
        AuthorizedUsers.numAdded += 1

        Database.insert("users", """{}, "{}" """.format(userId, username), True)