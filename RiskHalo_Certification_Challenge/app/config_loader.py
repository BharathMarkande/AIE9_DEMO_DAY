import yaml
from pathlib import Path

def load_rules_config(config_path="config/rules_config.yaml"):
    """
    Loads trading rule configuration from YAML file.
    """

    path = Path(config_path)

    if not path.exists():
        raise FileNotFoundError(f"Rules config not found at {config_path}")

    with open(path, "r") as file:
        config = yaml.safe_load(file)

    return config