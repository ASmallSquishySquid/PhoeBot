import os
import sqlite3

class Database():
    connection = None

    def select(query):
        if Database.connection == None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute(query)

        results = list(cursor.fetchall())

        cursor.close()

        return results

    def insert(query):
        if Database.connection == None:
            Database.connect()
        
        cursor = Database.connection.cursor()
        cursor.execute(query)
        cursor.close()
        Database.connection.commit()
        
    def connect():
        package_dir = os.path.abspath(os.path.dirname(__file__))
        database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
        Database.connection = sqlite3.connect(database_path)