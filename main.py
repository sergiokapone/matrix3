# ============================================================================
# CLI INTERFACE
# ============================================================================

from pathlib import Path
import sys

from core.models import WordPressPage
from core.parse_index_links import parse_index_links
from core.config import AppConfig, WordPressConfig
from core.file_utils import load_yaml_data, save_wp_links_yaml
from core.html_generator import generate_discipline_page, generate_index_page
from core.logging_config import setup_logging
from core.wordpress_client import WordPressClient
from core.wordpress_uploader import upload_all_pages, upload_discipline_page, upload_index
from requests.auth import HTTPBasicAuth


config = AppConfig()

def create_wordpress_client():
    config = WordPressConfig()
    api_url = config.api_url
    auth = HTTPBasicAuth(config.username, config.password)

    # Створюємо клієнт з параметрами
    return WordPressClient(api_url=api_url, auth=auth)

client = create_wordpress_client()


def print_usage_examples():
    """Виводить приклади використання CLI"""
    examples = [
        "💡 Usage examples:",
        "  python create_discipline_page.py data.yaml -d 'PO 01'                # Generate single discipline",
        "  python create_discipline_page.py data.yaml --all                     # Generate all disciplines",
        "  python create_discipline_page.py data.yaml --all --upload            # Generate and upload all",
        "  python create_discipline_page.py data.yaml --upload                  # Upload existing pages",
        "  python create_discipline_page.py data.yaml --index                   # Generate index page",
        "  python create_discipline_page.py data.yaml --parse-index             # Parse WP links to index",
        "  python create_discipline_page.py data.yaml --upload-index            # Upload index to WP",
        "  python create_discipline_page.py data.yaml --all --clean             # Clean before generation"
    ]
    
    print("\n".join(examples))


def parse_arguments():
    """Парсинг аргументів командного рядка"""
    import argparse

    parser = argparse.ArgumentParser(
        description="WordPress discipline pages generator",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=print_usage_examples()
    )

    parser.add_argument("yaml_file", help="Path to YAML data file")
    parser.add_argument("--discipline", "-d", help="Specific discipline code")
    parser.add_argument("--template", "-t", default="discipline_template.html", help="Template file")
    parser.add_argument("--all", "-a", action="store_true", help="Generate all disciplines")
    parser.add_argument("--index", "-i", action="store_true", help="Create index page")
    parser.add_argument("--output", "-o", help="Output file or directory")
    parser.add_argument("--clean", "-c", action="store_true", help="Clean directory before generation")
    parser.add_argument("--upload-all", "-ua", action="store_true", help="Upload to WordPress")
    parser.add_argument("--parse-index", "-pi", action="store_true", help="Parse WP links to index")
    parser.add_argument("--upload-discipline", "-ud", help="Upload Discipline to WordPress")

    parser.add_argument("--upload-index", "-ui", action="store_true", help="Upload index to WordPress")
    parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], 
                        default="INFO", help="Logging level")

    return parser.parse_args()

def handle_single_discipline(yaml_file: str | Path, discipline_code: str):
    """CLI хендлер для генерації однієї дисципліни"""
    # Преобразуем в Path и проверяем существование
    yaml_path = Path(yaml_file)
    if not yaml_path.exists():
        # Если файл не найден, ищем в data folder
        yaml_path = config.yaml_data_folder / yaml_file
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_file}")
    
    output = config.output_dir / f"{discipline_code}.html"
    template_name = "discipline_template.html"

    return generate_discipline_page(
        str(yaml_path), 
        discipline_code, 
        str(output), 
        template_name
    )

def handle_all_disciplines(yaml_file: str | Path):
    """CLI хендлер для генерації всіх дисциплін з прогрес-баром"""
    
    yaml_path = Path(yaml_file)
    if not yaml_path.exists():
        yaml_path = config.yaml_data_folder / yaml_file
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_file}")
    
    # Спочатку отримуємо список всіх дисциплін
    data = load_yaml_data(yaml_path)
    if data is None:
        print("❌ Failed to load YAML data")
        return False
    
    all_disciplines = data.get("disciplines", {}).copy()
    if "elevative_disciplines" in data:
        all_disciplines.update(data.get("elevative_disciplines", {}))
    
    total = len(all_disciplines)
    print(f"🎯 Generating {total} disciplines from {yaml_path.name}")
    
    results = {}
    successful = 0
    
    # Генеруємо з прогресом
    for i, discipline_code in enumerate(all_disciplines.keys(), 1):
        print(f"[{i}/{total}] Generating {discipline_code}...", end=" ")
        
        output_filename = config.output_dir / f"{discipline_code}.html"
        
        success = generate_discipline_page(
            str(yaml_path),
            discipline_code,
            str(output_filename)
        )
        
        results[discipline_code] = success
        
        if success:
            print("✅")
            successful += 1
        else:
            print("❌")
    
    print(f"\n📊 Results: {successful}/{total} successful")
    
    return successful == total

def handle_index_page(yaml_file: str | Path):
    """CLI хендлер для генерації індексної сторінки зі списком дисциплін"""
    
    # Перевіряємо існування файлу
    yaml_path = Path(yaml_file)
    if not yaml_path.exists():
        yaml_path = config.yaml_data_folder / yaml_file
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_file}")
    
    # Визначаємо шлях для вихідного файлу
    output_file = config.output_dir / "index.html"
    
    logger.info(f"📄 Generating index page from: {yaml_path}")
    logger.info(f"📁 Output: {output_file}")
    
    try:
        # Генеруємо індексну сторінку
        generate_index_page(str(yaml_path), str(output_file))
        print("✅ Index page generated successfully!")
        return True
        
    except Exception as e:
        logger.error(f"❌ Failed to generate index page: {e}")
        return False


def handle_parse_links(yaml_file: str | Path):
    """CLI хендлер для заміни локальних посилань на WordPress посилання"""
    
    if not Path(yaml_file).exists():
        yaml_file = config.yaml_data_folder / yaml_file
        if not yaml_file.exists():
            raise FileNotFoundError(f"YAML file not found: {yaml_file}")
    
    print(f"🔗 Parsing WordPress links for: {config.wp_links_dir}")
    
    try:
        result = parse_index_links(str(yaml_file))
        return result
    except Exception as e:
        logger.error(f"❌ Failed to parse links: {e}")
        return False


def handle_upload_page(
    discipline_code: str,
    data_yaml: str | Path = None
):
    """CLI хендлер для завантаження сторінки дисципліни на WordPress"""
    
    # Якщо data_yaml не передано, шукаємо стандартний файл
    if data_yaml is None:
        logger.error("❌ No YAML file specified and no default file found")
        return False
    
    # Перевіряємо існування файлу
    yaml_path = Path(data_yaml)
    if not yaml_path.exists():
        yaml_path = config.yaml_data_folder / data_yaml
        if not yaml_path.exists():
            raise FileNotFoundError(f"YAML file not found: {data_yaml}")
    
    try:
        # Завантажуємо дані з YAML
        yaml_data = load_yaml_data(yaml_path)
        if not yaml_data:
            logger.erro("❌ Failed to load YAML data")
            return False
        
        # Отримуємо parent_id з метаданих
        wp_parent_id = yaml_data.get("metadata", {}).get("page_id")
        if not wp_parent_id:
            logger.error("❌ page_id not found in YAML metadata")
            return False
        
        # Отримуємо всі дисципліни
        all_disciplines = {**yaml_data.get('disciplines', {}), **yaml_data.get('elevative_disciplines', {})}
        
       
        # Перевіряємо чи існує дисципліна
        if discipline_code not in all_disciplines:
            logger.error(f"❌ Discipline '{discipline_code}' not found in YAML")
            logger.info(f"Available disciplines: {list(all_disciplines.keys())}")
            return False
        
        
        # Завантажуємо сторінку
        page = upload_discipline_page(
            discipline_code=discipline_code,
            discipline_info=all_disciplines[discipline_code],
            parent_id=wp_parent_id,
            client=client
        )
        
        if page:
            logger.info(f"✅ Successfully uploaded: {discipline_code}")
            logger.info(f"📝 Title: {page.title}")
            logger.info(f"🔗 Link: {page.link}")
            logger.info(f"🆔 ID: {page.id}")
            return True
        else:
            logger.error(f"❌ Failed to upload: {discipline_code}")
            return False
            
    except Exception as e:
        logger.info(f"❌ Error uploading {discipline_code}: {e}")
        return False


def handle_upload_all_pages(yaml_file: str | Path) -> bool:
        """
        Handler для завантаження всіх дисциплін на WordPress.
        
        Аргументи:
            yaml_file: шлях до YAML файлу з даними дисциплін
            parent_id: ID батьківської сторінки у WordPress
            client: інстанс WordPressClient
            
        Повертає:
            True якщо хоча б одна сторінка завантажена, False інакше
        """
        yaml_path = (config.yaml_data_folder / Path(yaml_file)).resolve()
        
        # Якщо файлу немає, створюємо порожній
        if not yaml_path.exists():
            logger.warning(f"{yaml_path} не знайдено, створюю порожній YAML")
            yaml_path.write_text("disciplines: {}\nelevative_disciplines: {}\n", encoding="utf-8")
        
        try:
            wp_data = upload_all_pages(
                yaml_file=yaml_path,
                client=client
            )
            if wp_data:
                logger.info(f"✅ Успішно завантажено {len(wp_data)} сторінок")
                save_wp_links_yaml(wp_data, config.wp_links_dir / f'wp_links_{yaml_file}') 
                return True
            else:
                logger.warning("❌ Жодної сторінки не було завантажено")
                return False
        except Exception as e:
            logger.error(f"❌ Помилка під час завантаження сторінок: {e}")
            return False
    

def handle_upload_index(yaml_file: str | Path) -> WordPressPage | None:
    """
    Обработчик для CLI: загружает или обновляет индексную страницу на WordPress.

    Args:
        index_file (str | Path): Путь к HTML-файлу индекса.
        page_id (int): ID существующей страницы на WP для обновления.
        client (WordPressClient): Экземпляр клиента WP.

    Returns:
        WordPressPage | None: Загруженная/обновленная страница или None при ошибке.
    """
    yaml_path = config.yaml_data_folder / yaml_file
    page = upload_index(yaml_path, client)

    if page:
        logger.info(f"✅ Индексная страница успешно загружена: {page.title} (ID: {page.id})")
    else:
        logger.error(f"❌ Не удалось загрузить индексную страницу")

    return page


def find_default_yaml_file() -> Path | None:
    """Шукає стандартний YAML файл у папці даних"""
    yaml_files = list(config.yaml_data_folder.glob("*.yaml")) + list(config.yaml_data_folder.glob("*.yml"))
    if yaml_files:
        return yaml_files[0]  # Повертаємо перший знайдений файл
    return None


def main():
    """Головна функція з CLI інтерфейсом"""
    try:
        args = parse_arguments()

        # Налаштування логування
        global logger
        logger = setup_logging(args.log_level)

        # Конфігурація
        yaml_file = args.yaml_file
        
        # if not yaml_file.exists():
        #     logger.error("YAML file not found")
        #     sys.exit(1)

        # Виконуємо дії послідовно
        executed_actions = []

        # # 1. Очищення (якщо потрібно)
        # if args.clean:
        #     config = AppConfig(yaml_file=yaml_file)
        #     clean_output_directory(config.output_dir)
        #     executed_actions.append("clean")

        # 2. Генерація однієї дисципліни
        if args.discipline:
            handle_single_discipline(yaml_file, args.discipline)
            executed_actions.append(f"generate discipline {args.discipline} from {yaml_file}")

        # 3. Генерація всіх дисциплін
        if args.all:
            handle_all_disciplines(yaml_file)
            executed_actions.append("generate all disciplines")

        # 4. Генерація індексу
        if args.index:
            handle_index_page(yaml_file)
            executed_actions.append("generate index")

        # 5. Парсинг індексу
        if args.parse_index:
            handle_parse_links(yaml_file)
            executed_actions.append("parse index links")

        # 6. Завантаження дисципліни
        if args.upload_discipline:
            handle_upload_page(args.upload_discipline, yaml_file)
            executed_actions.append("upload disciplines")

        # 7. Завантаження дисципліни
        if args.upload_all:
            handle_upload_all_pages(yaml_file)
            executed_actions.append("upload disciplines")

        # 8. Завантаження всіх дисциплін
        if args.upload_index:
            handle_upload_index(yaml_file)
            executed_actions.append("upload index")

        # Якщо нічого не виконано - показуємо довідку
        if not executed_actions:
            logger.error("❌ No action specified. Use -h for help.")
            print_usage_examples()
            sys.exit(0)

        # Звіт про виконані дії
        logger.info("✅ Completed actions")
        logger.info(f"✅ Successfully completed: {', '.join(executed_actions)}")

    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        logger.info("⚠️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Failed to generate index page: {e}")
        logger.error(f"❌ Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()