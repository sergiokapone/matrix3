# config.py
import os
from dataclasses import dataclass
from pathlib import Path
from requests.auth import HTTPBasicAuth

from dataclasses import field

from dotenv import load_dotenv

load_dotenv()


@dataclass
class WordPressConfig:
    base_url: str = "https://apd.ipt.kpi.ua"
    api_path: str = "/wp-json/wp/v2"
    # api_url: str = "https://apd.ipt.kpi.ua"
    username: str = field(default_factory=lambda: os.getenv("WP_USER", ""))
    password: str = field(default_factory=lambda: os.getenv("WP_PASSWORD", ""))

    def __post_init__(self):
        if not self.username or not self.password:
            raise ValueError("WP_USER або WP_PASSWORD не встановлені")

    @property
    def api_url(self) -> str:
        return f"{self.base_url}{self.api_path}"

    @property
    def auth(self) -> HTTPBasicAuth:
        return HTTPBasicAuth(self.username, self.password)


@dataclass
class AppConfig:
    yaml_data_folder: Path = Path("data")
    template_dir: Path = Path("templates")
    output_dir: Path = Path("disciplines")
    wp_links_dir: Path = Path("wp_links")
    lecturers_yaml: Path = yaml_data_folder / "lecturers.yaml"

    # def __post_init__(self):
    #     self.validate()

    # def validate(self):
    #     if not self.yaml_file.exists():
    #         raise FileNotFoundError(f"YAML file not found: {self.yaml_file}")
    #     if not self.template_dir.exists():
    #         raise FileNotFoundError(f"Template directory not found: {self.template_dir}")
