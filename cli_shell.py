import sys
import shlex
import subprocess
from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter
from core.config import AppConfig

from core.logging_config import get_logger

logger = get_logger (__name__)
config = AppConfig()

# ====== Список команд и флагов для автодополнения ======
completer = NestedCompleter.from_nested_dict(
    {
        "generate": {"-a": None, "-d": None},
        "upload": {"-a": None, "-d": None, "-i": None},
        "index": {"-g": None, "-p": None, "-u": None},
        "scenario": {"-f": None},
        "dir": None,
        "clean": None,
        "exit": None,
        "quit": None,
    }
)


def choose_yaml_file() -> str:
    """Выбор YAML-файла из папки, указанной в config.yaml_data_folder"""
    folder: Path = config.yaml_data_folder
    if not folder.exists() or not folder.is_dir():
        print(f"Папка {folder} не существует или не является директорией.")
        sys.exit(1)

    # Получаем список всех yaml файлов
    yaml_files = list(folder.glob("*.yaml")) + list(folder.glob("*.yml"))
    if not yaml_files:
        print(f"В папці {folder} нема YAML-файлів.")
        sys.exit(1)

    print("Доступні YAML-файли:")
    for i, f in enumerate(yaml_files, 1):
        print(f"{i}. {f.name}")  # показываем только имя файла

    while True:
        choice = input(f"Виберіть файл з даними (1-{len(yaml_files)}): ").strip()
        if choice.isdigit():
            idx = int(choice) - 1
            if 0 <= idx < len(yaml_files):
                return str(yaml_files[idx])  # возвращаем путь в виде строки
        print("Неправильний вибір, спробуйте знову.")


def run_shell(yaml_file: str):
    """Запускает интерактивную оболочку для управления cli.py"""
    session = PromptSession()

    while True:
        try:
            text = session.prompt(
                f"{Path(yaml_file).stem}> ", completer=completer
            ).strip()

            if not text:
                continue
            if text in ("exit", "quit"):
                break

            try:
                argv = shlex.split(text)
            except ValueError as e:
                logger.error(f"Ошибка парсинга команды: {e}")
                continue
            
            cmd = [sys.executable, "cli.py", yaml_file] + argv
            subprocess.run(cmd)

        except (EOFError, KeyboardInterrupt):
            print("\nВыход")
            break


def main():
    while True:
        yaml_file = choose_yaml_file()  # выбор YAML
        run_shell(yaml_file)  # запуск интерактивной оболочки

        # После выхода из оболочки спрашиваем, хотим ли выбрать другой файл
        again = input("Хочете вибрати інший YAML-файл? (y/n): ").strip().lower()
        if again != "y":
            print("Вихід із програми.")
            break


if __name__ == "__main__":
    main()
