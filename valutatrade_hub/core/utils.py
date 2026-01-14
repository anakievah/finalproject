import shlex
import sys
from typing import Any, Dict, List, Union

from ..infra.database import DatabaseManager
from .currencies import get_currency
from .exceptions import CurrencyNotFoundError
from .models import Portfolio, Wallet


def split_command(command: str) -> List[str]:
    """Разделить команду на аргументы с учетом кавычек."""
    try:
        if sys.platform.startswith('win'):
            # Windows-совместимая версия
            return command.split()
        else:
            # Unix-версия
            return shlex.split(command)
    except ValueError:
        # Если shlex не может обработать команду
        return command.split()

def parse_args(args_list: List[str]) -> Dict[str, Any]:
    """Разобрать аргументы командной строки в словарь."""
    args = {}
    i = 0
    while i < len(args_list):
        if args_list[i].startswith('--'):
            key = args_list[i][2:]
            if i + 1 < len(args_list) and not args_list[i + 1].startswith('--'):
                value = args_list[i + 1]
                # Пытаемся преобразовать в число, если возможно
                try:
                    if '.' in value:
                        value = float(value)
                    else:
                        value = int(value)
                except (ValueError, TypeError):
                    pass
                args[key] = value
                i += 2
            else:
                args[key] = True
                i += 1
        else:
            i += 1
    return args

def validate_currency_code(currency_code: str) -> str:
    """Проверить и нормализовать код валюты."""
    currency_code = currency_code.strip().upper()
    if not currency_code:
        raise ValueError("Код валюты не может быть пустым")
    
    # Проверяем, что валюта зарегистрирована
    try:
        get_currency(currency_code)
    except Exception as e:
        raise CurrencyNotFoundError(currency_code) from e
    
    return currency_code

def validate_positive_float(value: Union[str, float]) -> float:
    """Проверить и преобразовать значение в положительное число."""
    try:
        float_value = float(value)
    except (TypeError, ValueError):
        raise ValueError(f"'{value}' не является числом")
    
    if float_value <= 0:
        raise ValueError("Значение должно быть положительным")
    
    return float_value

def get_exchange_rates() -> Dict[str, float]:
    """Получить курсы обмена из базы данных."""
    db = DatabaseManager()
    rates_data = db.get_rates()
    rates = {}
    
    if "pairs" in rates_data:
        for pair, data in rates_data["pairs"].items():
            if "rate" in data:
                rates[pair] = data["rate"]
    
    return rates

def format_currency_amount(amount: float, currency_code: str) -> str:
    """Отформатировать сумму валюты для отображения."""
    if currency_code in ["BTC", "ETH", "SOL"]:
        return f"{amount:.4f}"
    elif currency_code == "USD":
        return f"{amount:,.2f}"
    else:
        return f"{amount:.2f}"

def load_user_portfolio(user_id: int) -> Portfolio:
    """Загрузить портфель пользователя из базы данных."""
    db = DatabaseManager()
    portfolio_data = db.get_portfolio(user_id)
    
    if not portfolio_data:
        portfolio = Portfolio(user_id)
        return portfolio
    
    portfolio = Portfolio(user_id)
    
    # Загружаем кошельки
    for currency_code, wallet_data in portfolio_data.get("wallets", {}).items():
        wallet = Wallet(currency_code)
        wallet.balance = wallet_data.get("balance", 0.0)
        portfolio._wallets[currency_code] = wallet
    
    return portfolio

def save_user_portfolio(user_id: int, portfolio: Portfolio):
    """Сохранить портфель пользователя в базу данных."""
    db = DatabaseManager()
    
    # Преобразуем портфель в формат для сохранения
    wallets_data = {}
    for currency_code, wallet in portfolio.wallets.items():
        wallets_data[currency_code] = {
            "balance": wallet.balance
        }
    
    db.update_portfolio(user_id, wallets_data)