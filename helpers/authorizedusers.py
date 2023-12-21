import os
import sqlite3

class AuthorizedUsers():
    def __init__(self):
        self.users = set()
        self.connection = None

    def getUserSet(self):
        if (len(self.users) == 0):
            if (self.connection == None):
                package_dir = os.path.abspath(os.path.dirname(__file__))
                database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
                self.connection = sqlite3.connect(database_path)
           
            cursor = self.connection.cursor()
            cursor.execute("""SELECT id FROM users;""")
            return set(cursor.fetchall())
        else:
            return self.users
    
    def addUser(self, userId, username):
        self.users.add(userId)
        insert = """INSERT INTO users VALUES ({}, "{}");""".format(userId, username)

        if (self.connection == None):
            package_dir = os.path.abspath(os.path.dirname(__file__))
            database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
            self.connection = sqlite3.connect(database_path)
        cursor = self.connection.cursor()
        cursor.execute(insert)
        self.connection.commit()