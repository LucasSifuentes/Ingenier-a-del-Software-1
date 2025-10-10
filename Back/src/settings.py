from enum import Enum
from pydantic import IPvAnyAddress, PositiveInt
from pydantic_settings import BaseSettings
from pathlib import Path
import os

class LoggingEnum(str, Enum):
    debug = "DEBUG"
    info = "INFO"
    warning = "WARNING"
    error = "ERROR"
    critical = "CRITICAL"

class Settings(BaseSettings):
    # Diferente BD para testing
    BASE_DIR: Path = Path(__file__).resolve().parent.parent
    
    if os.getenv("TESTING"):
        DB_FILENAME: str = "sqlite:///" + str(BASE_DIR / "test.db")
    else:
        DB_FILENAME: str = "sqlite:///" + str(BASE_DIR / "agatha_christie.db")
    
    # server
    HOST: IPvAnyAddress = "0.0.0.0"
    PORT: PositiveInt = 8000
    DEBUG_MODE: bool = True 
    ROOT_PATH: str = ""
    LOGLEVEL: LoggingEnum = "DEBUG"
    
    class Config:
        env_file = ".env"

settings = Settings()