import pytest
from unittest.mock import patch, MagicMock
from importlib.metadata import version
from core.version import display_version


class TestDisplayVersion:
    """Test cases for the display_version function"""

    @patch('core.version.console')
    @patch('core.version.version')
    def test_display_version_success(self, mock_version, mock_console):
        """Test successful version display"""
        mock_version.return_value = "1.0.0"
        
        display_version()
        
        mock_version.assert_called_once_with('nixopus')
        mock_console.print.assert_called_once()
        
        call_args = mock_console.print.call_args[0][0]
        assert call_args.title == "[bold white]Version Info[/bold white]"
        assert call_args.border_style == "blue"
        assert call_args.padding == (0, 1)

    @patch('core.version.console')
    @patch('core.version.version')
    def test_display_version_with_different_versions(self, mock_version, mock_console):
        """Test version display with different version numbers"""
        test_versions = ["0.1.0", "2.3.4", "1.0.0-beta"]
        
        for test_version in test_versions:
            mock_version.return_value = test_version
            mock_console.reset_mock()
            
            display_version()
            
            mock_version.assert_called_with('nixopus')
            mock_console.print.assert_called_once()

    @patch('core.version.console')
    @patch('core.version.version')
    def test_display_version_panel_content(self, mock_version, mock_console):
        """Test that panel contains correct text content"""
        mock_version.return_value = "1.2.3"
        
        display_version()
        
        call_args = mock_console.print.call_args[0][0]
        panel_content = call_args.renderable
        
        assert "NixOpus CLI" in str(panel_content)
        assert "v1.2.3" in str(panel_content)

    @patch('core.version.console')
    @patch('core.version.version')
    def test_display_version_handles_version_error(self, mock_version, mock_console):
        """Test handling of version import error"""
        mock_version.side_effect = Exception("Version not found")
        
        with pytest.raises(Exception):
            display_version()
        
        mock_version.assert_called_once_with('nixopus')

    @patch('core.version.console')
    @patch('core.version.version')
    def test_display_version_console_error_handling(self, mock_version, mock_console):
        """Test handling of console print errors"""
        mock_version.return_value = "1.0.0"
        mock_console.print.side_effect = Exception("Console error")
        
        with pytest.raises(Exception):
            display_version()
        
        mock_version.assert_called_once_with('nixopus')
        mock_console.print.assert_called_once()


class TestVersionModuleImports:
    """Test cases for module imports and dependencies"""

    def test_import_metadata_version(self):
        """Test that importlib.metadata.version is available"""
        try:
            from importlib.metadata import version
            assert callable(version)
        except ImportError:
            pytest.skip("importlib.metadata not available")

    def test_rich_console_import(self):
        """Test that rich.console.Console is available"""
        try:
            from rich.console import Console
            assert callable(Console)
        except ImportError:
            pytest.skip("rich.console not available")

    def test_rich_panel_import(self):
        """Test that rich.panel.Panel is available"""
        try:
            from rich.panel import Panel
            assert callable(Panel)
        except ImportError:
            pytest.skip("rich.panel not available")

    def test_rich_text_import(self):
        """Test that rich.text.Text is available"""
        try:
            from rich.text import Text
            assert callable(Text)
        except ImportError:
            pytest.skip("rich.text not available")


class TestVersionFunctionSignature:
    """Test cases for function signature and behavior"""

    def test_display_version_is_callable(self):
        """Test that display_version is a callable function"""
        assert callable(display_version)

    def test_display_version_no_parameters(self):
        """Test that display_version takes no parameters"""
        import inspect
        sig = inspect.signature(display_version)
        assert len(sig.parameters) == 0

    def test_display_version_returns_none(self):
        """Test that display_version returns None"""
        with patch('core.version.console'):
            with patch('core.version.version', return_value="1.0.0"):
                result = display_version()
                assert result is None
