"""Tests for the generate_profiles module."""

import json
import logging
from argparse import Namespace
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from resume_composer.generate_profiles import (
    read_profiles_file,
    generate_resume,
    main,
)


class TestReadProfilesFile:
    """Test cases for the read_profiles_file function."""

    def test_read_valid_profiles_file(self, tmp_path: Path) -> None:
        """Test reading a valid profiles file."""
        profiles_content = """USA,UK,Germany
data_scientist,finance
researcher,academic
engineer,general"""
        
        profiles_file = tmp_path / "profiles.txt"
        profiles_file.write_text(profiles_content)
        
        countries, profiles = read_profiles_file(str(profiles_file))
        
        assert countries == ["USA", "UK", "Germany"]
        assert profiles == [
            ["data_scientist", "finance"],
            ["researcher", "academic"],
            ["engineer", "general"]
        ]

    def test_read_profiles_file_with_empty_lines(self, tmp_path: Path) -> None:
        """Test reading profiles file with empty lines."""
        profiles_content = """USA,UK,Germany

data_scientist,finance

researcher,academic

engineer,general
"""
        
        profiles_file = tmp_path / "profiles.txt"
        profiles_file.write_text(profiles_content)
        
        countries, profiles = read_profiles_file(str(profiles_file))
        
        assert countries == ["USA", "UK", "Germany"]
        assert profiles == [
            ["data_scientist", "finance"],
            ["researcher", "academic"],
            ["engineer", "general"]
        ]

    def test_read_profiles_file_with_spaces(self, tmp_path: Path) -> None:
        """Test reading profiles file with extra spaces."""
        profiles_content = """ USA , UK , Germany 
 data_scientist , finance 
 researcher , academic """
        
        profiles_file = tmp_path / "profiles.txt"
        profiles_file.write_text(profiles_content)
        
        countries, profiles = read_profiles_file(str(profiles_file))
        
        assert countries == ["USA", "UK", "Germany"]
        assert profiles == [
            ["data_scientist", "finance"],
            ["researcher", "academic"]
        ]

    def test_read_nonexistent_profiles_file(self) -> None:
        """Test reading nonexistent profiles file."""
        with pytest.raises(SystemExit):
            read_profiles_file("nonexistent.txt")

    def test_read_invalid_encoding_file(self, tmp_path: Path) -> None:
        """Test reading file with invalid encoding."""
        profiles_file = tmp_path / "profiles.txt"
        profiles_file.write_bytes(b"\xff\xfe")  # Invalid UTF-8
        
        with pytest.raises(SystemExit):
            read_profiles_file(str(profiles_file))

    def test_read_empty_profiles_file(self, tmp_path: Path) -> None:
        """Test reading empty profiles file."""
        profiles_file = tmp_path / "profiles.txt"
        profiles_file.write_text("")
        
        with pytest.raises(SystemExit):
            read_profiles_file(str(profiles_file))

    def test_read_profiles_file_no_countries(self, tmp_path: Path) -> None:
        """Test reading profiles file with no countries."""
        profiles_content = "\ndata_scientist,finance"
        
        profiles_file = tmp_path / "profiles.txt"
        profiles_file.write_text(profiles_content)
        
        with pytest.raises(SystemExit):
            read_profiles_file(str(profiles_file))

    def test_read_profiles_file_no_profiles(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Test reading profiles file with no profile lines."""
        profiles_content = "USA,UK,Germany"
        
        profiles_file = tmp_path / "profiles.txt"
        profiles_file.write_text(profiles_content)
        
        with pytest.raises(SystemExit):
            read_profiles_file(str(profiles_file))

    def test_read_profiles_file_empty_profile_line(self, tmp_path: Path, capsys: pytest.CaptureFixture[str]) -> None:
        """Test reading profiles file with empty profile line."""
        profiles_content = """USA,UK,Germany
data_scientist,finance

researcher,academic"""
        
        profiles_file = tmp_path / "profiles.txt"
        profiles_file.write_text(profiles_content)
        
        countries, profiles = read_profiles_file(str(profiles_file))
        
        assert countries == ["USA", "UK", "Germany"]
        assert profiles == [
            ["data_scientist", "finance"],
            ["researcher", "academic"]
        ]
        
        captured = capsys.readouterr()
        assert "Warning: Empty profile on line" in captured.out


class TestGenerateResume:
    """Test cases for the generate_resume function."""

    @patch("resume_composer.generate_profiles.process_resume_substitution")
    def test_generate_resume_success(self, mock_process: Mock, caplog: pytest.LogCaptureFixture) -> None:
        """Test successful resume generation."""
        caplog.set_level(logging.INFO)
        
        generate_resume(
            "USA", ["data_scientist", "finance"], "config.json", "input.tex", compile_pdf=False
        )
        
        mock_process.assert_called_once()
        args = mock_process.call_args[0][0]
        
        assert args.tags == "data_scientist,finance"
        assert args.country == "USA"
        assert args.config == "config.json"
        assert args.input == "input.tex"
        assert args.compile is False
        
        assert "Generating resume for USA with tags: data_scientist, finance" in caplog.text

    @patch("resume_composer.generate_profiles.process_resume_substitution")
    def test_generate_resume_with_compilation(self, mock_process: Mock) -> None:
        """Test resume generation with PDF compilation."""
        generate_resume("UK", ["researcher"], "config.json", "input.tex", compile_pdf=True)
        
        mock_process.assert_called_once()
        args = mock_process.call_args[0][0]
        
        assert args.compile is True

    @patch("resume_composer.generate_profiles.process_resume_substitution")
    def test_generate_resume_failure(self, mock_process: Mock, caplog: pytest.LogCaptureFixture) -> None:
        """Test resume generation failure."""
        caplog.set_level(logging.INFO)
        mock_process.side_effect = Exception("Test error")

        generate_resume("USA", ["data_scientist"], "config.json", "input.tex", compile_pdf=False)
        assert "✗ Error" in caplog.text


class TestMainFunction:
    """Test cases for the main function."""

    @patch("resume_composer.generate_profiles.read_profiles_file")
    @patch("resume_composer.generate_profiles.generate_resume")
    @patch("sys.argv", ["generate_profiles.py", "--profiles", "test.txt"])
    def test_main_basic_execution(self, mock_generate: Mock, mock_read: Mock) -> None:
        """Test basic main function execution."""
        mock_read.return_value = (["USA", "UK"], [["data_scientist"], ["researcher"]])
        
        with patch("pathlib.Path.exists", return_value=True):
            main()
        
        mock_read.assert_called_once_with("test.txt")
        assert mock_generate.call_count == 4  # 2 countries × 2 profiles

    @patch("resume_composer.generate_profiles.read_profiles_file")
    @patch("sys.argv", ["generate_profiles.py", "--profiles", "test.txt", "--dry-run"])
    def test_main_dry_run(self, mock_read: Mock, capsys: pytest.CaptureFixture[str]) -> None:
        """Test main function with dry-run option."""
        mock_read.return_value = (["USA", "UK"], [["data_scientist"], ["researcher"]])
        
        main()
        
        captured = capsys.readouterr()
        assert "Dry run - showing combinations that would be generated:" in captured.out
        assert "USA: data_scientist" in captured.out
        assert "UK: researcher" in captured.out

    @patch("resume_composer.generate_profiles.read_profiles_file")
    @patch("sys.argv", ["generate_profiles.py", "--profiles", "test.txt"])
    def test_main_missing_config_file(self, mock_read: Mock) -> None:
        """Test main function with missing config file."""
        mock_read.return_value = (["USA"], [["data_scientist"]])
        
        with patch("pathlib.Path.exists", return_value=False):  # config file doesn't exist
            
            with pytest.raises(SystemExit):
                main()

    @patch("resume_composer.generate_profiles.read_profiles_file")
    @patch("sys.argv", ["generate_profiles.py", "--profiles", "test.txt"])
    def test_main_missing_input_file(self, mock_read: Mock) -> None:
        """Test main function with missing input file."""
        mock_read.return_value = (["USA"], [["data_scientist"]])
        
        def side_effect_func(self):
            return str(self).endswith("config.json")
        with patch.object(Path, "exists", side_effect_func):
            
            with pytest.raises(SystemExit):
                main()

    @patch("resume_composer.generate_profiles.read_profiles_file")
    @patch("resume_composer.generate_profiles.generate_resume")
    @patch("sys.argv", ["generate_profiles.py", "--profiles", "test.txt", "--compile"])
    def test_main_with_compilation(self, mock_generate: Mock, mock_read: Mock) -> None:
        """Test main function with PDF compilation enabled."""
        mock_read.return_value = (["USA"], [["data_scientist"]])
        
        with patch("pathlib.Path.exists", return_value=True):
            main()
        
        mock_generate.assert_called_once()
        call_args, call_kwargs = mock_generate.call_args
        assert call_kwargs["compile_pdf"] is True

    @patch("resume_composer.generate_profiles.read_profiles_file")
    @patch("sys.argv", ["generate_profiles.py", "--profiles", "test.txt", "--config", "custom.json", "--input", "custom.tex"])
    def test_main_custom_files(self, mock_read: Mock, capsys: pytest.CaptureFixture[str]) -> None:
        """Test main function with custom config and input files."""
        mock_read.return_value = (["USA"], [["data_scientist"]])
        
        with patch("pathlib.Path.exists", return_value=True):
            with patch("resume_composer.generate_profiles.generate_resume"):
                main()
        
        mock_read.assert_called_once_with("test.txt")

    @patch("resume_composer.generate_profiles.read_profiles_file")
    @patch("resume_composer.generate_profiles.generate_resume")
    @patch("sys.argv", ["generate_profiles.py"])
    def test_main_default_arguments(self, mock_generate: Mock, mock_read: Mock) -> None:
        """Test main function with default arguments."""
        mock_read.return_value = (["USA"], [["data_scientist"]])
        
        with patch("pathlib.Path.exists", return_value=True):
            main()
        
        mock_read.assert_called_once_with("profiles.txt")


class TestIntegration:
    """Integration tests using sample data files."""

    def test_integration_with_sample_data(self, tmp_path: Path) -> None:
        """Test integration using actual sample data files."""
        # Copy sample files to temp directory for testing
        import shutil
        from pathlib import Path as PathlibPath
        
        project_root = PathlibPath(__file__).parent.parent.parent
        data_dir = project_root / "data"
        
        if data_dir.exists():
            # Copy sample files
            sample_config = data_dir / "sample_config.json"
            sample_template = data_dir / "sample_resume_template.tex"
            sample_profiles = data_dir / "sample_profiles.txt"
            
            if sample_config.exists():
                shutil.copy(sample_config, tmp_path / "config.json")
            if sample_template.exists():
                shutil.copy(sample_template, tmp_path / "template.tex")
            if sample_profiles.exists():
                shutil.copy(sample_profiles, tmp_path / "profiles.txt")
                
                # Test reading the sample profiles file
                countries, profiles = read_profiles_file(str(tmp_path / "profiles.txt"))
                
                assert len(countries) > 0
                assert len(profiles) > 0
                assert "USA" in countries or "UK" in countries

    def test_end_to_end_workflow(self, tmp_path: Path) -> None:
        """Test complete end-to-end workflow."""
        # Create test files
        config_data = {
            "1": {"default": "John Doe", "usa": "John Doe USA"},
            "title": {"default": "Engineer", "data_scientist": "Data Scientist"}
        }
        
        config_file = tmp_path / "config.json"
        config_file.write_text(json.dumps(config_data))
        
        template_content = "Name: <1>, Title: <title>"
        template_file = tmp_path / "template.tex"
        template_file.write_text(template_content)
        
        profiles_content = "USA,UK\ndata_scientist,tech"
        profiles_file = tmp_path / "profiles.txt"
        profiles_file.write_text(profiles_content)
        
        # Test the workflow
        countries, profiles = read_profiles_file(str(profiles_file))
        assert countries == ["USA", "UK"]
        assert profiles == [["data_scientist", "tech"]]
        
        # Test generating one resume
        args = Namespace(
            tags="data_scientist",
            country="USA",
            config=str(config_file),
            input=str(template_file),
            compile=False,
            output=None,
            list_tags=False,
            use_folders=False,
            no_folders=True
        )
        
        from resume_composer.substitute_resume import process_resume_substitution
        
        # Change to tmp_path for output
        import os
        original_cwd = os.getcwd()
        os.chdir(tmp_path)
        
        try:
            process_resume_substitution(args)
            
            # Check if output file was created
            output_file = tmp_path / "template_usa_data_scientist.tex"
            assert output_file.exists()
            
            result = output_file.read_text()
            assert "John Doe USA" in result
            assert "Data Scientist" in result
        finally:
            os.chdir(original_cwd)