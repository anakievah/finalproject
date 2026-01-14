import json
import threading
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from .settings import SettingsLoader


class DatabaseManager:
    """Singleton класс для управления данными в JSON файлах."""
    
    _instance = None
    _lock = threading.Lock()  # Блокировка для потокобезопасности
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DatabaseManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self.settings = SettingsLoader()
        
        # Создаем пустые файлы если их нет
        self._init_data_files()
        
        self._initialized = True
    
    def _init_data_files(self):
        """Инициализировать файлы данных если их нет."""
        # Пользователи
        if not self.settings.USERS_FILE.exists():
            with open(self.settings.USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
        
        # Портфели
        if not self.settings.PORTFOLIOS_FILE.exists():
            with open(self.settings.PORTFOLIOS_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
        
        # Курсы валют
        if not self.settings.RATES_FILE.exists():
            initial_rates = {
                "pairs": {
                    "EUR_USD": {"rate": 1.0786, "updated_at": datetime.now().isoformat(), "source": "default"},
                    "BTC_USD": {"rate": 59337.21, "updated_at": datetime.now().isoformat(), "source": "default"},
                    "RUB_USD": {"rate": 0.01016, "updated_at": datetime.now().isoformat(), "source": "default"},
                    "ETH_USD": {"rate": 3720.00, "updated_at": datetime.now().isoformat(), "source": "default"}
                },
                "last_refresh": datetime.now().isoformat()
            }
            with open(self.settings.RATES_FILE, 'w', encoding='utf-8') as f:
                json.dump(initial_rates, f, indent=2)
        
        # История курсов
        if not self.settings.EXCHANGE_RATES_FILE.exists():
            with open(self.settings.EXCHANGE_RATES_FILE, 'w', encoding='utf-8') as f:
                json.dump([], f, indent=2)
    
    def _read_json(self, file_path: Path) -> Any:
        """Прочитать данные из JSON файла."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return []
    
    def _write_json(self, file_path: Path, data: Any):
        """Записать данные в JSON файл."""
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def get_all_users(self) -> List[Dict]:
        """Получить всех пользователей."""
        with self._lock:
            return self._read_json(self.settings.USERS_FILE)
    
    def get_user_by_username(self, username: str) -> Optional[Dict]:
        """Получить пользователя по имени."""
        users = self.get_all_users()
        for user in users:
            if user["username"] == username:
                return user
        return None
    
    def create_user(self, username: str, password: str) -> Dict:
        """Создать нового пользователя."""
        with self._lock:
            users = self.get_all_users()
            
            # Проверка на уникальность имени
            if any(user["username"] == username for user in users):
                raise ValueError(f"Пользователь с именем '{username}' уже существует")
            
            # Генерация ID
            user_id = max([user["user_id"] for user in users], default=0) + 1
            
            # Генерация соли и хеширование пароля
            import random
            import string
            from hashlib import sha256
            
            salt = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
            hashed_password = sha256((password + salt).encode()).hexdigest()
            
            # Создание пользователя
            new_user = {
                "user_id": user_id,
                "username": username,
                "hashed_password": hashed_password,
                "salt": salt,
                "registration_date": datetime.now().isoformat()
            }
            
            users.append(new_user)
            self._write_json(self.settings.USERS_FILE, users)
            
            # Создание пустого портфеля для пользователя
            self.create_portfolio(user_id)
            
            return new_user
    
    def create_portfolio(self, user_id: int):
        """Создать пустой портфель для пользователя."""
        with self._lock:
            portfolios = self._read_json(self.settings.PORTFOLIOS_FILE)
            
            # Проверка, не существует ли уже портфель
            if any(portfolio["user_id"] == user_id for portfolio in portfolios):
                return
            
            new_portfolio = {
                "user_id": user_id,
                "wallets": {}
            }
            
            portfolios.append(new_portfolio)
            self._write_json(self.settings.PORTFOLIOS_FILE, portfolios)
    
    def get_portfolio(self, user_id: int) -> Optional[Dict]:
        """Получить портфель пользователя."""
        portfolios = self._read_json(self.settings.PORTFOLIOS_FILE)
        for portfolio in portfolios:
            if portfolio["user_id"] == user_id:
                return portfolio
        return None
    
    def update_portfolio(self, user_id: int, wallets: Dict[str, Dict]):
        """Обновить портфель пользователя."""
        with self._lock:
            portfolios = self._read_json(self.settings.PORTFOLIOS_FILE)
            for portfolio in portfolios:
                if portfolio["user_id"] == user_id:
                    portfolio["wallets"] = wallets
                    self._write_json(self.settings.PORTFOLIOS_FILE, portfolios)
                    return
            # Если портфель не найден, создаем его
            new_portfolio = {
                "user_id": user_id,
                "wallets": wallets
            }
            portfolios.append(new_portfolio)
            self._write_json(self.settings.PORTFOLIOS_FILE, portfolios)
    
    def get_rates(self) -> Dict[str, Any]:
        """Получить курсы валют из кеша."""
        return self._read_json(self.settings.RATES_FILE)
    
    def update_rates(self, rates_data: Dict[str, Any]):
        """Обновить курсы валют в кеше."""
        with self._lock:
            self._write_json(self.settings.RATES_FILE, rates_data)
    
    def get_exchange_rates_history(self) -> List[Dict]:
        """Получить историю курсов обмена."""
        return self._read_json(self.settings.EXCHANGE_RATES_FILE)
    
    def add_exchange_rate_record(self, record: Dict):
        """Добавить запись в историю курсов обмена."""
        with self._lock:
            history = self.get_exchange_rates_history()
            history.append(record)
            self._write_json(self.settings.EXCHANGE_RATES_FILE, history)
    
    def are_rates_fresh(self) -> bool:
        """Проверить, достаточно ли свежие курсы."""
        rates = self.get_rates()
        if not rates or "last_refresh" not in rates:
            return False
        
        try:
            last_refresh = datetime.fromisoformat(rates["last_refresh"])
            ttl = timedelta(seconds=self.settings.RATES_TTL_SECONDS)
            return datetime.now() - last_refresh < ttl
        except ValueError:
            return False