import functools
import logging
import time

logger = logging.getLogger("actions")

def log_action(verbose=False):
    """Декоратор для логирования действий пользователя."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()
            action_name = func.__name__.upper()
            user_id = kwargs.get('user_id') or (args[0].user_id if hasattr(args[0], 'user_id') else None)
            username = kwargs.get('username') or (args[0].username if hasattr(args[0], 'username') else None)
            currency_code = kwargs.get('currency_code') or kwargs.get('from_code')
            amount = kwargs.get('amount')
            base_currency = kwargs.get('base_currency', 'USD')
            
            try:
                result = func(*args, **kwargs)
                execution_time = time.time() - start_time
                status = "OK"
                
                log_message = (
                    f"{action_name} user_id='{user_id}' username='{username}' "
                    f"currency='{currency_code}' amount={amount} base='{base_currency}' "
                    f"result={status} time={execution_time:.3f}s"
                )
                
                if verbose and hasattr(result, 'wallet') and action_name in ['BUY', 'SELL']:
                    wallet = result.wallet
                    balance_before = wallet.balance - (amount if action_name == 'BUY' else -amount)
                    log_message += f" balance_before={balance_before:.4f} balance_after={wallet.balance:.4f}"
                
                logger.info(log_message)
                return result
                
            except Exception as e:
                execution_time = time.time() - start_time
                error_type = type(e).__name__
                error_message = str(e)
                
                log_message = (
                    f"{action_name} user_id='{user_id}' username='{username}' "
                    f"currency='{currency_code}' amount={amount} base='{base_currency}' "
                    f"result=ERROR error_type='{error_type}' error_message='{error_message}' "
                    f"time={execution_time:.3f}s"
                )
                logger.error(log_message)
                raise
                
        return wrapper
    return decorator