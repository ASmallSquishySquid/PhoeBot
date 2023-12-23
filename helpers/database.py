import os
import sqlite3

class Database():
    connection = None

    def select(columns: str, table: str, filters: str = "") -> list:
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute("""SELECT {} FROM {} {};""".format(columns, table, filters))

        results = list(cursor.fetchall())

        cursor.close()

        return results

    def insert(tableAndCols: str, values: str, ignore: bool = False) -> None:
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()

        cursor.execute("""INSERT {} INTO {} VALUES({});""".format("OR IGNORE" if ignore else "", tableAndCols, values))
        cursor.close()
        Database.connection.commit()

    def delete(table: str, filters: str = "") -> None:
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute("""DELETE FROM {} {};""".format(table, filters))
        cursor.close()
        Database.connection.commit()

    def count(table: str, filters: str = "") -> int:
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute("""SELECT COUNT(*) FROM {} {};""".format(table, filters))

        count = cursor.fetchone()[0]

        cursor.close()

        return count
    
    def query(query: str) -> list:
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute(query)
        result = list(cursor.fetchall())
        cursor.close()
        Database.connection.commit()

        return result

    def connect() -> None:
        package_dir = os.path.abspath(os.path.dirname(__file__))
        database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
        Database.connection = sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)