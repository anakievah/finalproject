import os
from pathlib import Path

from dotenv import load_dotenv


class SettingsLoader:
    """Singleton класс для загрузки и управления настройками."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(SettingsLoader, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        # Загружаем переменные окружения
        load_dotenv()
        
        # Базовые пути
        self.BASE_DIR = Path(__file__).resolve().parent.parent.parent
        self.DATA_DIR = self.BASE_DIR / "data"
        self.LOGS_DIR = self.BASE_DIR / "logs"
        
        # Создаем директории если их нет
        self.DATA_DIR.mkdir(exist_ok=True)
        self.LOGS_DIR.mkdir(exist_ok=True)
        
        # Файлы данных
        self.USERS_FILE = self.DATA_DIR / "users.json"
        self.PORTFOLIOS_FILE = self.DATA_DIR / "portfolios.json"
        self.RATES_FILE = self.DATA_DIR / "rates.json"
        self.EXCHANGE_RATES_FILE = self.DATA_DIR / "exchange_rates.json"
        
        # Параметры приложения
        self.DEFAULT_BASE_CURRENCY = "USD"
        self.RATES_TTL_SECONDS = 300  # 5 минут
        
        # API ключи
        self.EXCHANGERATE_API_KEY = os.getenv("EXCHANGERATE_API_KEY", "")
        
        # Логирование
        self.LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
        self.LOG_MAX_BYTES = 10485760  # 10MB
        self.LOG_BACKUP_COUNT = 5
        
        self._initialized = True
    
    def get(self, key: str, default=None):
        """Получить значение настройки по ключу."""
        return getattr(self, key, default)
    
    def reload(self):
        """Перезагрузить настройки."""
        self.__init__()