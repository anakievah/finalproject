import os
from dataclasses import dataclass
from typing import Dict, Tuple


@dataclass
class ParserConfig:
    """Конфигурация для сервиса парсинга курсов."""
    
    # API ключ загружается из переменных окружения
    EXCHANGERATE_API_KEY: str = os.getenv("EXCHANGERATE_API_KEY", "")
    
    # Эндпоинты API
    COINGECKO_URL: str = "https://api.coingecko.com/api/v3/simple/price"
    EXCHANGERATE_API_URL: str = "https://v6.exchangerate-api.com/v6"
    
    # Базовая валюта для запросов
    BASE_CURRENCY: str = "USD"
    
    # Списки отслеживаемых валют
    FIAT_CURRENCIES: Tuple[str, ...] = ("EUR", "GBP", "RUB", "JPY", "CHF", "CAD", "AUD")
    CRYPTO_CURRENCIES: Tuple[str, ...] = ("BTC", "ETH", "SOL", "XRP", "ADA", "DOGE", "DOT")
    
    # Маппинг ID для CoinGecko
    CRYPTO_ID_MAP: Dict[str, str] = {
        "BTC": "bitcoin",
        "ETH": "ethereum",
        "SOL": "solana",
        "XRP": "ripple",
        "ADA": "cardano",
        "DOGE": "dogecoin",
        "DOT": "polkadot"
    }
    
    # Сетевые параметры
    REQUEST_TIMEOUT: int = 10  # секунд
    
    # Форматы даты/времени
    DATETIME_FORMAT: str = "%Y-%m-%dT%H:%M:%SZ"