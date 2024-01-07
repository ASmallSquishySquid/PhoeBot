import os
import sqlite3

class Database():
    connection = None

    @classmethod
    def select(cls, columns: str, table: str, filters: str = "") -> list:
        """Performs a SELECT query in the phoebot database.

        Args:
            columns (str): The columns to select from
            table (str): The table to use
            filters (str, optional): Any filters to apply to the query. Defaults to "".

        Returns:
            list: The results
        """
        if cls.connection is None:
            cls.connect()

        cursor = cls.connection.cursor()
        cursor.execute(f"""SELECT {columns} FROM {table} {filters};""")

        results = list(cursor.fetchall())

        cursor.close()

        return results

    @classmethod
    def insert(cls, table_and_cols: str, values: str, ignore: bool = False) -> None:
        """Performs an INSERT query in the phoebot database.

        Args:
            table_and_cols (str): The tables and columns being used
            values (str): The values to insert
            ignore (bool, optional): Flag to ignore duplicates. Defaults to False.
        """
        if cls.connection is None:
            cls.connect()

        cursor = cls.connection.cursor()

        cursor.execute(
            f"""INSERT {"OR IGNORE" if ignore else ""} INTO {table_and_cols} VALUES({values});""")
        cursor.close()
        cls.connection.commit()

    @classmethod
    def delete(cls, table: str, filters: str = "") -> None:
        """Performs a DELETE query in the phoebot database.

        Args:
            table (str): The table to use
            filters (str, optional): The filters to use. Defaults to "".
        """
        if cls.connection is None:
            cls.connect()

        cursor = Database.connection.cursor()
        cursor.execute(f"DELETE FROM {table} {filters};")
        cursor.close()
        cls.connection.commit()

    @classmethod
    def count(cls, table: str, filters: str = "") -> int:
        """Performs a COUNT query in the phoebot database.

        Args:
            table (str): The table to use
            filters (str, optional): The filters to use. Defaults to "".

        Returns:
            int: The resulting count
        """
        if cls.connection is None:
            cls.connect()

        cursor = cls.connection.cursor()
        cursor.execute(f"SELECT COUNT(*) FROM {table} {filters};")

        count = cursor.fetchone()[0]

        cursor.close()

        return count

    @classmethod
    def query(cls, query: str) -> list:
        """Performs a query in the phoebot database.

        Args:
            query (str): The query string

        Returns:
            list: The results
        """
        if cls.connection is None:
            cls.connect()

        cursor = cls.connection.cursor()
        cursor.execute(query)
        result = list(cursor.fetchall())
        cursor.close()
        cls.connection.commit()

        return result

    @classmethod
    def connect(cls) -> None:
        """Connect to the phoebot database"""
        package_dir = os.path.abspath(os.path.dirname(__file__))
        database_path = os.path.join(package_dir, "..", "..", "phoebot.db")
        cls.connection = sqlite3.connect(
            database=database_path,
            detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
