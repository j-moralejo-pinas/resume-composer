"""Tests for the substitute_resume module."""

import json
import logging
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch
from argparse import Namespace

import pytest

from resume_composer.substitute_resume import (
    ResumeSubstituter,
    process_resume_substitution,
    compile_latex_to_pdf,
    main,
)


class TestResumeSubstituter:
    """Test cases for the ResumeSubstituter class."""

    def test_init_with_valid_config(self, tmp_path: Path) -> None:
        """Test initialization with a valid config file."""
        config_data = {
            "1": {"default": "John Doe", "academic": "Dr. John Doe"},
            "2": {"default": "Engineer", "data_scientist": "Data Scientist"},
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        substituter = ResumeSubstituter(str(config_file))

        assert substituter.config == config_data
        assert substituter.config_file == str(config_file)

    def test_init_with_nonexistent_config(self) -> None:
        """Test initialization with nonexistent config file."""
        with pytest.raises(SystemExit):
            ResumeSubstituter("nonexistent.json")

    def test_init_with_invalid_json(self, tmp_path: Path) -> None:
        """Test initialization with invalid JSON config."""
        config_file = tmp_path / "invalid.json"
        config_file.write_text("invalid json content")

        with pytest.raises(SystemExit):
            ResumeSubstituter(str(config_file))

    def test_get_value_for_placeholder_with_matching_tag(self, tmp_path: Path) -> None:
        """Test getting value for placeholder with matching tag."""
        config_data = {
            "1": {"default": "John Doe", "academic": "Dr. John Doe"},
            "2": {"default": "Engineer"},
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        substituter = ResumeSubstituter(str(config_file))

        assert substituter._get_value_for_placeholder("1", ["academic"]) == "Dr. John Doe"
        assert (
            substituter._get_value_for_placeholder("1", ["nonexistent", "academic"])
            == "Dr. John Doe"
        )

    def test_get_value_for_placeholder_with_default(self, tmp_path: Path) -> None:
        """Test getting value for placeholder with default fallback."""
        config_data = {"1": {"default": "John Doe", "academic": "Dr. John Doe"}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        substituter = ResumeSubstituter(str(config_file))

        assert substituter._get_value_for_placeholder("1", ["nonexistent"]) == "John Doe"

    def test_get_value_for_placeholder_missing_config(self, tmp_path: Path) -> None:
        """Test getting value for placeholder with missing config."""
        config_data = {"1": {"default": "John Doe"}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        substituter = ResumeSubstituter(str(config_file))

        assert substituter._get_value_for_placeholder("2", ["academic"]) == "<2>"

    def test_get_value_for_placeholder_no_default(self, tmp_path: Path) -> None:
        """Test getting value for placeholder with no default value."""
        config_data = {"1": {"academic": "Dr. John Doe"}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        substituter = ResumeSubstituter(str(config_file))

        assert substituter._get_value_for_placeholder("1", ["nonexistent"]) == "<1>"

    def test_map_country_to_tag_direct_mappings(self, tmp_path: Path) -> None:
        """Test country to tag mapping for direct mappings."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))

        substituter = ResumeSubstituter(str(config_file))

        assert substituter.map_country_to_tag("UK") == "uk"
        assert substituter.map_country_to_tag("united kingdom") == "uk"
        assert substituter.map_country_to_tag("USA") == "usa"
        assert substituter.map_country_to_tag("united states") == "usa"
        assert substituter.map_country_to_tag("Switzerland") == "switzerland"
        assert substituter.map_country_to_tag("Spain") == "spain"

    def test_map_country_to_tag_european_countries(self, tmp_path: Path) -> None:
        """Test country to tag mapping for European countries."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))

        substituter = ResumeSubstituter(str(config_file))

        assert substituter.map_country_to_tag("Germany") == "europe"
        assert substituter.map_country_to_tag("france") == "europe"
        assert substituter.map_country_to_tag("Italy") == "europe"
        assert substituter.map_country_to_tag("netherlands") == "europe"

    def test_map_country_to_tag_default_fallback(self, tmp_path: Path) -> None:
        """Test country to tag mapping with default fallback."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))

        substituter = ResumeSubstituter(str(config_file))

        assert substituter.map_country_to_tag("Japan") == "default"
        assert substituter.map_country_to_tag("Brazil") == "default"

    def test_create_folder_structure_basic(self, tmp_path: Path) -> None:
        """Test folder structure creation with basic tags."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))

        substituter = ResumeSubstituter(str(config_file))

        # Change to tmp_path for folder creation
        import os

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = substituter.create_folder_structure(
                ["usa", "data_scientist"], "resume.tex", "USA"
            )

            assert "USA/_base/Position/resume.tex" in result
            assert Path(result).parent.exists()
        finally:
            os.chdir(original_cwd)

    def test_create_folder_structure_with_other_tags(self, tmp_path: Path) -> None:
        """Test folder structure creation with additional tags."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))

        substituter = ResumeSubstituter(str(config_file))

        import os

        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            result = substituter.create_folder_structure(
                ["usa", "data_scientist", "finance"], "resume.tex", "USA"
            )

            assert "USA/_base_finance/Position/resume.tex" in result
            assert Path(result).parent.exists()
        finally:
            os.chdir(original_cwd)

    def test_substitute_file_successful(self, tmp_path: Path) -> None:
        """Test successful file substitution."""
        config_data = {"1": {"default": "John Doe"}, "name": {"default": "Jane Smith"}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        input_file = tmp_path / "input.tex"
        input_file.write_text("Hello <1>, my name is <name>.")

        output_file = tmp_path / "output.tex"

        substituter = ResumeSubstituter(str(config_file))
        substituter.substitute_file(str(input_file), str(output_file), [])

        result = output_file.read_text()
        assert result == "Hello John Doe, my name is Jane Smith."

    def test_substitute_file_with_tags(self, tmp_path: Path) -> None:
        """Test file substitution with specific tags."""
        config_data = {
            "1": {"default": "John Doe", "academic": "Dr. John Doe"},
            "title": {"default": "Engineer", "academic": "Professor"},
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        input_file = tmp_path / "input.tex"
        input_file.write_text("Name: <1>, Title: <title>")

        output_file = tmp_path / "output.tex"

        substituter = ResumeSubstituter(str(config_file))
        substituter.substitute_file(str(input_file), str(output_file), ["academic"])

        result = output_file.read_text()
        assert result == "Name: Dr. John Doe, Title: Professor"

    def test_substitute_file_nonexistent_input(self, tmp_path: Path) -> None:
        """Test substitution with nonexistent input file."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))

        substituter = ResumeSubstituter(str(config_file))

        with pytest.raises(SystemExit):
            substituter.substitute_file("nonexistent.tex", "output.tex", [])

    def test_substitute_file_no_placeholders(self, tmp_path: Path) -> None:
        """Test substitution with file containing no placeholders."""
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps({}))

        input_file = tmp_path / "input.tex"
        input_file.write_text("No placeholders here.")

        output_file = tmp_path / "output.tex"

        substituter = ResumeSubstituter(str(config_file))
        substituter.substitute_file(str(input_file), str(output_file), [])

        result = output_file.read_text()
        assert result == "No placeholders here."

    def test_substitute_file_write_error(self, tmp_path: Path) -> None:
        """Test substitution with write error."""
        config_data = {"1": {"default": "John Doe"}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        input_file = tmp_path / "input.tex"
        input_file.write_text("Hello <1>")

        # Create a directory with the output filename to cause write error
        output_file = tmp_path / "output.tex"
        output_file.mkdir()

        substituter = ResumeSubstituter(str(config_file))

        with pytest.raises(SystemExit):
            substituter.substitute_file(str(input_file), str(output_file), [])

    def test_list_available_tags(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """Test listing available tags."""
        caplog.set_level(logging.INFO)
        config_data = {
            "1": {"default": "John", "academic": "Dr. John", "professional": "John Doe"},
            "2": {"default": "Engineer", "data_scientist": "Data Scientist"}
        }
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        substituter = ResumeSubstituter(str(config_file))
        substituter.list_available_tags()

        assert "Available tags:" in caplog.text
        assert "academic" in caplog.text
        assert "professional" in caplog.text
        assert "data_scientist" in caplog.text

    def test_list_available_tags_empty(
        self, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test listing tags when no tags are available."""
        caplog.set_level(logging.INFO)
        config_data = {"1": {"default": "John"}, "2": {"default": "Engineer"}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        substituter = ResumeSubstituter(str(config_file))
        substituter.list_available_tags()

        assert "No tags found in configuration." in caplog.text


class TestProcessResumeSubstitution:
    """Test cases for the process_resume_substitution function."""

    def test_list_tags_mode(self, tmp_path: Path, caplog: pytest.LogCaptureFixture) -> None:
        """Test process function in list-tags mode."""
        caplog.set_level(logging.INFO)
        config_data = {"1": {"default": "John", "academic": "Dr. John"}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        args = Namespace(
            config=str(config_file),
            list_tags=True,
            tags=None,
            country=None,
            use_folders=True,
            no_folders=False,
            input="resume.tex",
            output=None,
            compile=False,
        )

        process_resume_substitution(args)

        assert "Available tags:" in caplog.text

    def test_substitution_with_tags(self, tmp_path: Path) -> None:
        """Test process function with tag substitution."""
        config_data = {"1": {"default": "John", "academic": "Dr. John"}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        input_file = tmp_path / "input.tex"
        input_file.write_text("Hello <1>")

        args = Namespace(
            config=str(config_file),
            list_tags=False,
            tags="academic",
            country=None,
            use_folders=False,
            no_folders=True,
            input=str(input_file),
            output=None,
            compile=False,
        )

        process_resume_substitution(args)

        output_file = tmp_path / "input_academic.tex"
        assert output_file.exists()
        result = output_file.read_text()
        assert result == "Hello Dr. John"

    def test_substitution_with_country(self, tmp_path: Path) -> None:
        """Test process function with country mapping."""
        config_data = {"1": {"default": "John", "uk": "John Smith UK"}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        input_file = tmp_path / "input.tex"
        input_file.write_text("Hello <1>")

        args = Namespace(
            config=str(config_file),
            list_tags=False,
            tags=None,
            country="UK",
            use_folders=False,
            no_folders=True,
            input=str(input_file),
            output=None,
            compile=False,
        )

        process_resume_substitution(args)

        output_file = tmp_path / "input_uk.tex"
        assert output_file.exists()
        result = output_file.read_text()
        assert result == "Hello John Smith UK"

    @patch("resume_composer.substitute_resume.compile_latex_to_pdf")
    def test_substitution_with_compile(self, mock_compile: Mock, tmp_path: Path) -> None:
        """Test process function with PDF compilation."""
        config_data = {"1": {"default": "John"}}
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))

        input_file = tmp_path / "input.tex"
        input_file.write_text("Hello <1>")

        args = Namespace(
            config=str(config_file),
            list_tags=False,
            tags=None,
            country=None,
            use_folders=False,
            no_folders=True,
            input=str(input_file),
            output=None,
            compile=True,
        )

        process_resume_substitution(args)

        output_file = tmp_path / "input_default.tex"
        assert output_file.exists()
        mock_compile.assert_called_once_with(str(output_file))


class TestCompileLatexToPdf:
    """Test cases for the compile_latex_to_pdf function."""

    def test_compile_nonexistent_file(self, caplog: pytest.LogCaptureFixture) -> None:
        """Test compilation of nonexistent file."""
        caplog.set_level(logging.ERROR)
        compile_latex_to_pdf("nonexistent.tex")

        assert "LaTeX file 'nonexistent.tex' not found." in caplog.text

    @patch("resume_composer.substitute_resume.subprocess.run")
    def test_compile_successful(
        self, mock_run: Mock, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test successful compilation."""
        caplog.set_level(logging.INFO)
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")

        pdf_file = tmp_path / "test.pdf"
        pdf_file.write_text("fake pdf content")

        mock_result = Mock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        compile_latex_to_pdf(str(tex_file))

        assert f"Compiling {tex_file} to PDF..." in caplog.text
        assert f"Successfully compiled to '{pdf_file}'" in caplog.text

    @patch("resume_composer.substitute_resume.subprocess.run")
    def test_compile_failure(
        self, mock_run: Mock, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test compilation failure."""
        caplog.set_level(logging.ERROR)
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")

        mock_result = Mock()
        mock_result.returncode = 1
        mock_result.stderr = "LaTeX Error: Something went wrong"
        mock_run.return_value = mock_result

        compile_latex_to_pdf(str(tex_file))

        assert "Compilation failed with return code 1" in caplog.text
        assert "Error output:" in caplog.text

    @patch("resume_composer.substitute_resume.subprocess.run")
    def test_compile_timeout(
        self, mock_run: Mock, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test compilation timeout."""
        caplog.set_level(logging.ERROR)
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")

        from subprocess import TimeoutExpired

        mock_run.side_effect = TimeoutExpired("pdflatex", 60)

        compile_latex_to_pdf(str(tex_file))

        assert "Compilation timed out after 60 seconds." in caplog.text

    @patch("resume_composer.substitute_resume.subprocess.run")
    def test_compile_pdflatex_not_found(
        self, mock_run: Mock, tmp_path: Path, caplog: pytest.LogCaptureFixture
    ) -> None:
        """Test compilation when pdflatex is not found."""
        caplog.set_level(logging.ERROR)
        tex_file = tmp_path / "test.tex"
        tex_file.write_text("\\documentclass{article}\\begin{document}Test\\end{document}")

        mock_run.side_effect = FileNotFoundError()

        compile_latex_to_pdf(str(tex_file))

        assert "pdflatex not found. Please install a LaTeX distribution." in caplog.text


class TestMainFunction:
    """Test cases for the main function."""

    @patch("resume_composer.substitute_resume.process_resume_substitution")
    @patch("sys.argv", ["substitute_resume.py", "--tags", "academic"])
    def test_main_function(self, mock_process: Mock) -> None:
        """Test main function argument parsing and processing."""
        main()

        mock_process.assert_called_once()
        args = mock_process.call_args[0][0]
        assert args.tags == "academic"

    @patch("resume_composer.substitute_resume.process_resume_substitution")
    @patch("sys.argv", ["substitute_resume.py", "--list-tags"])
    def test_main_function_list_tags(self, mock_process: Mock) -> None:
        """Test main function with list-tags option."""
        main()

        mock_process.assert_called_once()
        args = mock_process.call_args[0][0]
        assert args.list_tags is True
