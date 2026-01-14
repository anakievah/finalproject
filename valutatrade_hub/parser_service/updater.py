import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from ..core.exceptions import ApiRequestError
from .api_clients import BaseApiClient, CoinGeckoClient, ExchangeRateApiClient
from .config import ParserConfig
from .storage import RatesStorage

logger = logging.getLogger(__name__)

class RatesUpdater:
    """Класс для обновления курсов валют."""
    
    def __init__(self, config: ParserConfig, storage: RatesStorage):
        """
        Инициализация обновителя курсов.
        
        Args:
            config: Конфигурация
            storage: Хранилище для сохранения данных
        """
        self.config = config
        self.storage = storage
        self.clients: List[BaseApiClient] = []
    
    def add_client(self, client: BaseApiClient):
        """
        Добавить клиента для получения курсов.
        
        Args:
            client: Клиент API
        """
        self.clients.append(client)
    
    def run_update(self, source: Optional[str] = None) -> Dict[str, Any]:
        """
        Запустить обновление курсов.
        
        Args:
            source: Источник для обновления (опционально)
            
        Returns:
            Dict[str, Any]: Результат обновления
        """
        logger.info("Starting rates update process")
        
        # Загружаем текущие курсы
        current_rates = self.storage.load_current_rates()
        if "pairs" not in current_rates:
            current_rates["pairs"] = {}
        
        update_results = {
            "success": True,
            "updated_pairs": [],
            "errors": [],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        # Фильтруем клиентов по источнику, если указано
        clients_to_use = self.clients
        if source:
            source_lower = source.lower()
            if source_lower == "coingecko":
                clients_to_use = [client for client in self.clients if isinstance(client, CoinGeckoClient)]
            elif source_lower == "exchangerate":
                clients_to_use = [client for client in self.clients if isinstance(client, ExchangeRateApiClient)]
        
        # Опрашиваем каждого клиента
        for client in clients_to_use:
            client_name = type(client).__name__
            logger.info(f"Fetching rates from {client_name}")
            
            try:
                new_rates = client.fetch_rates()
                
                # Обновляем курсы в текущих данных
                for pair, rate_data in new_rates.items():
                    current_rates["pairs"][pair] = rate_data
                    update_results["updated_pairs"].append(pair)
                    
                    # Добавляем запись в историю
                    history_record = {
                        "id": f"{pair}_{rate_data['updated_at']}",
                        "from_currency": pair.split('_')[0],
                        "to_currency": pair.split('_')[1],
                        "rate": rate_data["rate"],
                        "timestamp": rate_data["updated_at"],
                        "source": rate_data["source"],
                        "meta": {
                            "client": client_name
                        }
                    }
                    self.storage.append_to_history(history_record)
                
                logger.info(f"Successfully updated {len(new_rates)} rates from {client_name}")
                
            except ApiRequestError as e:
                error_msg = f"Failed to fetch rates from {client_name}: {str(e)}"
                logger.error(error_msg)
                update_results["errors"].append(error_msg)
                update_results["success"] = False
        
        # Обновляем время последнего обновления
        current_rates["last_refresh"] = datetime.utcnow().isoformat()
        
        # Сохраняем обновленные курсы
        self.storage.save_current_rates(current_rates)
        
        logger.info(f"Rates update completed. Updated {len(update_results['updated_pairs'])} pairs, encountered {len(update_results['errors'])} errors")
        
        return update_results