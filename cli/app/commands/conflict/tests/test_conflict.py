import unittest
from unittest.mock import Mock, patch, MagicMock, call
import yaml
import tempfile
import os
import subprocess
from app.commands.conflict.conflict import (
    ConflictConfig,
    ConflictService,
    ConfigLoader,
    ToolVersionChecker,
    ConflictChecker,
    ConflictCheckResult,
)
from app.utils.logger import Logger


class TestConflictCommand(unittest.TestCase):

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

    @patch("subprocess.run")
    def test_tool_version_checker_successful(self, mock_run):
        """Test ToolVersionChecker with successful version check"""
        mock_result = Mock()
        mock_result.returncode = 0
        mock_result.stdout = "Docker version 20.10.5, build 55c4c88"
        mock_run.return_value = mock_result

        checker = ToolVersionChecker(5, self.logger)
        version = checker.get_tool_version("docker")

        self.assertEqual(version, "20.10.5")
        mock_run.assert_called_once_with(["docker", "--version"], capture_output=True, text=True, timeout=5)

    @patch("subprocess.run")
    def test_tool_version_checker_not_found(self, mock_run):
        """Test ToolVersionChecker with tool not found"""
        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stdout = ""
        mock_run.return_value = mock_result

        checker = ToolVersionChecker(5, self.logger)
        version = checker.get_tool_version("nonexistent")

        self.assertIsNone(version)

    @patch("subprocess.run")
    def test_tool_version_checker_timeout(self, mock_run):
        """Test ToolVersionChecker with timeout"""
        mock_run.side_effect = subprocess.TimeoutExpired("cmd", 5)

        checker = ToolVersionChecker(5, self.logger)
        version = checker.get_tool_version("slow_tool")

        self.assertIsNone(version)

    def test_version_comparison(self):
        """Test version comparison logic"""
        checker = ToolVersionChecker(5, self.logger)

        # Test valid version comparisons
        self.assertTrue(checker.compare_versions("20.10.5", "20.10.0"))
        self.assertTrue(checker.compare_versions("20.10.0", "20.10.0"))
        self.assertFalse(checker.compare_versions("20.9.0", "20.10.0"))

        # Test string comparison fallback
        self.assertTrue(checker.compare_versions("same", "same"))
        self.assertFalse(checker.compare_versions("different", "same"))

    def test_conflict_service_integration(self):
        """Test ConflictService integration with YAML config"""
        config_data = {"deps": {"docker": {"version": "20.10.0"}, "go": {"version": "1.18.0"}, "python": {"version": "3.9.0"}}}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = ConflictConfig(config_file=temp_path, environment="production", timeout=1, verbose=False, output="text")

            service = ConflictService(config, self.logger)

            # This would normally make real system calls
            # In a real test, we'd mock all the checkers
            with patch.object(service.checker, "check_conflicts") as mock_check:
                mock_check.return_value = [
                    ConflictCheckResult(
                        tool="docker", expected="20.10.0", current="20.10.5", status="compatible", conflict=False
                    )
                ]

                results = service.check_conflicts()
                self.assertEqual(len(results), 1)
                self.assertFalse(results[0].conflict)
        finally:
            os.unlink(temp_path)

    def test_version_requirement_parsing(self):
        """Test version requirement parsing for different formats"""
        checker = ToolVersionChecker(5, self.logger)

        # Test caret range parsing
        self.assertEqual(checker.parse_version_requirement("^1.20.0"), ">=1.20.0, <2.0.0")

        # Test tilde range parsing
        self.assertEqual(checker.parse_version_requirement("~1.20.0"), ">=1.20.0, <1.21.0")

        # Test comma-separated ranges
        self.assertEqual(checker.parse_version_requirement("1.20.0,2.0.0"), ">=1.20.0, <2.0.0")

        # Test wildcard ranges
        self.assertEqual(checker.parse_version_requirement("1.20.*"), ">=1.20.0, <1.21.0")

        # Test exact version
        self.assertEqual(checker.parse_version_requirement("1.20.0"), "1.20.0")

    def test_tool_mapping(self):
        """Test tool name mapping for system commands"""
        checker = ToolVersionChecker(5, self.logger)

        # Test that the mapping works correctly in _check_version_conflicts
        deps = {"open-ssh": {"version": "8.0.0"}, "open-sshserver": {"version": "8.0.0"}, "python3-venv": {"version": "3.9.0"}}

        conflict_checker = ConflictChecker(self.config, self.logger)

        # Mock the version checker to simulate tool responses
        with patch.object(conflict_checker.version_checker, "get_tool_version") as mock_get_version:
            mock_get_version.return_value = "8.1.0"

            results = conflict_checker._check_version_conflicts(deps)

            # Should have called with mapped tool names
            expected_calls = [call("ssh"), call("sshd"), call("python3")]

            # Check that the correct mapped commands were called
            actual_calls = [call[0][0] for call in mock_get_version.call_args_list]
            self.assertIn("ssh", actual_calls)
            self.assertIn("sshd", actual_calls)
            self.assertIn("python3", actual_calls)

    def test_empty_deps_handling(self):
        """Test handling of empty or missing deps section"""
        config_data = {}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = ConflictConfig(config_file=temp_path, environment="production", timeout=1, verbose=False, output="text")

            service = ConflictService(config, self.logger)
            results = service.check_conflicts()

            # Should return empty results for empty deps
            self.assertEqual(len(results), 0)
        finally:
            os.unlink(temp_path)

    def test_version_requirement_none_or_empty(self):
        """Test handling of tools with no version requirements"""
        config_data = {"deps": {"docker": {"version": ""}, "git": {"version": None}, "python": {}}}  # No version key

        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(config_data, f)
            temp_path = f.name

        try:
            config = ConflictConfig(config_file=temp_path, environment="production", timeout=1, verbose=False, output="text")

            checker = ConflictChecker(config, self.logger)

            # Mock version checker to return versions
            with patch.object(checker.version_checker, "get_tool_version") as mock_get_version:
                mock_get_version.return_value = "1.0.0"

                results = checker._check_version_conflicts(config_data["deps"])

                # Only docker and git should be checked (they have version keys)
                # python should not be checked (no version key)
                self.assertEqual(len(results), 2)

                # All should be compatible (no version requirement)
                for result in results:
                    self.assertFalse(result.conflict)
                    self.assertEqual(result.expected, "present")
        finally:
            os.unlink(temp_path)

    def test_conflict_formatter_output(self):
        """Test ConflictFormatter output formatting"""
        from app.commands.conflict.conflict import ConflictFormatter

        formatter = ConflictFormatter()

        results = [
            ConflictCheckResult(tool="docker", expected="20.10.0", current="20.10.5", status="compatible", conflict=False),
            ConflictCheckResult(tool="python", expected="3.9.0", current="3.8.0", status="conflict", conflict=True),
        ]

        output = formatter.format_output(results, "text")

        # Should contain both tools
        self.assertIn("docker", output)
        self.assertIn("python", output)

        # Should indicate status
        self.assertIn("compatible", output)

    def test_conflict_formatter_json_output(self):
        """Test ConflictFormatter JSON output formatting"""
        from app.commands.conflict.conflict import ConflictFormatter

        formatter = ConflictFormatter()

        results = [
            ConflictCheckResult(tool="docker", expected="20.10.0", current="20.10.5", status="compatible", conflict=False)
        ]

        output = formatter.format_output(results, "json")

        # Should be valid JSON structure
        self.assertIn("docker", output)
        self.assertIn("compatible", output)
        self.assertIn("20.10.5", output)


if __name__ == "__main__":
    unittest.main()
