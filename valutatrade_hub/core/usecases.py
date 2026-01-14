import logging
from datetime import datetime
from typing import Any, Dict, Optional

from ..decorators import log_action
from ..infra.database import DatabaseManager
from ..parser_service.api_clients import CoinGeckoClient, ExchangeRateApiClient
from ..parser_service.config import ParserConfig
from ..parser_service.storage import RatesStorage
from ..parser_service.updater import RatesUpdater
from .exceptions import (
    AuthenticationError,
    DuplicateUsernameError,
    InvalidPasswordError,
    UserNotFoundError,
    WalletNotFoundError,
)
from .models import User
from .utils import (
    get_exchange_rates,
    load_user_portfolio,
    save_user_portfolio,
    validate_currency_code,
    validate_positive_float,
)

logger = logging.getLogger(__name__)

class UserUsecases:
    """Бизнес-логика для работы с пользователями."""
    
    def __init__(self):
        self.db = DatabaseManager()
    
    def register_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Зарегистрировать нового пользователя.
        
        Args:
            username: Имя пользователя
            password: Пароль
            
        Returns:
            Dict[str, Any]: Информация о созданном пользователе
            
        Raises:
            DuplicateUsernameError: Если имя уже занято
            InvalidPasswordError: Если пароль некорректный
        """
        if len(password) < 4:
            raise InvalidPasswordError()
        
        try:
            user_data = self.db.create_user(username, password)
            logger.info(f"User '{username}' registered successfully with ID {user_data['user_id']}")
            return user_data
        except ValueError as e:
            if "уже существует" in str(e):
                raise DuplicateUsernameError(username) from e
            raise
    
    def authenticate_user(self, username: str, password: str) -> Dict[str, Any]:
        """
        Аутентифицировать пользователя.
        
        Args:
            username: Имя пользователя
            password: Пароль
            
        Returns:
            Dict[str, Any]: Информация о пользователе
            
        Raises:
            UserNotFoundError: Если пользователь не найден
            AuthenticationError: Если пароль неверный
        """
        user_data = self.db.get_user_by_username(username)
        if not user_data:
            raise UserNotFoundError(username)
        
        # Воссоздаем объект пользователя для проверки пароля
        user = User(
            user_id=user_data["user_id"],
            username=user_data["username"],
            hashed_password=user_data["hashed_password"],
            salt=user_data["salt"],
            registration_date=datetime.fromisoformat(user_data["registration_date"])
        )
        
        if not user.verify_password(password):
            raise AuthenticationError()
        
        logger.info(f"User '{username}' authenticated successfully")
        return user_data

class TradingUsecases:
    """Бизнес-логика для торговых операций."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.exchange_rates = get_exchange_rates()
    
    def _get_exchange_rate(self, from_currency: str, to_currency: str) -> float:
        """
        Получить курс обмена между двумя валютами.
        
        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта
            
        Returns:
            float: Курс обмена
            
        Raises:
            ValueError: Если курс не найден
        """
        # Прямой курс
        direct_pair = f"{from_currency}_{to_currency}"
        if direct_pair in self.exchange_rates:
            return self.exchange_rates[direct_pair]
        
        # Обратный курс
        reverse_pair = f"{to_currency}_{from_currency}"
        if reverse_pair in self.exchange_rates:
            return 1 / self.exchange_rates[reverse_pair]
        
        # Если базовая валюта USD или одна из валют - USD
        base_currency = "USD"
        if from_currency == base_currency:
            pair = f"{to_currency}_{base_currency}"
            if pair in self.exchange_rates:
                return 1 / self.exchange_rates[pair]
        elif to_currency == base_currency:
            pair = f"{from_currency}_{base_currency}"
            if pair in self.exchange_rates:
                return self.exchange_rates[pair]
        
        # Попытка через базовую валюту
        from_to_base = f"{from_currency}_{base_currency}"
        to_to_base = f"{to_currency}_{base_currency}"
        
        if from_to_base in self.exchange_rates and to_to_base in self.exchange_rates:
            from_rate = self.exchange_rates[from_to_base]
            to_rate = self.exchange_rates[to_to_base]
            return from_rate / to_rate
        
        raise ValueError(f"Не удалось найти курс обмена между {from_currency} и {to_currency}")
    
    @log_action(verbose=True)
    def buy_currency(self, user_id: int, currency_code: str, amount: float) -> Dict[str, Any]:
        """
        Купить валюту.
        
        Args:
            user_id: ID пользователя
            currency_code: Код покупаемой валюты
            amount: Количество покупаемой валюты
            
        Returns:
            Dict[str, Any]: Результат операции
            
        Raises:
            CurrencyNotFoundError: Если валюта не найдена
            ValueError: Если сумма некорректная
        """
        # Валидация входных данных
        currency_code = validate_currency_code(currency_code)
        amount = validate_positive_float(amount)
        
        # Загружаем портфель пользователя
        portfolio = load_user_portfolio(user_id)
        
        # Получаем или создаем кошелек для валюты
        if currency_code not in portfolio.wallets:
            portfolio.add_currency(currency_code)
        
        wallet = portfolio.get_wallet(currency_code)
        
        # Выполняем покупку
        wallet.deposit(amount)
        
        # Сохраняем обновленный портфель
        save_user_portfolio(user_id, portfolio)
        
        # Получаем курс для оценки стоимости
        try:
            rate = self._get_exchange_rate(currency_code, "USD")
            usd_value = amount * rate
        except ValueError:
            rate = None
            usd_value = None
        
        logger.info(f"User {user_id} bought {amount} {currency_code}")
        
        return {
            "success": True,
            "currency": currency_code,
            "amount": amount,
            "rate": rate,
            "usd_value": usd_value,
            "wallet": wallet
        }
    
    @log_action(verbose=True)
    def sell_currency(self, user_id: int, currency_code: str, amount: float) -> Dict[str, Any]:
        """
        Продать валюту.
        
        Args:
            user_id: ID пользователя
            currency_code: Код продаваемой валюты
            amount: Количество продаваемой валюты
            
        Returns:
            Dict[str, Any]: Результат операции
            
        Raises:
            CurrencyNotFoundError: Если валюта не найдена
            WalletNotFoundError: Если кошелек не найден
            InsufficientFundsError: Если недостаточно средств
            ValueError: Если сумма некорректная
        """
        # Валидация входных данных
        currency_code = validate_currency_code(currency_code)
        amount = validate_positive_float(amount)
        
        # Загружаем портфель пользователя
        portfolio = load_user_portfolio(user_id)
        
        # Проверяем наличие кошелька
        if currency_code not in portfolio.wallets:
            raise WalletNotFoundError(currency_code)
        
        wallet = portfolio.get_wallet(currency_code)
        
        # Выполняем продажу
        wallet.withdraw(amount)
        
        # Сохраняем обновленный портфель
        save_user_portfolio(user_id, portfolio)
        
        # Получаем курс для оценки выручки
        try:
            rate = self._get_exchange_rate(currency_code, "USD")
            usd_value = amount * rate
        except ValueError:
            rate = None
            usd_value = None
        
        logger.info(f"User {user_id} sold {amount} {currency_code}")
        
        return {
            "success": True,
            "currency": currency_code,
            "amount": amount,
            "rate": rate,
            "usd_value": usd_value,
            "wallet": wallet
        }
    
    def get_portfolio(self, user_id: int, base_currency: str = "USD") -> Dict[str, Any]:
        """
        Получить информацию о портфеле пользователя.
        
        Args:
            user_id: ID пользователя
            base_currency: Базовая валюта для оценки
            
        Returns:
            Dict[str, Any]: Информация о портфеле
        """
        # Загружаем портфель пользователя
        portfolio = load_user_portfolio(user_id)
        
        # Вычисляем общую стоимость в базовой валюте
        total_value = portfolio.get_total_value(self.exchange_rates, base_currency)
        
        # Формируем результат
        wallets_info = []
        for currency_code, wallet in portfolio.wallets.items():
            try:
                rate = self._get_exchange_rate(currency_code, base_currency)
                value_in_base = wallet.balance * rate
            except ValueError:
                rate = None
                value_in_base = None
            
            wallets_info.append({
                "currency": currency_code,
                "balance": wallet.balance,
                "rate": rate,
                "value_in_base": value_in_base
            })
        
        return {
            "user_id": user_id,
            "wallets": wallets_info,
            "total_value": total_value,
            "base_currency": base_currency
        }
    
    def get_exchange_rate(self, from_currency: str, to_currency: str) -> Dict[str, Any]:
        """
        Получить курс обмена между двумя валютами.
        
        Args:
            from_currency: Исходная валюта
            to_currency: Целевая валюта
            
        Returns:
            Dict[str, Any]: Информация о курсе
            
        Raises:
            CurrencyNotFoundError: Если валюта не найдена
            ValueError: Если курс не найден
        """
        # Валидация валют
        from_currency = validate_currency_code(from_currency)
        to_currency = validate_currency_code(to_currency)
        
        # Получаем курс
        rate = self._get_exchange_rate(from_currency, to_currency)
        
        # Получаем обратный курс
        try:
            reverse_rate = self._get_exchange_rate(to_currency, from_currency)
        except ValueError:
            reverse_rate = None
        
        # Получаем информацию о времени обновления из базы данных
        db = DatabaseManager()
        rates_data = db.get_rates()
        timestamp = rates_data.get("last_refresh", "Unknown")
        
        return {
            "from_currency": from_currency,
            "to_currency": to_currency,
            "rate": rate,
            "reverse_rate": reverse_rate,
            "updated_at": timestamp
        }

class RatesUsecases:
    """Бизнес-логика для работы с курсами валют."""
    
    def __init__(self):
        self.db = DatabaseManager()
        self.config = ParserConfig()
        self.storage = RatesStorage(
            rates_file=self.db.settings.RATES_FILE,
            history_file=self.db.settings.EXCHANGE_RATES_FILE
        )
    
    def update_rates(self, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Обновить курсы валют.
        
        Args:
            source: Источник для обновления (опционально)
            
        Returns:
            Dict[str, Any]: Результат обновления
        """
        logger.info(f"Starting rates update with source: {source}")
        
        # Инициализируем клиентов
        updater = RatesUpdater(self.config, self.storage)
        updater.add_client(CoinGeckoClient(self.config))
        updater.add_client(ExchangeRateApiClient(self.config))
        
        # Запускаем обновление
        result = updater.run_update(source)
        
        # Перезагружаем курсы в памяти
        global get_exchange_rates
        get_exchange_rates = DatabaseManager().get_rates
        
        logger.info(f"Rates update completed: {result}")
        return result
    
    def get_cached_rates_info(self) -> Dict[str, Any]:
        """
        Получить информацию о кешированных курсах.
        
        Returns:
            Dict[str, Any]: Информация о кеше
        """
        rates_data = self.db.get_rates()
        last_refresh = rates_data.get("last_refresh", "Unknown")
        pairs_count = len(rates_data.get("pairs", {}))
        
        return {
            "last_refresh": last_refresh,
            "pairs_count": pairs_count,
            "ttl_seconds": self.db.settings.RATES_TTL_SECONDS,
            "is_fresh": self.db.are_rates_fresh()
        }