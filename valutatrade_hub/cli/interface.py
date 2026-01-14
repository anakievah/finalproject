import logging
from datetime import datetime
from typing import Dict

from prettytable import PrettyTable

from ..core.exceptions import (
    ApiRequestError,
    AuthenticationError,
    CurrencyNotFoundError,
    DuplicateUsernameError,
    InsufficientFundsError,
    InvalidPasswordError,
    UserNotFoundError,
    WalletNotFoundError,
)
from ..core.usecases import RatesUsecases, TradingUsecases, UserUsecases
from ..core.utils import format_currency_amount, parse_args, split_command
from ..infra.database import DatabaseManager

logger = logging.getLogger(__name__)

class CLIInterface:
    """Класс для интерфейса командной строки."""
    
    def __init__(self):
        self.user_usecases = UserUsecases()
        self.trading_usecases = TradingUsecases()
        self.rates_usecases = RatesUsecases()
        self.current_user = None
        self.db = DatabaseManager()
    
    def run(self):
        """Запустить интерфейс командной строки."""
        logger.info("Starting CLI interface")
        
        print("Welcome to ValutaTrade Hub!")
        print("Type 'help' to see available commands or 'exit' to quit.")
        
        while True:
            try:
                command_line = input(f"\n{self._get_prompt()}> ").strip()
                if not command_line:
                    continue
                
                if command_line.lower() == "exit":
                    print("Goodbye!")
                    break
                
                self._process_command(command_line)
                
            except KeyboardInterrupt:
                print("\nOperation cancelled by user.")
            except Exception as e:
                logger.exception(f"Unexpected error: {str(e)}")
                print(f"Error: {str(e)}")
                print("Please try again or type 'help' for assistance.")
    
    def _get_prompt(self) -> str:
        """Получить приглашение для ввода команды."""
        if self.current_user:
            return f"{self.current_user['username']}@valutatrade"
        return "guest@valutatrade"
    
    def _process_command(self, command_line: str):
        """Обработать команду пользователя."""
        args = split_command(command_line)
        if not args:
            return
        
        command = args[0].lower()
        command_args = parse_args(args[1:])
        
        # Словарь команд
        commands = {
            "help": self._cmd_help,
            "register": self._cmd_register,
            "login": self._cmd_login,
            "logout": self._cmd_logout,
            "show-portfolio": self._cmd_show_portfolio,
            "buy": self._cmd_buy,
            "sell": self._cmd_sell,
            "get-rate": self._cmd_get_rate,
            "update-rates": self._cmd_update_rates,
            "show-rates": self._cmd_show_rates
        }
        
        if command in commands:
            commands[command](command_args)
        else:
            print(f"Unknown command: {command}")
            print("Type 'help' to see available commands.")
    
    def _cmd_help(self, args: Dict[str, str]):
        """Показать справку по командам."""
        table = PrettyTable()
        table.field_names = ["Command", "Description", "Arguments"]
        table.align = "l"
        
        help_data = [
            ("help", "Show this help message", ""),
            ("register", "Register a new user", "--username <name> --password <pwd>"),
            ("login", "Log in to your account", "--username <name> --password <pwd>"),
            ("logout", "Log out from your account", ""),
            ("show-portfolio", "Show your portfolio", "[--base <currency>]"),
            ("buy", "Buy currency", "--currency <code> --amount <number>"),
            ("sell", "Sell currency", "--currency <code> --amount <number>"),
            ("get-rate", "Get exchange rate", "--from <code> --to <code>"),
            ("update-rates", "Update exchange rates", "[--source <coingecko|exchangerate>]"),
            ("show-rates", "Show cached rates", "[--currency <code>] [--top <number>] [--base <code>]"),
            ("exit", "Exit the application", "")
        ]
        
        for cmd, desc, args_desc in help_data:
            table.add_row([cmd, desc, args_desc])
        
        print(table)
    
    def _cmd_register(self, args: Dict[str, str]):
        """Зарегистрировать нового пользователя."""
        username = args.get("username")
        password = args.get("password")
        
        if not username:
            print("Error: --username is required")
            return
        
        if not password:
            print("Error: --password is required")
            return
        
        try:
            user_data = self.user_usecases.register_user(username, password)
            print(f"User '{username}' registered successfully (ID: {user_data['user_id']})")
            print("Please log in with your credentials.")
        except DuplicateUsernameError:
            print(f"Error: Username '{username}' is already taken. Please choose another one.")
        except InvalidPasswordError:
            print("Error: Password must be at least 4 characters long.")
        except Exception as e:
            print(f"Error: Failed to register user: {str(e)}")
    
    def _cmd_login(self, args: Dict[str, str]):
        """Войти в систему."""
        username = args.get("username")
        password = args.get("password")
        
        if not username:
            print("Error: --username is required")
            return
        
        if not password:
            print("Error: --password is required")
            return
        
        try:
            user_data = self.user_usecases.authenticate_user(username, password)
            self.current_user = user_data
            print(f"Successfully logged in as '{username}'")
        except UserNotFoundError:
            print(f"Error: User '{username}' not found")
        except AuthenticationError:
            print("Error: Incorrect password")
        except Exception as e:
            print(f"Error: Failed to log in: {str(e)}")
    
    def _cmd_logout(self, args: Dict[str, str]):
        """Выйти из системы."""
        if self.current_user:
            username = self.current_user["username"]
            self.current_user = None
            print(f"Successfully logged out from '{username}'")
        else:
            print("You are not logged in.")
    
    def _cmd_show_portfolio(self, args: Dict[str, str]):
        """Показать портфель пользователя."""
        if not self.current_user:
            print("Error: You must be logged in to view your portfolio")
            print("Please log in first using the 'login' command.")
            return
        
        base_currency = args.get("base", "USD").upper()
        
        try:
            # Валидация базовой валюты
            from ..core.utils import validate_currency_code
            validate_currency_code(base_currency)
            
            portfolio_data = self.trading_usecases.get_portfolio(self.current_user["user_id"], base_currency)
            
            print(f"\nPortfolio for '{self.current_user['username']}' (base currency: {base_currency})")
            print("-" * 60)
            
            if not portfolio_data["wallets"]:
                print("Your portfolio is empty. Use 'buy' command to add currencies.")
                return
            
            table = PrettyTable()
            table.field_names = ["Currency", "Balance", f"Value in {base_currency}"]
            table.align = "r"
            table.align["Currency"] = "l"
            
            total_value = 0.0
            
            for wallet in portfolio_data["wallets"]:
                currency = wallet["currency"]
                balance = wallet["balance"]
                value_in_base = wallet["value_in_base"]
                
                balance_str = format_currency_amount(balance, currency)
                value_str = format_currency_amount(value_in_base, base_currency) if value_in_base is not None else "N/A"
                
                table.add_row([currency, balance_str, value_str])
                
                if value_in_base is not None:
                    total_value += value_in_base
            
            print(table)
            print("-" * 60)
            print(f"TOTAL VALUE: {format_currency_amount(total_value, base_currency)} {base_currency}")
            
        except CurrencyNotFoundError as e:
            print(f"Error: {str(e)}")
            print("Supported currencies: USD, EUR, GBP, RUB, BTC, ETH, SOL")
        except Exception as e:
            print(f"Error: Failed to load portfolio: {str(e)}")
    
    def _cmd_buy(self, args: Dict[str, str]):
        """Купить валюту."""
        if not self.current_user:
            print("Error: You must be logged in to buy currency")
            print("Please log in first using the 'login' command.")
            return
        
        currency_code = args.get("currency")
        amount_str = args.get("amount")
        
        if not currency_code:
            print("Error: --currency is required")
            return
        
        if not amount_str:
            print("Error: --amount is required")
            return
        
        try:
            amount = float(amount_str)
        except ValueError:
            print(f"Error: '{amount_str}' is not a valid number")
            return
        
        try:
            result = self.trading_usecases.buy_currency(
                self.current_user["user_id"],
                currency_code,
                amount
            )
            
            currency = result["currency"]
            amount = result["amount"]
            rate = result["rate"]
            usd_value = result["usd_value"]
            
            print("\n✅ Purchase successful!")
            print(f"  Currency: {currency}")
            print(f"  Amount: {format_currency_amount(amount, currency)}")
            
            if rate and usd_value:
                print(f"  Rate: {rate:.4f} USD/{currency}")
                print(f"  Estimated value: {format_currency_amount(usd_value, 'USD')} USD")
            
            wallet = result["wallet"]
            print(f"\nUpdated wallet balance for {currency}: {format_currency_amount(wallet.balance, currency)}")
            
        except CurrencyNotFoundError as e:
            print(f"Error: {str(e)}")
            print("Supported currencies: USD, EUR, GBP, RUB, BTC, ETH, SOL")
        except ValueError as e:
            if "positive" in str(e).lower():
                print("Error: Amount must be a positive number")
            else:
                print(f"Error: {str(e)}")
        except Exception as e:
            print(f"Error: Failed to buy currency: {str(e)}")
    
    def _cmd_sell(self, args: Dict[str, str]):
        """Продать валюту."""
        if not self.current_user:
            print("Error: You must be logged in to sell currency")
            print("Please log in first using the 'login' command.")
            return
        
        currency_code = args.get("currency")
        amount_str = args.get("amount")
        
        if not currency_code:
            print("Error: --currency is required")
            return
        
        if not amount_str:
            print("Error: --amount is required")
            return
        
        try:
            amount = float(amount_str)
        except ValueError:
            print(f"Error: '{amount_str}' is not a valid number")
            return
        
        try:
            result = self.trading_usecases.sell_currency(
                self.current_user["user_id"],
                currency_code,
                amount
            )
            
            currency = result["currency"]
            amount = result["amount"]
            rate = result["rate"]
            usd_value = result["usd_value"]
            
            print("\n✅ Sale successful!")
            print(f"  Currency: {currency}")
            print(f"  Amount: {format_currency_amount(amount, currency)}")
            
            if rate and usd_value:
                print(f"  Rate: {rate:.4f} USD/{currency}")
                print(f"  Estimated revenue: {format_currency_amount(usd_value, 'USD')} USD")
            
            wallet = result["wallet"]
            print(f"\nUpdated wallet balance for {currency}: {format_currency_amount(wallet.balance, currency)}")
            
        except CurrencyNotFoundError as e:
            print(f"Error: {str(e)}")
            print("Supported currencies: USD, EUR, GBP, RUB, BTC, ETH, SOL")
        except WalletNotFoundError as e:
            print(f"Error: {str(e)}")
            print("You can buy this currency first to create a wallet.")
        except InsufficientFundsError as e:
            print(f"Error: {str(e)}")
            print("Check your wallet balance with 'show-portfolio' command.")
        except ValueError as e:
            if "positive" in str(e).lower():
                print("Error: Amount must be a positive number")
            else:
                print(f"Error: {str(e)}")
        except Exception as e:
            print(f"Error: Failed to sell currency: {str(e)}")
    
    def _cmd_get_rate(self, args: Dict[str, str]):
        """Получить курс обмена."""
        from_currency = args.get("from")
        to_currency = args.get("to")
        
        if not from_currency:
            print("Error: --from currency is required")
            return
        
        if not to_currency:
            print("Error: --to currency is required")
            return
        
        try:
            rate_data = self.trading_usecases.get_exchange_rate(from_currency, to_currency)
            
            from_curr = rate_data["from_currency"]
            to_curr = rate_data["to_currency"]
            rate = rate_data["rate"]
            reverse_rate = rate_data["reverse_rate"]
            updated_at = rate_data["updated_at"]
            
            print(f"\nExchange Rate: {from_curr} → {to_curr}")
            print(f"Rate: {rate:.6f} {to_curr} per {from_curr}")
            print(f"Updated at: {updated_at}")
            
            if reverse_rate:
                print(f"\nReverse Rate ({to_curr} → {from_curr}): {reverse_rate:.6f}")
            
            # Проверяем, не устарели ли данные
            if not self.db.are_rates_fresh():
                print("\n⚠️  Warning: Exchange rates may be outdated.")
                print("You can update them with 'update-rates' command.")
            
        except CurrencyNotFoundError as e:
            print(f"Error: {str(e)}")
            print("Supported currencies: USD, EUR, GBP, RUB, BTC, ETH, SOL")
        except ValueError as e:
            if "find exchange rate" in str(e).lower():
                print(f"Error: Could not find exchange rate between {from_currency} and {to_currency}")
                print("Try updating the rates with 'update-rates' command.")
            else:
                print(f"Error: {str(e)}")
        except Exception as e:
            print(f"Error: Failed to get exchange rate: {str(e)}")
    
    def _cmd_update_rates(self, args: Dict[str, str]):
        """Обновить курсы валют."""
        source = args.get("source")
        
        print("🔄 Updating exchange rates...")
        
        try:
            result = self.rates_usecases.update_rates(source)
            
            if result["success"]:
                print("✅ Exchange rates updated successfully!")
                print(f"Updated {len(result['updated_pairs'])} currency pairs")
                print(f"Last refresh: {result['timestamp']}")
            else:
                print("⚠️  Exchange rates update completed with errors:")
                for error in result["errors"]:
                    print(f"  - {error}")
                print("Check logs for details.")
            
            # Показываем информацию о кеше
            cache_info = self.rates_usecases.get_cached_rates_info()
            print("\nCache status:")
            print(f"  Last refresh: {cache_info['last_refresh']}")
            print(f"  Currency pairs: {cache_info['pairs_count']}")
            
        except ApiRequestError as e:
            print(f"❌ Error updating rates: {str(e)}")
            print("Please check your network connection and API configuration.")
            print("You may need to set the EXCHANGERATE_API_KEY environment variable.")
        except Exception as e:
            print(f"❌ Unexpected error updating rates: {str(e)}")
            print("Check logs for details.")
    
    def _cmd_show_rates(self, args: Dict[str, str]):
        """Показать кешированные курсы валют."""
        currency_filter = args.get("currency")
        top_n = args.get("top")
        base_currency = args.get("base", "USD").upper()
        
        try:
            # Валидация базовой валюты
            from ..core.utils import validate_currency_code
            validate_currency_code(base_currency)
            
            # Получаем курсы из базы данных
            rates_data = self.db.get_rates()
            pairs = rates_data.get("pairs", {})
            last_refresh = rates_data.get("last_refresh", "Unknown")
            
            print("\nExchange Rates (cached)")
            print(f"Last refresh: {last_refresh}")
            print(f"Base currency: {base_currency}")
            print("-" * 60)
            
            if not pairs:
                print("No exchange rates available in cache.")
                print("Update rates with 'update-rates' command.")
                return
            
            # Фильтрация по валюте
            filtered_pairs = {}
            if currency_filter:
                currency_filter = currency_filter.upper()
                for pair, data in pairs.items():
                    from_curr, to_curr = pair.split('_')
                    if from_curr == currency_filter or to_curr == currency_filter:
                        filtered_pairs[pair] = data
            else:
                filtered_pairs = pairs
            
            if not filtered_pairs:
                if currency_filter:
                    print(f"No rates found for currency '{currency_filter}'")
                else:
                    print("No exchange rates available")
                return
            
            # Сортировка для top N
            if top_n and isinstance(top_n, int) and top_n > 0:
                # Фильтруем пары с базовой валютой
                base_pairs = {
                    pair: data for pair, data in filtered_pairs.items()
                    if pair.endswith(f"_{base_currency}")
                }
                
                # Сортируем по курсу в обратном порядке (самые дорогие вверху)
                sorted_pairs = sorted(
                    base_pairs.items(),
                    key=lambda x: x[1]["rate"],
                    reverse=True
                )[:top_n]
                
                filtered_pairs = dict(sorted_pairs)
            
            # Выводим результаты
            table = PrettyTable()
            table.field_names = ["Pair", "Rate", "Source", "Updated"]
            table.align = "r"
            table.align["Pair"] = "l"
            table.align["Source"] = "l"
            
            for pair, data in filtered_pairs.items():
                rate = data["rate"]
                source = data["source"]
                updated_at = data["updated_at"]
                
                # Форматируем дату для отображения
                try:
                    dt = datetime.fromisoformat(updated_at.replace("Z", "+00:00"))
                    updated_str = dt.strftime("%Y-%m-%d %H:%M:%S")
                except (ValueError, TypeError):
                    updated_str = updated_at
                
                table.add_row([pair, f"{rate:.6f}", source, updated_str])
            
            print(table)
            
            # Проверяем, не устарели ли данные
            if not self.db.are_rates_fresh():
                print("\n⚠️  Warning: Exchange rates may be outdated.")
                print("You can update them with 'update-rates' command.")
            
        except CurrencyNotFoundError as e:
            print(f"Error: {str(e)}")
            print("Supported base currencies: USD, EUR, GBP, RUB")
        except Exception as e:
            print(f"Error: Failed to show rates: {str(e)}")