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
    
    def execute(self, stmnt: str):
        self._cursor.execute(stmnt)

    def fetchall(self, stmnt: str):
        self._cursor.execute(stmnt)
        return self._cursor.fetchall()
    
    def end_session(self):
        self._cursor.close()
        self._conn.close()

    