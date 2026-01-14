import logging
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict

import requests

from ..core.exceptions import ApiRequestError
from .config import ParserConfig

logger = logging.getLogger(__name__)

class BaseApiClient(ABC):
    """Абстрактный базовый класс для API клиентов."""
    
    def __init__(self, config: ParserConfig):
        """
        Инициализация API клиента.
        
        Args:
            config: Конфигурация
        """
        self.config = config
    
    @abstractmethod
    def fetch_rates(self) -> Dict[str, Any]:
        """
        Получить курсы валют.
        
        Returns:
            Dict[str, Any]: Словарь с курсами
        """
        pass

class CoinGeckoClient(BaseApiClient):
    """Клиент для работы с CoinGecko API."""
    
    def fetch_rates(self) -> Dict[str, Any]:
        """
        Получить курсы криптовалют с CoinGecko.
        
        Returns:
            Dict[str, Any]: Словарь с курсами
        """
        try:
            # Формируем список ID для запроса
            crypto_ids = [self.config.CRYPTO_ID_MAP[code] for code in self.config.CRYPTO_CURRENCIES 
                         if code in self.config.CRYPTO_ID_MAP]
            
            if not crypto_ids:
                logger.warning("No valid cryptocurrency IDs found for CoinGecko request")
                return {}
            
            # Формируем параметры запроса
            params = {
                'ids': ','.join(crypto_ids),
                'vs_currencies': self.config.BASE_CURRENCY.lower()
            }
            
            # Отправляем запрос
            logger.info(f"Fetching cryptocurrency rates from CoinGecko for {len(crypto_ids)} currencies")
            response = requests.get(
                self.config.COINGECKO_URL,
                params=params,
                timeout=self.config.REQUEST_TIMEOUT
            )
            
            # Проверяем статус ответа
            response.raise_for_status()
            
            # Парсим ответ
            data = response.json()
            rates = {}
            timestamp = datetime.utcnow().strftime(self.config.DATETIME_FORMAT)
            
            # Преобразуем данные в единый формат
            for code in self.config.CRYPTO_CURRENCIES:
                if code in self.config.CRYPTO_ID_MAP:
                    crypto_id = self.config.CRYPTO_ID_MAP[code]
                    if crypto_id in data and self.config.BASE_CURRENCY.lower() in data[crypto_id]:
                        rate = data[crypto_id][self.config.BASE_CURRENCY.lower()]
                        pair = f"{code}_{self.config.BASE_CURRENCY}"
                        rates[pair] = {
                            "rate": rate,
                            "updated_at": timestamp,
                            "source": "CoinGecko"
                        }
            
            logger.info(f"Successfully fetched {len(rates)} cryptocurrency rates from CoinGecko")
            return rates
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error when fetching from CoinGecko: {str(e)}"
            logger.error(error_msg)
            raise ApiRequestError(error_msg) from e
        except ValueError as e:
            error_msg = f"Invalid response format from CoinGecko: {str(e)}"
            logger.error(error_msg)
            raise ApiRequestError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error when fetching from CoinGecko: {str(e)}"
            logger.error(error_msg)
            raise ApiRequestError(error_msg) from e

class ExchangeRateApiClient(BaseApiClient):
    """Клиент для работы с ExchangeRate-API."""
    
    def fetch_rates(self) -> Dict[str, Any]:
        """
        Получить курсы фиатных валют с ExchangeRate-API.
        
        Returns:
            Dict[str, Any]: Словарь с курсами
        """
        try:
            if not self.config.EXCHANGERATE_API_KEY:
                error_msg = "ExchangeRate-API key is not configured"
                logger.error(error_msg)
                raise ApiRequestError(error_msg)
            
            # Формируем URL запроса
            url = f"{self.config.EXCHANGERATE_API_URL}/{self.config.EXCHANGERATE_API_KEY}/latest/{self.config.BASE_CURRENCY}"
            
            # Отправляем запрос
            logger.info(f"Fetching fiat currency rates from ExchangeRate-API for base currency {self.config.BASE_CURRENCY}")
            response = requests.get(url, timeout=self.config.REQUEST_TIMEOUT)
            
            # Проверяем статус ответа
            response.raise_for_status()
            
            # Парсим ответ
            data = response.json()
            
            # Проверяем успешность ответа
            if data.get("result") != "success":
                error_msg = f"API returned error: {data.get('error-type', 'Unknown error')}"
                logger.error(error_msg)
                raise ApiRequestError(error_msg)
            
            # Извлекаем курсы
            rates = {}
            timestamp = datetime.strptime(data["time_last_update_utc"], "%a, %d %b %Y %H:%M:%S %z").strftime(self.config.DATETIME_FORMAT)
            
            # Преобразуем данные в единый формат
            for code in self.config.FIAT_CURRENCIES:
                if code in data["conversion_rates"]:
                    rate = data["conversion_rates"][code]
                    # Для фиатных валют мы получаем сколько базовой валюты в 1 единице данной валюты
                    # Поэтому нужно инвертировать курс для нашего формата
                    pair = f"{code}_{self.config.BASE_CURRENCY}"
                    rates[pair] = {
                        "rate": 1 / rate,
                        "updated_at": timestamp,
                        "source": "ExchangeRate-API"
                    }
            
            logger.info(f"Successfully fetched {len(rates)} fiat currency rates from ExchangeRate-API")
            return rates
            
        except requests.exceptions.RequestException as e:
            error_msg = f"Network error when fetching from ExchangeRate-API: {str(e)}"
            logger.error(error_msg)
            raise ApiRequestError(error_msg) from e
        except ValueError as e:
            error_msg = f"Invalid response format from ExchangeRate-API: {str(e)}"
            logger.error(error_msg)
            raise ApiRequestError(error_msg) from e
        except Exception as e:
            error_msg = f"Unexpected error when fetching from ExchangeRate-API: {str(e)}"
            logger.error(error_msg)
            raise ApiRequestError(error_msg) from e