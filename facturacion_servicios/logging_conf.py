import json
import logging.config
from pathlib import Path

_CONFIG_PATH = Path(__file__).parent / "logging_config.json"


def setup_logging(config_path: Path = _CONFIG_PATH) -> None:
    with open(config_path) as f:
        config = json.load(f)
    logging.config.dictConfig(config)
