import os
import sys
import shlex
import subprocess

from pathlib import Path
from prompt_toolkit import PromptSession
from prompt_toolkit.completion import NestedCompleter
from core.config import AppConfig

config = AppConfig()



# ====== Список команд и флагов для автодополнения ======
completer = NestedCompleter.from_nested_dict({
    "generate": {"-a": None, "-d": None},
    "upload": {"-a": None, "-d": None, "-i": None},
    "index": {"-g": None, "-p": None, "-u": None},
    "scenario": {"-f": None},
    "dir": None,
    "clean": None,
    "exit": None,
    "quit": None,
})

def run_shell(yaml_file: str):
    """
    Запускает интерактивную оболочку для управления main.py
    с подстановкой yaml_file и автодополнением команд.
    """
    session = PromptSession()
    
    while True:
        try:
            text = session.prompt(f"{Path(yaml_file).stem}> ", completer=completer).strip()
            
            if not text:
                continue
            if text in ("exit", "quit"):
                break

            argv = shlex.split(text)
            # Вызываем main.py через subprocess с YAML и командой
            cmd = [sys.executable, "cli.py", yaml_file] + argv
            subprocess.run(cmd)
        
        except (EOFError, KeyboardInterrupt):
            print("\nВыход")
            break

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python cli_shell.py <yaml_file>")
        sys.exit(1)

    yaml_file = sys.argv[1]
    run_shell(yaml_file)
