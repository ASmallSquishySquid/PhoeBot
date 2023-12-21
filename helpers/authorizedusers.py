import os
import sqlite3

class AuthorizedUsers():
    users = set()
    connection = None

    def getUserSet():
        if (len(AuthorizedUsers.users) == 0):
            if (AuthorizedUsers.connection == None):
                package_dir = os.path.abspath(os.path.dirname(__file__))
                database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
                AuthorizedUsers.connection = sqlite3.connect(database_path)
           
            cursor = AuthorizedUsers.connection.cursor()
            cursor.execute("""SELECT id FROM users;""")
            return set(cursor.fetchall())
        else:
            return AuthorizedUsers.users
    
    def addUser(userId, username):
        AuthorizedUsers.users.add(userId)
        insert = """INSERT INTO users VALUES ({}, "{}");""".format(userId, username)

        if (AuthorizedUsers.connection == None):
            package_dir = os.path.abspath(os.path.dirname(__file__))
            database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
            AuthorizedUsers.connection = sqlite3.connect(database_path)
        cursor = AuthorizedUsers.connection.cursor()
        cursor.execute(insert)
        AuthorizedUsers.connection.commit()