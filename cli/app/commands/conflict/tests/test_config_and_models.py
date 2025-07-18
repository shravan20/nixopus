import unittest
import yaml
import tempfile
import os
from app.commands.conflict.models import (
    ConflictConfig,
    ConflictCheckResult,
)
from app.commands.conflict.conflict import (
    ConfigLoader,
)
from app.utils.logger import Logger


class TestConfigAndModels(unittest.TestCase):
    """Test configuration loading and data models"""

    def setUp(self):
        self.logger = Logger(verbose=False)
        self.config = ConflictConfig(
            config_file="test_config.yaml", environment="production", timeout=1, verbose=False, output="text"
        )

    def test_conflict_check_result_creation(self):
        """Test ConflictCheckResult model creation"""
        result = ConflictCheckResult(tool="docker", expected="20.10.0", current="20.10.5", status="compatible", conflict=False)

        self.assertEqual(result.tool, "docker")
        self.assertEqual(result.expected, "20.10.0")
        self.assertEqual(result.current, "20.10.5")
        self.assertFalse(result.conflict)

    def test_config_loader_valid_yaml_config(self):
        """Test ConfigLoader with valid YAML config"""
        config_data = {"deps": {"docker": {"version": "20.10.0"}, "go": {"version": "1.18.0"}, "python": {"version": "3.9.0"}}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            loader = ConfigLoader(self.logger)
            result = loader.load_config(temp_path)

            self.assertEqual(result, config_data)
            self.assertIn("deps", result)
            self.assertIn("docker", result["deps"])
            self.assertEqual(result["deps"]["docker"]["version"], "20.10.0")
        finally:
            os.unlink(temp_path)

    def test_config_loader_missing_file(self):
        """Test ConfigLoader with missing file"""
        loader = ConfigLoader(self.logger)

        with self.assertRaises(FileNotFoundError):
            loader.load_config("nonexistent.yaml")

    def test_config_loader_invalid_yaml(self):
        """Test ConfigLoader with invalid YAML"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            f.write("invalid: yaml: content: [")
            temp_path = f.name

        try:
            loader = ConfigLoader(self.logger)

            with self.assertRaises(ValueError):
                loader.load_config(temp_path)
        finally:
            os.unlink(temp_path)

    def test_empty_deps_handling(self):
        """Test handling of empty or missing deps section"""
        config_data = {}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = ConflictConfig(config_file=temp_path, environment="production", timeout=1, verbose=False, output="text")
            
            # Test that config is created successfully even with empty deps
            self.assertEqual(config.config_file, temp_path)
            self.assertEqual(config.environment, "production")
            self.assertEqual(config.timeout, 1)
            self.assertFalse(config.verbose)
            self.assertEqual(config.output, "text")
        finally:
            os.unlink(temp_path)


if __name__ == "__main__":
    unittest.main()
