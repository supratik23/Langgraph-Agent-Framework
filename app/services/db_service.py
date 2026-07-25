import mysql.connector
import os
import logging
from config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DBConnectionManager:
    def __init__(self):
        self.host = settings.DB_SERVER_NAME
        self.database = settings.DB_NAME
        self.user = settings.DB_USERNAME
        self.password = settings.DB_PASSKEY

        if not all([self.host, self.database, self.user, self.password]):
            logger.error("Database connection parameters are not fully set in environment variables.")
            raise ValueError("Missing database connection parameters.")
        self.connection = None

    def db_connection(self):
        db_host = self.host
        db_name = self.database
        db_user = self.user
        db_password = self.password

        logger.info(f"Connecting to MySQL database at {db_host} with user {db_user}")

        try:
            self.connection = mysql.connector.connect(
                host=db_host,
                database=db_name,
                user=db_user,
                password=db_password,
                ssl_ca=""
            )
            logger.info(f"Connected to MySQL. Server version: {self.connection.get_server_info()}")
            return self.connection
        except mysql.connector.Error as err:
            logger.error(f"MySQL connection error: {err}")
            return None

    def __enter__(self):
        logger.info("Entering context manager")
        return self 

    def __exit__(self, exc_type, exc_val, exc_tb):
        logger.info("Exiting context manager")
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")