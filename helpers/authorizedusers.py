import os
import sqlite3

class AuthorizedUsers():
    users = set()
    connection = None
    numAdded = 0

    def getUserSet():
        # Pull from the database if we haven't yet
        if (len(AuthorizedUsers.users) == AuthorizedUsers.numAdded):
            if (AuthorizedUsers.connection == None):
                package_dir = os.path.abspath(os.path.dirname(__file__))
                database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
                AuthorizedUsers.connection = sqlite3.connect(database_path)

            cursor = AuthorizedUsers.connection.cursor()
            cursor.execute("""SELECT id FROM users;""")

            for userId in cursor.fetchall():
                AuthorizedUsers.users.add(userId[0])

        return AuthorizedUsers.users

    def addUser(userId, username):
        AuthorizedUsers.users.add(userId)

        AuthorizedUsers.numAdded += 1

        insert = """INSERT INTO users VALUES ({}, "{}");""".format(userId, username)

        if (AuthorizedUsers.connection == None):
            package_dir = os.path.abspath(os.path.dirname(__file__))
            database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
            AuthorizedUsers.connection = sqlite3.connect(database_path)

        cursor = AuthorizedUsers.connection.cursor()
        cursor.execute(insert)
        AuthorizedUsers.connection.commit()