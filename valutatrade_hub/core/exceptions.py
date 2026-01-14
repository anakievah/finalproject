class InsufficientFundsError(Exception):
    """Недостаточно средств на кошельке."""
    def __init__(self, currency_code, available, required):
        self.currency_code = currency_code
        self.available = available
        self.required = required
        super().__init__(f"Недостаточно средств: доступно {available:.4f} {currency_code}, требуется {required:.4f} {currency_code}")

class CurrencyNotFoundError(Exception):
    """Валюта не найдена."""
    def __init__(self, currency_code):
        self.currency_code = currency_code
        super().__init__(f"Неизвестная валюта '{currency_code}'")

class ApiRequestError(Exception):
    """Ошибка при обращении к внешнему API."""
    def __init__(self, reason):
        self.reason = reason
        super().__init__(f"Ошибка при обращении к внешнему API: {reason}")

class UserNotFoundError(Exception):
    """Пользователь не найден."""
    def __init__(self, username):
        self.username = username
        super().__init__(f"Пользователь '{username}' не найден")

class AuthenticationError(Exception):
    """Ошибка аутентификации."""
    def __init__(self, message="Неверный пароль"):
        super().__init__(message)

class WalletNotFoundError(Exception):
    """Кошелек не найден."""
    def __init__(self, currency_code):
        self.currency_code = currency_code
        super().__init__(f"У вас нет кошелька '{currency_code}'. Добавьте валюту: она создаётся автоматически при первой покупке.")

class DuplicateUsernameError(Exception):
    """Имя пользователя уже занято."""
    def __init__(self, username):
        self.username = username
        super().__init__(f"Имя пользователя '{username}' уже занято")

class InvalidPasswordError(Exception):
    """Некорректный пароль."""
    def __init__(self, message="Пароль должен быть не короче 4 символов"):
        super().__init__(message)

