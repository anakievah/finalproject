import random
import string
from datetime import datetime
from hashlib import sha256
from typing import Dict, Union

from .currencies import get_currency
from .exceptions import InsufficientFundsError, WalletNotFoundError


class User:
    """Класс пользователя системы."""
    
    def __init__(self, user_id: int, username: str, hashed_password: str, salt: str, registration_date: datetime):
        """
        Инициализация пользователя.
        
        Args:
            user_id: Уникальный идентификатор пользователя
            username: Имя пользователя
            hashed_password: Хешированный пароль
            salt: Соль для хеширования
            registration_date: Дата регистрации
        """
        self._validate_username(username)
        
        self._user_id = user_id
        self._username = username
        self._hashed_password = hashed_password
        self._salt = salt
        self._registration_date = registration_date
    
    def _validate_username(self, username: str):
        """Валидация имени пользователя."""
        if not username or not username.strip():
            raise ValueError("Имя пользователя не может быть пустым")
    
    @property
    def user_id(self) -> int:
        """Геттер для ID пользователя."""
        return self._user_id
    
    @property
    def username(self) -> str:
        """Геттер для имени пользователя."""
        return self._username
    
    @property
    def registration_date(self) -> datetime:
        """Геттер для даты регистрации."""
        return self._registration_date
    
    def get_user_info(self) -> Dict[str, Union[int, str, datetime]]:
        """Получить информацию о пользователе."""
        return {
            "user_id": self._user_id,
            "username": self._username,
            "registration_date": self._registration_date
        }
    
    def verify_password(self, password: str) -> bool:
        """Проверить пароль пользователя."""
        hashed_input = sha256((password + self._salt).encode()).hexdigest()
        return hashed_input == self._hashed_password
    
    def change_password(self, new_password: str) -> None:
        """Изменить пароль пользователя."""
        if len(new_password) < 4:
            raise ValueError("Пароль должен быть не короче 4 символов")
        
        self._salt = ''.join(random.choices(string.ascii_letters + string.digits, k=16))
        self._hashed_password = sha256((new_password + self._salt).encode()).hexdigest()

class Wallet:
    """Класс кошелька для конкретной валюты."""
    
    def __init__(self, currency_code: str, balance: float = 0.0):
        """
        Инициализация кошелька.
        
        Args:
            currency_code: Код валюты
            balance: Начальный баланс
        """
        self._validate_currency(currency_code)
        
        self.currency_code = currency_code.upper()
        self._balance = 0.0
        self.deposit(balance)
    
    def _validate_currency(self, currency_code: str):
        """Валидация кода валюты."""
        if not currency_code or not currency_code.strip():
            raise ValueError("Код валюты не может быть пустым")
        try:
            get_currency(currency_code)
        except Exception as e:
            raise ValueError(f"Недопустимая валюта: {currency_code}") from e
    
    def _validate_amount(self, amount: float):
        """Валидация суммы операции."""
        if not isinstance(amount, (int, float)):
            raise TypeError("Сумма должна быть числом")
        if amount <= 0:
            raise ValueError("Сумма должна быть положительной")
    
    @property
    def balance(self) -> float:
        """Геттер для баланса."""
        return self._balance
    
    @balance.setter
    def balance(self, value: float):
        """Сеттер для баланса с проверкой."""
        if not isinstance(value, (int, float)):
            raise TypeError("Баланс должен быть числом")
        if value < 0:
            raise ValueError("Баланс не может быть отрицательным")
        self._balance = float(value)
    
    def deposit(self, amount: float) -> None:
        """Пополнить баланс кошелька."""
        self._validate_amount(amount)
        self._balance += amount
    
    def withdraw(self, amount: float) -> None:
        """Снять средства с кошелька."""
        self._validate_amount(amount)
        if self._balance < amount:
            raise InsufficientFundsError(self.currency_code, self._balance, amount)
        self._balance -= amount
    
    def get_balance_info(self) -> Dict[str, Union[str, float]]:
        """Получить информацию о балансе кошелька."""
        return {
            "currency_code": self.currency_code,
            "balance": self._balance
        }

class Portfolio:
    """Класс портфеля пользователя, управляющий всеми кошельками."""
    
    def __init__(self, user_id: int):
        """
        Инициализация портфеля.
        
        Args:
            user_id: ID пользователя
        """
        self._user_id = user_id
        self._wallets: Dict[str, Wallet] = {}
    
    @property
    def user_id(self) -> int:
        """Геттер для ID пользователя."""
        return self._user_id
    
    @property
    def wallets(self) -> Dict[str, Wallet]:
        """Геттер для кошельков (возвращает копию)."""
        return self._wallets.copy()
    
    def add_currency(self, currency_code: str) -> Wallet:
        """
        Добавить новую валюту в портфель.
        
        Args:
            currency_code: Код валюты
            
        Returns:
            Wallet: Созданный или существующий кошелек
        """
        currency_code = currency_code.upper()
        if currency_code in self._wallets:
            return self._wallets[currency_code]
        
        new_wallet = Wallet(currency_code)
        self._wallets[currency_code] = new_wallet
        return new_wallet
    
    def get_wallet(self, currency_code: str) -> Wallet:
        """
        Получить кошелек по коду валюты.
        
        Args:
            currency_code: Код валюты
            
        Returns:
            Wallet: Кошелек
            
        Raises:
            WalletNotFoundError: Если кошелек не найден
        """
        currency_code = currency_code.upper()
        if currency_code not in self._wallets:
            raise WalletNotFoundError(currency_code)
        return self._wallets[currency_code]
    
    def get_total_value(self, exchange_rates: Dict[str, float], base_currency: str = "USD") -> float:
        """
        Получить общую стоимость портфеля в базовой валюте.
        
        Args:
            exchange_rates: Словарь с курсами обмена
            base_currency: Базовая валюта для конвертации
            
        Returns:
            float: Общая стоимость в базовой валюте
        """
        base_currency = base_currency.upper()
        total_value = 0.0
        
        for wallet in self._wallets.values():
            if wallet.currency_code == base_currency:
                total_value += wallet.balance
            else:
                pair = f"{wallet.currency_code}_{base_currency}"
                if pair in exchange_rates:
                    total_value += wallet.balance * exchange_rates[pair]
                else:
                    # Попробуем обратную пару
                    reverse_pair = f"{base_currency}_{wallet.currency_code}"
                    if reverse_pair in exchange_rates:
                        total_value += wallet.balance / exchange_rates[reverse_pair]
        
        return total_value