# THE MRIDANSH - Core Engine Utilities

import os
import yaml

class ConfigLoader:
    """Reads and enforces the global system variables across the multi-modal engine."""
    
    def __init__(self, config_path: str = "7_config/global_config.yaml"):
        self.config_path = config_path
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Critical System Failure: {self.config_path} not found.")
        self.config = self._load_yaml()

    def _load_yaml(self) -> dict:
        with open(self.config_path, "r") as stream:
            try:
                return yaml.safe_load(stream)
            except yaml.YAMLError as exc:
                raise RuntimeError(f"Error parsing configuration YAML matrix: {exc}")

    def get_param(self, key_path: str):
        """Access nested parameters using dot notation (e.g., 'spatial_bounds.crs')"""
        keys = key_path.split('.')
        val = self.config
        for k in keys:
            if isinstance(val, dict) and k in val:
                val = val[k]
            else:
                return None
        return val

# Self-test block to verify execution
if __name__ == "__main__":
    loader = ConfigLoader()
    print(f"System Node Booted: {loader.get_param('engine_version')}")
    print(f"Target Satellites Configured: {list(loader.config['satellite_channels'].keys())}")