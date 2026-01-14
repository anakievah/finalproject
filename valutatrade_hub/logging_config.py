import io
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


def setup_logging(log_level=logging.INFO, log_dir="logs", max_bytes=10485760, backup_count=5):
    """Configure logging for the application."""
    # Windows-specific encoding fix
    if sys.platform.startswith('win'):
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')
    
    # Создаем директорию для логов если её нет
    log_path = Path(log_dir)
    log_path.mkdir(exist_ok=True)
    
    # Основной файл логов
    log_file = log_path / "application.log"
    
    # Формат логов
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    # Обработчик для файла с ротацией
    file_handler = RotatingFileHandler(
        log_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    file_handler.setFormatter(formatter)
    
    # Обработчик для консоли
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    
    # Настраиваем корневой логгер
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Отдельный логгер для действий пользователя
    action_logger = logging.getLogger("actions")
    action_logger.propagate = False
    action_logger.setLevel(log_level)
    
    action_file = log_path / "actions.log"
    action_handler = RotatingFileHandler(
        action_file, maxBytes=max_bytes, backupCount=backup_count, encoding='utf-8'
    )
    action_handler.setFormatter(logging.Formatter(
        '%(asctime)s %(message)s'
    ))
    action_logger.addHandler(action_handler)
    
    # Отключаем логирование запросов
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)
    
    return root_logger, action_logger