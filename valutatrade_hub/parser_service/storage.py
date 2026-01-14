import json
import logging
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List

logger = logging.getLogger(__name__)

class RatesStorage:
    """Класс для работы с хранилищем курсов валют."""
    
    def __init__(self, rates_file: Path, history_file: Path):
        """
        Инициализация хранилища.
        
        Args:
            rates_file: Путь к файлу с актуальными курсами
            history_file: Путь к файлу с историей курсов
        """
        self.rates_file = rates_file
        self.history_file = history_file
    
    def _read_json(self, file_path: Path) -> Any:
        """Прочитать данные из JSON файла."""
        try:
            if not file_path.exists():
                return {}
            
            with open(file_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError, IOError) as e:
            logger.error(f"Error reading JSON file {file_path}: {str(e)}")
            return {}
    
    def _write_json(self, file_path: Path, data: Any):
        """Записать данные в JSON файл атомарно."""
        try:
            # Создаем временную директорию для атомарной записи
            with tempfile.NamedTemporaryFile(mode='w', dir=file_path.parent, delete=False, suffix='.tmp', encoding='utf-8') as tmp_file:
                json.dump(data, tmp_file, indent=2, ensure_ascii=False)
                tmp_file_path = Path(tmp_file.name)
            
            # Атомарно заменяем файл
            tmp_file_path.replace(file_path)
            logger.info(f"Successfully wrote data to {file_path}")
            
        except (IOError, OSError) as e:
            logger.error(f"Error writing JSON file {file_path}: {str(e)}")
            raise
    
    def load_current_rates(self) -> Dict[str, Any]:
        """Загрузить текущие курсы из файла."""
        return self._read_json(self.rates_file)
    
    def save_current_rates(self, rates_data: Dict[str, Any]):
        """
        Сохранить текущие курсы в файл.
        
        Args:
            rates_data: Данные о курсах
        """
        # Добавляем время последнего обновления, если его нет
        if "last_refresh" not in rates_data:
            rates_data["last_refresh"] = datetime.utcnow().isoformat()
        
        self._write_json(self.rates_file, rates_data)
        logger.info(f"Saved current rates to {self.rates_file}")
    
    def load_history(self) -> List[Dict]:
        """Загрузить историю курсов из файла."""
        history = self._read_json(self.history_file)
        return history if isinstance(history, list) else []
    
    def append_to_history(self, record: Dict):
        """
        Добавить запись в историю курсов.
        
        Args:
            record: Запись для добавления
        """
        history = self.load_history()
        history.append(record)
        
        # Ограничиваем размер истории для производительности
        MAX_HISTORY_SIZE = 10000
        if len(history) > MAX_HISTORY_SIZE:
            history = history[-MAX_HISTORY_SIZE:]
        
        self._write_json(self.history_file, history)
        logger.info(f"Appended record to history file {self.history_file}")