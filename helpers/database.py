import os
import sqlite3

class Database():
    connection = None

    def select(columns: str, table: str, filters: str = "") -> list:
        """Performs a SELECT query in the phoebot database.

        Args:
            columns (str): The columns to select from
            table (str): The table to use
            filters (str, optional): Any filters to apply to the query. Defaults to "".

        Returns:
            list: The results
        """
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute(f"""SELECT {columns} FROM {table} {filters};""")

        results = list(cursor.fetchall())

        cursor.close()

        return results

    def insert(table_and_cols: str, values: str, ignore: bool = False) -> None:
        """Performs an INSERT query in the phoebot database.

        Args:
            table_and_cols (str): The tables and columns being used
            values (str): The values to insert
            ignore (bool, optional): Flag to ignore duplicates. Defaults to False.
        """
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()

        cursor.execute(f"""INSERT {"OR IGNORE" if ignore else ""} INTO {table_and_cols} VALUES({values});""")
        cursor.close()
        Database.connection.commit()

    def delete(table: str, filters: str = "") -> None:
        """Performs a DELETE query in the phoebot database.

        Args:
            table (str): The table to use
            filters (str, optional): The filters to use. Defaults to "".
        """
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute(f"DELETE FROM {table} {filters};")
        cursor.close()
        Database.connection.commit()

    def count(table: str, filters: str = "") -> int:
        """Performs a COUNT query in the phoebot database.

        Args:
            table (str): The table to use
            filters (str, optional): The filters to use. Defaults to "".

        Returns:
            int: The resulting count
        """
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table} {filters};")

        count = cursor.fetchone()[0]

        cursor.close()

        return count
    
    def query(query: str) -> list:
        """Performs a query in the phoebot database.

        Args:
            query (str): The query string

        Returns:
            list: The results
        """
        if Database.connection is None:
            Database.connect()

        cursor = Database.connection.cursor()
        cursor.execute(query)
        result = list(cursor.fetchall())
        cursor.close()
        Database.connection.commit()

        return result

    def connect() -> None:
        """Connect to the phoebot database"""
        package_dir = os.path.abspath(os.path.dirname(__file__))
        database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
        Database.connection = sqlite3.connect(database_path, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)