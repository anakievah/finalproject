# Makefile для ValutaTrade Hub
# Совместим с Windows (PowerShell/CMD) и Unix-системами (Linux/Mac)

# Определяем, в какой операционной системе мы работаем
ifeq ($(OS),Windows_NT)
    PYTHON := python
    RM := del /Q
    MKDIR := mkdir
    TOUCH := type nul >
else
    PYTHON := python3
    RM := rm -f
    MKDIR := mkdir -p
    TOUCH := touch
endif

# Цель по умолчанию
.DEFAULT_GOAL := help

# Установка зависимостей
install:
	@echo "🔧 Установка зависимостей..."
	poetry install

# Запуск проекта
project:
	@echo "🚀 Запуск ValutaTrade Hub..."
	poetry run project

# Сборка пакета
build:
	@echo "📦 Сборка пакета..."
	poetry build

# Публикация (только для тестирования)
publish:
	@echo "📤 Публикация (тестовый режим)..."
	poetry publish --dry-run

# Установка пакета из локальной сборки
package-install:
	@echo "📥 Установка пакета из локальной сборки..."
	$(PYTHON) -m pip install dist/*.whl

# Статический анализ кода
lint:
	@echo "🔍 Статический анализ кода..."
	poetry run ruff check .

# Автоматическое исправление замечаний
lint-fix:
	@echo "🛠️ Автоматическое исправление замечаний..."
	poetry run ruff check . --fix

# Форматирование кода
format:
	@echo "✏️ Форматирование кода..."
	poetry run ruff format .

# Очистка проекта
clean:
	@echo "🧹 Очистка проекта..."
	$(RM) *.pyc
	$(RM) *.pyo
	$(RM) *.pyd
	$(RM) *.log
	$(RM) *.tmp
	$(RM) __pycache__
	$(RM) .pytest_cache
	$(RM) .mypy_cache
	$(RM) .ruff_cache
	$(RM) .coverage
	$(RM) htmlcov
	$(RM) .tox
	$(RM) *.egg-info
	$(RM) build
	$(RM) dist

# Создание структуры проекта
init-project:
	@echo "🏗️ Инициализация структуры проекта..."
	$(MKDIR) data
	$(MKDIR) logs
	$(MKDIR) valutatrade_hub
	$(MKDIR) valutatrade_hub/core
	$(MKDIR) valutatrade_hub/cli
	$(MKDIR) valutatrade_hub/infra
	$(MKDIR) valutatrade_hub/parser_service
	$(TOUCH) data/.gitkeep
	$(TOUCH) logs/.gitkeep
	$(TOUCH) valutatrade_hub/__init__.py
	$(TOUCH) valutatrade_hub/core/__init__.py
	$(TOUCH) valutatrade_hub/cli/__init__.py
	$(TOUCH) valutatrade_hub/infra/__init__.py
	$(TOUCH) valutatrade_hub/parser_service/__init__.py

# Создание JSON файлов
init-data:
	@echo "💾 Инициализация данных..."
	@echo "[]" > data/users.json
	@echo "[]" > data/portfolios.json
	@echo "[]" > data/exchange_rates.json
	@echo '{ \
  "pairs": { \
    "USD_EUR": { \
      "rate": 0.925, \
      "updated_at": "2026-01-13T12:00:00Z", \
      "source": "default" \
    }, \
    "USD_RUB": { \
      "rate": 92.5, \
      "updated_at": "2026-01-13T12:00:00Z", \
      "source": "default" \
    }, \
    "USD_BTC": { \
      "rate": 0.0000168, \
      "updated_at": "2026-01-13T12:00:00Z", \
      "source": "default" \
    }, \
    "USD_ETH": { \
      "rate": 0.000268, \
      "updated_at": "2026-01-13T12:00:00Z", \
      "source": "default" \
    } \
  }, \
  "last_refresh": "2026-01-13T12:00:00Z" \
}' > data/rates.json

# Справка по командам
help:
	@echo "🎯 ValutaTrade Hub - Makefile commands"
	@echo ""
	@echo "Основные команды:"
	@echo "  make install        - Установить зависимости"
	@echo "  make project        - Запустить проект"
	@echo "  make build          - Собрать пакет"
	@echo "  make publish        - Протестировать публикацию"
	@echo "  make package-install - Установить пакет из локальной сборки"
	@echo ""
	@echo "Разработка:"
	@echo "  make lint           - Статический анализ кода"
	@echo "  make lint-fix       - Автоматическое исправление замечаний"
	@echo "  make format         - Форматирование кода"
	@echo ""
	@echo "Обслуживание:"
	@echo "  make clean          - Очистить проект"
	@echo "  make init-project   - Инициализировать структуру проекта"
	@echo "  make init-data      - Инициализировать данные"
	@echo ""

# Синтаксический сахар для Windows
.PHONY: all clean install project build publish package-install lint lint-fix format help init-project init-data