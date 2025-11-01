"""Additional tests for edge cases and error handling."""

import json
import subprocess
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from resume_composer.substitute_resume import ResumeSubstituter
from tests.test_helpers import create_test_config, create_test_template


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_config_with_missing_default_values(self, tmp_path: Path) -> None:
        """Test configuration with some placeholders missing default values."""
        config_data = {
            "1": {"academic": "Dr. John"},  # No default
            "2": {"default": "Engineer", "academic": "Professor"}
        }
        config_file = create_test_config(tmp_path, config_data)
        
        substituter = ResumeSubstituter(str(config_file))
        
        # Should return placeholder unchanged when no default and no matching tag
        assert substituter._get_value_for_placeholder("1", ["nonexistent"]) == "<1>"
        # Should work with matching tag
        assert substituter._get_value_for_placeholder("1", ["academic"]) == "Dr. John"

    def test_template_with_malformed_placeholders(self, tmp_path: Path) -> None:
        """Test template with various malformed placeholders."""
        template_content = """
        Valid: <1>, <name>
        Invalid: <>, <123abc>, <-invalid>, <spa ce>
        Nested: <<1>>, <1<2>>
        """
        template_file = create_test_template(tmp_path, template_content)
        config_file = create_test_config(tmp_path, {
            "1": {"default": "John"},
            "name": {"default": "Smith"}
        })
        
        substituter = ResumeSubstituter(str(config_file))
        output_file = tmp_path / "output.tex"
        
        substituter.substitute_file(str(template_file), str(output_file), [])
        
        result = output_file.read_text()
        # Valid placeholders should be replaced
        assert "Valid: John, Smith" in result
        # Invalid placeholders should remain unchanged
        assert "<>" in result
        assert "<123abc>" in result

    def test_unicode_content_handling(self, tmp_path: Path) -> None:
        """Test handling of Unicode content in templates and config."""
        config_data = {
            "name": {"default": "José García", "spanish": "José García Pérez"},
            "title": {"default": "Ingénieur", "french": "Ingénieur Logiciel"}
        }
        config_file = create_test_config(tmp_path, config_data)
        
        template_content = "Nom: <name>, Titre: <title> 🚀"
        template_file = create_test_template(tmp_path, template_content)
        
        substituter = ResumeSubstituter(str(config_file))
        output_file = tmp_path / "output.tex"
        
        substituter.substitute_file(str(template_file), str(output_file), ["spanish", "french"])
        
        result = output_file.read_text()
        assert "José García Pérez" in result
        assert "Ingénieur Logiciel" in result
        assert "🚀" in result

    def test_large_template_performance(self, tmp_path: Path) -> None:
        """Test performance with large template files."""
        # Create a large template with many placeholders
        template_content = ""
        for i in range(1000):
            template_content += f"Line {i}: <name> is <title_{i}>\n"
        
        template_file = create_test_template(tmp_path, template_content)
        
        # Create config with many placeholders
        config_data = {"name": {"default": "John"}}
        for i in range(1000):
            config_data[f"title_{i}"] = {"default": f"Title {i}"}
        
        config_file = create_test_config(tmp_path, config_data)
        
        substituter = ResumeSubstituter(str(config_file))
        output_file = tmp_path / "output.tex"
        
        # This should complete without timing out or excessive memory usage
        substituter.substitute_file(str(template_file), str(output_file), [])
        
        result = output_file.read_text()
        assert "John is Title 0" in result
        assert "John is Title 999" in result

    def test_empty_tags_list(self, tmp_path: Path) -> None:
        """Test behavior with empty tags list."""
        config_file = create_test_config(tmp_path)
        template_file = create_test_template(tmp_path)
        
        substituter = ResumeSubstituter(str(config_file))
        output_file = tmp_path / "output.tex"
        
        substituter.substitute_file(str(template_file), str(output_file), [])
        
        result = output_file.read_text()
        assert "Hello John Doe, you are a Engineer." == result

    def test_duplicate_placeholders(self, tmp_path: Path) -> None:
        """Test template with duplicate placeholders."""
        template_content = "<1> and <1> and <1> again"
        template_file = create_test_template(tmp_path, template_content)
        config_file = create_test_config(tmp_path, {"1": {"default": "John"}})
        
        substituter = ResumeSubstituter(str(config_file))
        output_file = tmp_path / "output.tex"
        
        substituter.substitute_file(str(template_file), str(output_file), [])
        
        result = output_file.read_text()
        assert result == "John and John and John again"

    def test_case_sensitive_tags(self, tmp_path: Path) -> None:
        """Test that tags are case-sensitive."""
        config_data = {
            "1": {"default": "Default", "Academic": "Academic", "academic": "academic"}
        }
        config_file = create_test_config(tmp_path, config_data)
        
        substituter = ResumeSubstituter(str(config_file))
        
        assert substituter._get_value_for_placeholder("1", ["Academic"]) == "Academic"
        assert substituter._get_value_for_placeholder("1", ["academic"]) == "academic"
        assert substituter._get_value_for_placeholder("1", ["ACADEMIC"]) == "Default"

    def test_numeric_vs_string_placeholders(self, tmp_path: Path) -> None:
        """Test mixing numeric and string placeholder IDs."""
        config_data = {
            "1": {"default": "Numeric One"},
            "name": {"default": "String Name"},
            "2name": {"default": "Mixed ID"}
        }
        config_file = create_test_config(tmp_path, config_data)
        
        template_content = "<1> <name> <2name>"
        template_file = create_test_template(tmp_path, template_content)
        
        substituter = ResumeSubstituter(str(config_file))
        output_file = tmp_path / "output.tex"
        
        substituter.substitute_file(str(template_file), str(output_file), [])
        
        result = output_file.read_text()
        assert result == "Numeric One String Name Mixed ID"


class TestErrorRecovery:
    """Test error recovery and graceful degradation."""

    def test_partial_config_corruption(self, tmp_path: Path) -> None:
        """Test behavior when part of config is corrupted."""
        # Create a config where one placeholder has invalid structure
        config_file = tmp_path / "config.json"
        config_content = """
        {
            "1": {"default": "John"},
            "2": "Invalid Structure",
            "3": {"default": "Valid"}
        }
        """
        config_file.write_text(config_content)
        
        substituter = ResumeSubstituter(str(config_file))
        
        # Should handle valid placeholders normally
        assert substituter._get_value_for_placeholder("1", []) == "John"
        assert substituter._get_value_for_placeholder("3", []) == "Valid"
        
        # Should handle invalid placeholder gracefully
        result = substituter._get_value_for_placeholder("2", [])
        assert result == "<2>"  # Should return placeholder unchanged

    def test_filesystem_permission_errors(self, tmp_path: Path) -> None:
        """Test handling of filesystem permission errors."""
        config_file = create_test_config(tmp_path)
        template_file = create_test_template(tmp_path)
        
        # Try to write to a read-only directory (simulate permission error)
        readonly_dir = tmp_path / "readonly"
        readonly_dir.mkdir()
        readonly_dir.chmod(0o444)  # Read-only
        
        output_file = readonly_dir / "output.tex"
        
        substituter = ResumeSubstituter(str(config_file))
        
        try:
            with pytest.raises(SystemExit):
                substituter.substitute_file(str(template_file), str(output_file), [])
        finally:
            # Clean up - restore permissions
            readonly_dir.chmod(0o755)

    @patch("builtins.open")
    def test_file_encoding_errors(self, mock_open: Mock, tmp_path: Path) -> None:
        """Test handling of file encoding errors."""
        config_file = create_test_config(tmp_path)
        
        mock_open.side_effect = UnicodeDecodeError("utf-8", b"", 0, 1, "invalid start byte")
        
        substituter = ResumeSubstituter(str(config_file))
        
        with pytest.raises(SystemExit):
            substituter.substitute_file("input.tex", "output.tex", [])


class TestCompilationEdgeCases:
    """Test LaTeX compilation edge cases."""

    @patch("resume_composer.substitute_resume.subprocess.run")
    def test_compilation_with_auxiliary_files(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test that auxiliary files are properly cleaned up."""
        from resume_composer.substitute_resume import compile_latex_to_pdf
        
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        # Create auxiliary files that should be cleaned up
        aux_files = [
            tmp_path / "test.aux",
            tmp_path / "test.log", 
            tmp_path / "test.out",
            tmp_path / "test.fls"
        ]
        
        for aux_file in aux_files:
            aux_file.write_text("auxiliary content")
        
        # Create PDF file to simulate successful compilation
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf")
        
        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result
        
        compile_latex_to_pdf(str(tex_file))
        
        # Check that auxiliary files were cleaned up
        for aux_file in aux_files:
            if aux_file.suffix in [".aux", ".log", ".out", ".fls"]:
                assert not aux_file.exists(), f"{aux_file} should have been cleaned up"

    @patch("resume_composer.substitute_resume.subprocess.run")
    def test_compilation_partial_failure(self, mock_run: Mock, tmp_path: Path) -> None:
        """Test compilation that fails but creates some output."""
        from resume_composer.substitute_resume import compile_latex_to_pdf
        
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        mock_result = Mock()
        mock_result.returncode = 1  # Failure
        mock_result.stderr = "LaTeX Warning: Something went wrong"
        mock_run.return_value = mock_result
        
        # Even though compilation "failed", PDF might still exist
        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("partial pdf output")
        
        compile_latex_to_pdf(str(tex_file))
        
        mock_run.assert_called_once()

    def test_compilation_with_spaces_in_filename(self, tmp_path: Path) -> None:
        """Test compilation with spaces in filename."""
        from resume_composer.substitute_resume import compile_latex_to_pdf
        
        # Create file with spaces in name
        tex_file = tmp_path / "test file with spaces.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")
        
        with patch("resume_composer.substitute_resume.subprocess.run") as mock_run:
            mock_result = Mock()
            mock_result.returncode = 0
            mock_run.return_value = mock_result
            
            # Create corresponding PDF
            pdf_file = tmp_path / "test file with spaces.pdf" 
            pdf_file.write_text("pdf content")
            
            compile_latex_to_pdf(str(tex_file))
            
            # Verify the command was called with the correct filename
            mock_run.assert_called_once()
            args = mock_run.call_args[0][0]
            assert "test file with spaces.tex" in args


class TestConfigurationValidation:
    """Test configuration file validation and edge cases."""

    def test_config_with_nested_objects(self, tmp_path: Path) -> None:
        """Test config with deeply nested objects."""
        config_data = {
            "1": {
                "default": "John",
                "nested": {"invalid": "structure"}  # This shouldn't crash
            }
        }
        config_file = create_test_config(tmp_path, config_data)
        
        substituter = ResumeSubstituter(str(config_file))
        # Should handle gracefully, likely falling back to placeholder
        result = substituter._get_value_for_placeholder("1", ["nested"])
        # Exact behavior may vary, but shouldn't crash
        assert isinstance(result, str)

    def test_config_with_null_values(self, tmp_path: Path) -> None:
        """Test config with null/None values."""
        config_file = tmp_path / "config.json"
        config_content = """
        {
            "1": {"default": null, "valid": "John"},
            "2": null
        }
        """
        config_file.write_text(config_content)
        
        substituter = ResumeSubstituter(str(config_file))
        
        # Should handle null values gracefully
        result1 = substituter._get_value_for_placeholder("1", ["valid"])
        assert result1 == "John"
        
        result2 = substituter._get_value_for_placeholder("2", [])
        assert result2 == "<2>"  # Should fallback to placeholder

    def test_config_with_empty_strings(self, tmp_path: Path) -> None:
        """Test config with empty string values."""
        config_data = {
            "1": {"default": "", "nonempty": "John"},
            "2": {"default": "Valid", "empty": ""}
        }
        config_file = create_test_config(tmp_path, config_data)
        
        substituter = ResumeSubstituter(str(config_file))
        
        assert substituter._get_value_for_placeholder("1", []) == ""
        assert substituter._get_value_for_placeholder("1", ["nonempty"]) == "John"
        assert substituter._get_value_for_placeholder("2", ["empty"]) == ""