# ============================================================================
# CLI INTERFACE
# ============================================================================

from pathlib import Path
import shutil
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
        "  python create_discipline_page.py data.yaml -d 'ЗO 05'                # Generate single discipline",
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


def main():
    """Головна функція з CLI інтерфейсом"""
    try:
        args = parse_arguments()

        # Налаштування логування
        global logger
        logger = setup_logging(args.log_level)

        # Конфігурація
        yaml_file = args.yaml_file

        # Виконуємо дії послідовно
        executed_actions = []

        # 1. Очищення (якщо потрібно)
        if args.clean:
            clean_output_directory(config.output_dir)
            executed_actions.append("clean")

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
            logger.error("No action specified. Use -h for help.")
            print_usage_examples()
            sys.exit(0)

        # Звіт про виконані дії
        logger.info("Completed actions")
        logger.info(f"Successfully completed: {', '.join(executed_actions)}")

    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        logger.warning(" Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Failed to generate index page: {e}")
        logger.error(f"Error: {str(e)}")
        sys.exit(1)


if __name__ == "__main__":
    main()