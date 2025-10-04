import argparse
import sys
from pathlib import Path


from core.config import AppConfig, WordPressConfig
from core.handlers import (
    clean_output_directory,
    handle_generate_single_discipline,
    handle_generate_all_disciplines,
    handle_parse_index_links,
    handle_upload_all_disciplines,
    handle_upload_discipline,
    handle_upload_index,
    handle_generate_index,
    handle_parse_index_links,
)

from core.wordpress_client import WordPressClient
from requests.auth import HTTPBasicAuth


def create_wordpress_client():
    wp_config = WordPressConfig()
    auth = HTTPBasicAuth(wp_config.username, wp_config.password)
    return WordPressClient(api_url=wp_config.api_url, auth=auth)


from core.logging_config import setup_logging, get_logger
setup_logging(level="DEBUG")

logger = get_logger()

client = create_wordpress_client()
config = AppConfig()




def resolve_yaml_path(yaml_arg: str) -> Path:
    """Возвращает корректный путь к YAML файлу"""
    yaml_path = Path(yaml_arg)
    if not yaml_path.is_absolute() and not yaml_path.exists():
        yaml_path = config.yaml_data_folder / yaml_arg
    return yaml_path

# def resolve_output_path(output_dir: str) -> Path:
#     """Возвращает корректный путь к YAML файлу"""
#     output_dir = Path(output_dir)
#     if not output_dir.is_absolute() and not output_dir.exists():
#         output_dir = config.output_dir
#     return output_dir


def main():
    parser = argparse.ArgumentParser(description="WordPress discipline pages manager")
    parser.add_argument("yaml_file", help="Path to YAML data file")  # перший аргумент
    parser.add_argument("--clean", "-c", action="store_true", help="Clean directory before generation")
    
    subparsers = parser.add_subparsers(dest="command", required=True)

    # =========================
    # generate
    # =========================
    gen_parser = subparsers.add_parser("generate", help="Generate discipline pages")
    gen_parser.add_argument("--discipline", "-d", help="Generate single discipline")
    gen_parser.add_argument("--all", "-a", action="store_true", help="Generate all disciplines")

    # =========================
    # upload
    # =========================
    upload_parser = subparsers.add_parser("upload", help="Upload pages to WordPress")
    upload_parser.add_argument("--discipline", "-d", help="Upload single discipline")
    upload_parser.add_argument("--all", "-a", action="store_true", help="Upload all disciplines")
    upload_parser.add_argument("--index", "-i", action="store_true", help="Upload index page")

    # =========================
    # index
    # =========================
    index_parser = subparsers.add_parser("index", help="Work with index page")
    index_parser.add_argument("--generate", "-g", action="store_true", help="Generate index page")
    index_parser.add_argument("--parse", "-p", action="store_true", help="Parse WordPress links")
    index_parser.add_argument("--upload", "-u", action="store_true", help="Upload index page")
    
    clean_folder = subparsers.add_parser("clean", help="Clean output folder")

    args = parser.parse_args()

    yaml_file = resolve_yaml_path(args.yaml_file)
    output_dir = config.output_dir
    
    
    # yaml_file = config.yaml_data_folder
        
    if not yaml_file.exists():
        logger.error(f"YAML file not found: {yaml_file}")
        sys.exit(1)

    try:
        # =========================
        # generate
        # =========================
        if args.command == "generate":
            if args.all:
                handle_generate_all_disciplines(yaml_file, output_dir)
            elif args.discipline:
                handle_generate_single_discipline(yaml_file, config.output_dir / f'{args.discipline}.html', args.discipline)
            else:
                logger.error("Specify --all or --discipline")

        # =========================
        # upload
        # =========================
        elif args.command == "upload":
            if args.all:
                handle_upload_all_disciplines(yaml_file, config.output_dir)
            elif args.discipline:
                handle_upload_discipline(args.discipline, yaml_file, client)
            else:
                logger.error("Specify --all, --discipline")

        # =========================
        # index
        # =========================
        elif args.command == "index":
            if args.generate:
                handle_generate_index(yaml_file, config.output_dir / "index.html")
            if args.parse:
                handle_parse_index_links(yaml_file)
            if args.upload:
                handle_upload_index(yaml_file, client)
        
        elif args.command == "clean":
            logger.info(f"Старт очищення директорії {output_dir}")
            try:
                clean_output_directory(output_dir)
                logger.info("Операція завершена успішно")
            except Exception as e:
                logger.critical(f"Неможливо завершити очищення: {e}")
                raise SystemExit(1)

    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
