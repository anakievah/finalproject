from abc import ABC, abstractmethod
from typing import List

from .exceptions import CurrencyNotFoundError


class Currency(ABC):
    """Абстрактный базовый класс для валют."""
    
    def __init__(self, name: str, code: str):
        """
        Инициализация валюты.
        
        Args:
            name: Человекочитаемое имя валюты
            code: ISO-код или тикер валюты
        """
        self._validate_code(code)
        self._validate_name(name)
        
        self.name = name
        self.code = code.upper()
    
    def _validate_code(self, code: str):
        """Валидация кода валюты."""
        if not code or not code.strip():
            raise ValueError("Код валюты не может быть пустым")
        if len(code) < 2 or len(code) > 5:
            raise ValueError("Код валюты должен содержать от 2 до 5 символов")
        if not code.replace('-', '').isalnum():
            raise ValueError("Код валюты может содержать только буквы, цифры и дефис")
    
    def _validate_name(self, name: str):
        """Валидация имени валюты."""
        if not name or not name.strip():
            raise ValueError("Имя валюты не может быть пустым")
    
    @abstractmethod
    def get_display_info(self) -> str:
        """Получить информацию для отображения о валюте."""
        pass

class FiatCurrency(Currency):
    """Класс для фиатных валют."""
    
    def __init__(self, name: str, code: str, issuing_country: str):
        """
        Инициализация фиатной валюты.
        
        Args:
            name: Человекочитаемое имя валюты
            code: ISO-код валюты
            issuing_country: Страна/регион эмиссии
        """
        super().__init__(name, code)
        self.issuing_country = issuing_country
    
    def get_display_info(self) -> str:
        """Получить информацию для отображения о фиатной валюте."""
        return f"[FIAT] {self.code} — {self.name} (Issuing: {self.issuing_country})"

class CryptoCurrency(Currency):
    """Класс для криптовалют."""
    
    def __init__(self, name: str, code: str, algorithm: str, market_cap: float):
        """
        Инициализация криптовалюты.
        
        Args:
            name: Человекочитаемое имя валюты
            code: Тикер валюты
            algorithm: Алгоритм майнинга
            market_cap: Рыночная капитализация в USD
        """
        super().__init__(name, code)
        self.algorithm = algorithm
        self.market_cap = market_cap
    
    def get_display_info(self) -> str:
        """Получить информацию для отображения о криптовалюте."""
        market_cap_str = f"{self.market_cap:.2e}" if self.market_cap >= 1e9 else f"{self.market_cap:,.2f}"
        return f"[CRYPTO] {self.code} — {self.name} (Algo: {self.algorithm}, MCAP: {market_cap_str})"

# Фабрика валют
_CURRENCY_REGISTRY = {}

def register_currency(currency: Currency):
    """Зарегистрировать валюту в реестре."""
    _CURRENCY_REGISTRY[currency.code.upper()] = currency

def get_currency(code: str) -> Currency:
    """
    Получить валюту по коду из реестра.
    
    Args:
        code: Код валюты
        
    Returns:
        Currency: Объект валюты
        
    Raises:
        CurrencyNotFoundError: Если валюта не найдена
    """
    code_upper = code.upper()
    if code_upper not in _CURRENCY_REGISTRY:
        raise CurrencyNotFoundError(code_upper)
    return _CURRENCY_REGISTRY[code_upper]

def get_all_currencies() -> List[Currency]:
    """Получить список всех зарегистрированных валют."""
    return list(_CURRENCY_REGISTRY.values())

# Предопределенные валюты
register_currency(FiatCurrency("US Dollar", "USD", "United States"))
register_currency(FiatCurrency("Euro", "EUR", "Eurozone"))
register_currency(FiatCurrency("British Pound", "GBP", "United Kingdom"))
register_currency(FiatCurrency("Russian Ruble", "RUB", "Russia"))
register_currency(CryptoCurrency("Bitcoin", "BTC", "SHA-256", 1.12e12))
register_currency(CryptoCurrency("Ethereum", "ETH", "Ethash", 2.85e11))
register_currency(CryptoCurrency("Solana", "SOL", "Proof of History", 7.85e10))