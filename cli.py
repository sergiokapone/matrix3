import argparse
import sys
from pathlib import Path

from requests.auth import HTTPBasicAuth

from core.config import AppConfig, WordPressConfig
from core.handlers import (
    clean_output_directory,
    handle_dir_discipline,
    handle_generate_all_disciplines,
    handle_generate_index,
    handle_generate_single_discipline,
    handle_parse_index_links,
    handle_upload_all_disciplines,
    handle_upload_discipline,
    handle_upload_index,
)
from core.logging_config import get_logger
from core.wordpress_client import WordPressClient


def create_wordpress_client() -> Warning:
    wp_config = WordPressConfig()
    auth = HTTPBasicAuth(wp_config.username, wp_config.password)
    return WordPressClient(api_url=wp_config.api_url, auth=auth)


logger = get_logger(__name__)

client = create_wordpress_client()

config = AppConfig()


def resolve_yaml_path(yaml_arg: str) -> Path:
    """Возвращает корректный путь к YAML файлу"""
    yaml_path = Path(yaml_arg)
    if not yaml_path.is_absolute() and not yaml_path.exists():
        yaml_path = config.yaml_data_folder / yaml_arg
    return yaml_path


def handle_generate(args: str, yaml_file: Path, output_dir: Path) -> None:
    if args.all:
        handle_generate_all_disciplines(yaml_file, output_dir)
        logger.info("All disciplines generated")
    elif args.discipline:
        handle_generate_single_discipline(
            yaml_file,
            output_dir / f"{args.discipline}.html",
            args.discipline,
        )
        logger.info(f"Discipline {args.discipline} generated")
    else:
        logger.error("Specify --all or --discipline")


def handle_upload(args: str, yaml_file: Path, client: WordPressClient) -> None:
    if args.all:
        wp_links_file = config.wp_links_dir / f"wp_links_{yaml_file.stem}.yaml"
        handle_upload_all_disciplines(yaml_file, wp_links_file, client)
        logger.info("All disciplines uploaded")
    elif args.discipline:
        handle_upload_discipline(args.discipline, yaml_file, client)
        logger.info(f"Discipline {args.discipline} uploaded")
    elif getattr(args, "index", False):
        handle_upload_index(yaml_file, client)
        logger.info("Index page uploaded")
    else:
        logger.error("Specify --all, --discipline, or --index")


def handle_index(
    args: str, yaml_file: Path, client: WordPressClient, output_dir: Path
) -> None:
    if getattr(args, "generate", False):
        handle_generate_index(yaml_file, output_dir / "index.html")
        logger.info("Index file generated")
    if getattr(args, "parse", False):
        handle_parse_index_links(yaml_file)
        logger.info("Index file parsed")
    if getattr(args, "upload", False):
        handle_upload_index(yaml_file, client)
        logger.info("Index file uploaded")


def handle_scenario(
    args: str, yaml_file: Path, client: WordPressClient, output_dir: Path
) -> None:
    if getattr(args, "full", False):
        clean_output_directory(output_dir)
        logger.info("Folder cleaned")

        handle_generate_all_disciplines(yaml_file, output_dir)
        logger.info("All disciplines generated")

        wp_links_file = config.wp_links_dir / f"wp_links_{yaml_file.stem}.yaml"
        handle_upload_all_disciplines(yaml_file, wp_links_file, client)
        logger.info("All disciplines uploaded")

        handle_generate_index(yaml_file, output_dir / "index.html")
        handle_parse_index_links(yaml_file)
        handle_upload_index(yaml_file, client)
        logger.info("Index page generated, parsed, and uploaded")
    else:
        logger.error("Specify --full for scenario")


def dispatch_command(args: str, yaml_file: Path, client: WordPressClient) -> None:
    output_dir = config.output_dir

    match args.command:
        case "generate":
            handle_generate(args, yaml_file, output_dir)
        case "upload":
            handle_upload(args, yaml_file, client)
        case "index":
            handle_index(args, yaml_file, client, output_dir)
        case "dir":
            handle_dir_discipline(yaml_file)
        case "clean":
            clean_output_directory(output_dir)
            logger.info("Output directory cleaned")
        case "scenario":
            handle_scenario(args, yaml_file, client, output_dir)
        case _:
            logger.error(f"Unknown command: {args.command}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="WordPress discipline pages manager")

    parser.add_argument("yaml_file", help="Path to YAML data file")

    parser.add_argument(
        "--clean",
        "-c",
        action="store_true",
        help="Clean directory before generation",
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    # =========================
    # generate
    # =========================
    gen_parser = subparsers.add_parser("generate", help="Generate discipline pages")
    gen_parser.add_argument("--discipline", "-d", help="Generate single discipline")
    gen_parser.add_argument(
        "--all", "-a", action="store_true", help="Generate all disciplines"
    )

    # =========================
    # upload
    # =========================
    upload_parser = subparsers.add_parser("upload", help="Upload pages to WordPress")
    upload_parser.add_argument("--discipline", "-d", help="Upload single discipline")
    upload_parser.add_argument(
        "--all", "-a", action="store_true", help="Upload all disciplines"
    )
    upload_parser.add_argument(
        "--index", "-i", action="store_true", help="Upload index page"
    )

    # =========================
    # index
    # =========================
    index_parser = subparsers.add_parser("index", help="Work with index page")
    index_parser.add_argument(
        "--generate", "-g", action="store_true", help="Generate index page"
    )
    index_parser.add_argument(
        "--parse", "-p", action="store_true", help="Parse WordPress links"
    )
    index_parser.add_argument(
        "--upload", "-u", action="store_true", help="Upload index page"
    )

    # =========================
    # dir / clean
    # =========================
    subparsers.add_parser("dir", help="Show disciplines")
    subparsers.add_parser("clean", help="Clean output folder")

    # =========================
    # scenario
    # =========================
    scenario_parser = subparsers.add_parser("scenario", help="Run predefined workflows")
    scenario_parser.add_argument(
        "--full",
        "-f",
        action="store_true",
        help="Generate all, upload all, and rebuild index",
    )

    return parser


def main(*args: tuple) -> None:
    parser = build_parser()
    args = parser.parse_args()
    yaml_file = resolve_yaml_path(args.yaml_file)
    if not yaml_file.exists():
        logger.error(f"YAML file not found: {yaml_file}")
        sys.exit(1)

    try:
        dispatch_command(args, yaml_file, client)
    except KeyboardInterrupt:
        logger.warning("Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
