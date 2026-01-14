import logging
import os
import sys

from valutatrade_hub.cli.interface import CLIInterface
from valutatrade_hub.logging_config import setup_logging


def main():
    """Точка входа в приложение."""
    # Настраиваем логирование
    _, action_logger = setup_logging(log_level=logging.INFO)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting ValutaTrade Hub application")
    
    # Проверяем наличие API ключа
    api_key = os.getenv("EXCHANGERATE_API_KEY")
    if not api_key:
        logger.warning("EXCHANGERATE_API_KEY environment variable is not set. Some features may not work properly.")
        print("⚠️  Warning: EXCHANGERATE_API_KEY environment variable is not set.")
        print("   Some features that require external API calls may not work properly.")
        print("   Set it using: set EXCHANGERATE_API_KEY=your_key (Windows) or export EXCHANGERATE_API_KEY=your_key (Linux/Mac)")
        print()
    
    try:
        # Запускаем CLI интерфейс
        cli = CLIInterface()
        cli.run()
        
    except KeyboardInterrupt:
        logger.info("Application terminated by user")
        print("\nApplication terminated by user.")
    except Exception as e:
        logger.exception(f"Critical error in application: {str(e)}")
        print(f"Critical error: {str(e)}")
        print("Please check logs for details.")
        sys.exit(1)
    
    logger.info("Application finished successfully")

if __name__ == "__main__":
    main()