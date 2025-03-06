from pydantic_settings import BaseSettings
import mysql.connector

class DBConfig(BaseSettings):
    
    class Config:
        env_prefix = "db_"
        case_sensitive = False

    host: str
    user: str
    port: int
    password: str
    database: str

class DBHandler:

    def __init__(self):
        self._settings = DBConfig()
        self._conn = None
        self._cursor = None

    def start_session(self):
        self._conn = mysql.connector.connect(**self._settings.model_dump())
        self._cursor = self._conn.cursor(dictionary=True)
    
    def execute(self, stmnt: str, commit=False):
        self._cursor.execute(stmnt)
        if commit is True:
            self.commit()

    def commit(self):
        self._conn.commit()

    def fetchall(self, stmnt: str):
        self._cursor.execute(stmnt)
        return self._cursor.fetchall()
    
    def fetchone(self, stmnt: str):
        self._cursor.execute(stmnt)
        return self._cursor.fetchone()
    
    def end_session(self):
        self._cursor.close()
        self._conn.close()

    @classmethod
    def get_session(cls):
        """
        Using yield is more efficient for FastAPI and will ensure db session is closed after request is complete.
        """

        db_client = cls()
        db_client.start_session()
        try:
            yield db_client
        finally:
            db_client.end_session()

    