from helpers.database import Database

class AuthorizedUsers():
    users = set()
    unauthorizedMessage = "Sorry, I don't talk to strangers <:mmSweatUhhMocha:764772302403272704>"

    def startup():
        userIds = Database.select("id", "users")
        for userId in userIds:
            AuthorizedUsers.users.add(userId[0])

    def getUserSet() -> set:
        return AuthorizedUsers.users

    def addUser(userId: int, username: str) -> None:
        if userId in AuthorizedUsers.users:
            return

        AuthorizedUsers.users.add(userId)
        Database.insert("users", """{}, "{}" """.format(userId, username), True)
    
    def removeUser(userId: int):
        if not userId in AuthorizedUsers.users:
            return
        
        AuthorizedUsers.users.remove(userId)
        Database.delete("users", "WHERE id={}".format(userId))

    def isAuthorized(userId: int) -> bool:
        return userId in AuthorizedUsers.users