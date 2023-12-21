from helpers.database import Database

class AuthorizedUsers():
    users = set()
    numAdded = 0

    def getUserSet():
        # Pull from the database if we haven't yet
        if (len(AuthorizedUsers.users) == AuthorizedUsers.numAdded):
            userIds = Database.select("SELECT id FROM users;")
            for userId in userIds:
                AuthorizedUsers.users.add(userId[0])

        return AuthorizedUsers.users

    def addUser(userId, username):
        if userId in AuthorizedUsers.users:
            return

        AuthorizedUsers.users.add(userId)
        AuthorizedUsers.numAdded += 1

        Database.insert("""INSERT OR IGNORE INTO users VALUES ({}, "{}");""".format(userId, username))