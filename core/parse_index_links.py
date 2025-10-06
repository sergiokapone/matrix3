import re
from pathlib import Path

import yaml

from core.config import AppConfig
from core.logging_config import get_logger

logger = get_logger(__name__)

config = AppConfig()


def parse_index_links(data_yaml: str | Path) -> bool:
    """
    Заменяет локальные ссылки на дисциплины в HTML-файле на ссылки из WordPress.

    Функция выполняет следующие действия:
    1. Загружает соответствия кодов дисциплин и WP-ссылок из YAML-файла
    2. Проверяет совпадение метаданных (год, степень) между основным YAML и WP-ссылками
    3. Находит все ссылки формата 'ЗО_01.html', 'ПО_02.html' и т.д.
    4. Заменяет их на соответствующие WordPress URL

    Args:
        data_yaml (str | Path): Путь к основному YAML-файлу с метаданными.
            Используется для проверки соответствия года и степени.

    Returns:
        None

    Side Effects:
        - Перезаписывает файл index.html в output_dir с обновленными ссылками
        - Выводит статус операции в консоль

    Формат YAML с WP-ссылками (wp_links/wp_links_*.yaml):
        year: "2024"
        degree: "bachelor"
        links:
          ЗО 01: "https://example.com/zo-01"
          ПО 02: "https://example.com/po-02"

    Поддерживаемые коды дисциплин:
        - ЗО (Загальноосвітні)
        - ПО (Професійні обов'язкові)
        - ПВ (Професійні вибіркові)
        - НК (Нормативні курси)
        - ВК (Вибіркові курси)

    Examples:
        >>> parse_index_links("data/bachelor_2024.yaml")
        ✅ href в disciplines/index.html заменены на WP ссылки для ЗО_XX / ПО_XX

        >>> parse_index_links("data/master_2023.yaml")
        ❌ Метаданные не совпадают: WP (2024/bachelor) vs YAML (2023/master)

    Notes:
        - Ссылки вида 'ЗО_01.html' и 'ЗО 01.html' обрабатываются одинаково
        - Если код дисциплины не найден в YAML, подставляется "#"
        - Название YAML-файла с WP-ссылками формируется автоматически
          из имени основного YAML (wp_links_<stem>.yaml)
    """
    # Беремо шлях до index.html з config
    index_file = config.output_dir / "index.html"
    if not index_file.exists():
        logger.error(f"Файл {index_file} не найден")
        return False

    # Формируем путь к YAML-файлу с WordPress ссылками
    data_yaml_path = Path(data_yaml)
    data_yaml_stem = data_yaml_path.stem
    wp_links_yaml = Path("wp_links") / f"wp_links_{data_yaml_stem}.yaml"

    # Проверяем существование файла с WP ссылками
    if not wp_links_yaml.exists():
        logger.error(f"Файл с WordPress ссылками не найден: {wp_links_yaml}")
        return False

    # Загружаем данные о WordPress ссылках из YAML
    with open(wp_links_yaml, encoding="utf-8") as f:
        wp_data = yaml.safe_load(f)

    # Извлекаем словарь соответствий "код дисциплины" -> "WP URL"
    wp_links = wp_data.get("links", {})
    # Извлекаем метаданные для проверки совпадения
    wp_year = wp_data.get("year", "")
    wp_degree = wp_data.get("degree", "")

    # Проверяем соответствие метаданных с основным YAML
    with open(data_yaml, encoding="utf-8") as f:
        meta_data = yaml.safe_load(f)

    # Получаем год и степень из основного YAML
    year = meta_data.get("metadata", {}).get("year", "")
    degree = meta_data.get("metadata", {}).get("degree", "")

    # Если метаданные не совпадают, прерываем выполнение
    if wp_year != year or wp_degree != degree:
        logger.error(
            f"Метаданные не совпадают: WP ({wp_year}/{wp_degree}) vs YAML ({year}/{degree}). Парсинг отменен."
        )
        return False

    # Читаем содержимое HTML-файла
    html = index_file.read_text(encoding="utf-8")

    # Регулярное выражение для поиска ссылок на дисциплины:
    # - Ищет href="XX_NN.html" или href="XX NN.html"
    # - XX - двухбуквенный код типа дисциплины (ЗО, ПО, ПВ, НК, ВК)
    # - NN - двузначный номер (с опциональной дробной частью вида .1, .2)
    # Примеры: "ЗО_01.html", "ПО 02.html", "ПВ_03.1.html"
    pattern = re.compile(r'href="((ЗО|ПО|ПВ|НК|ВК)[ _]\d{2}(?:\.\d+)?)\.html"')

    def replace_href(match):
        """
        Callback-функция для замены найденного href на WordPress URL.

        Args:
            match (re.Match): Объект совпадения регулярного выражения

        Returns:
            str: Новый атрибут href с WordPress URL или "#" если код не найден

        Notes:
            - Нормализует код дисциплины: заменяет '_' на пробел и убирает лишние пробелы
            - Использует замыкание для доступа к wp_links из внешней функции
        """
        # Извлекаем полный код дисциплины (например, "ЗО_01" или "ПО 02")
        # group(1) содержит весь код без .html
        code = match.group(1).replace("_", " ").strip()

        # Ищем соответствующий WordPress URL в словаре
        # Если код не найден, используем заглушку "#"
        wp_url = wp_links.get(code, "#")

        # Возвращаем новый атрибут href
        return f'href="{wp_url}"'

    # Выполняем замену всех найденных ссылок
    html_new = pattern.sub(replace_href, html)

    # Сохраняем обновленный HTML обратно в файл
    index_file.write_text(html_new, encoding="utf-8")

    # Выводим сообщение об успешном выполнении
    logger.debug(f"href в {index_file} заменены на WP ссылки для ЗО_XX / ПО_XX")

    return True
