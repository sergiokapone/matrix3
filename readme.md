# 🎓 Генератор сторінок дисциплін для WordPress

**Automated system for generating and managing educational discipline pages for WordPress**

## 📖 Опис

Цей проект автоматизує процес створення та управління сторінками навчальних дисциплін для WordPress. Система генерує HTML-сторінки на основі YAML-даних, завантажує їх на WordPress через REST API та створює індексні сторінки з посиланнями на всі дисципліни.

## ✨ Особливості

- 🚀 Автоматична генерація сторінок дисциплін з YAML-даних
- 🌐 Інтеграція з WordPress через REST API
- 📊 Структуровані дані - компетенції, результати навчання, викладачі
- 🎨 Jinja2 шаблони - гнучка система шаблонів
- 🛡️ Обробка помилок - retry логіка та детальне логування

## 📁 Базові команди

```
# Генерація однієї дисципліни
pipenv run python main.py bachelor2024.yaml -d "ПО 01"

# Генерація всіх дисциплін
pipenv run python main.py bachelor2024.yaml --all

# Генерація індексної сторінки
pipenv run python main.py bachelor2024.yaml --index

# Завантаження всіх сторінок на WordPress
pipenv run python main.py bachelor2024.yaml --all --upload

# Завантаження індексної сторінки
pipenv run python main.py bachelor2024.yaml --upload-index
```
