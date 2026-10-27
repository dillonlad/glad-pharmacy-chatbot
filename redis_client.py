from redis import Redis
from pydantic_settings import BaseSettings

class RedisSettings(BaseSettings):

    class Config:
        env_prefix = "redis_"
        case_sensetive = False
        
    host: str
    port: int
    user: str
    password: str

class RedisClient:
    def __init__(self):
        self._settings = RedisSettings()
        self._client = None

    def initialise(self):
        self._client = Redis(
            host=self._settings.host, 
            port=self._settings.port, 
            username=self._settings.user,
            password=self._settings.password,
        )

    def get(self, key: str) -> str :
        value = self._client.get(key)
        if value is not None and isinstance(value, bytes):
            value = value.decode()
        return value

    def set(self, key: str, value: str, ex: int = None):
        self._client.set(key, value, ex=ex)

