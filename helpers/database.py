import os
import sqlite3

class Database():
    connection = None

    def select(query):
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute(query)

        results = list(cursor.fetchall())

        cursor.close()

        return results

    def insert(query):
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute(query)
        cursor.close()
        Database.connection.commit()

    def count(table, filters):
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute("""SELECT COUNT(*) FROM {} {};""".format(table, filters))

        count = cursor.fetchone()[0]

        cursor.close()

        return count

    def connect():
        package_dir = os.path.abspath(os.path.dirname(__file__))
        database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
        Database.connection = sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)