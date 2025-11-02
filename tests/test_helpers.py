"""Test utilities and helpers for resume-composer tests."""

import json
import os
from pathlib import Path
from typing import Any


def create_test_config(tmp_path: Path, config_data: dict[str, Any] | None = None) -> Path:
    """Create a test configuration file."""
    if config_data is None:
        config_data = {
            "1": {"default": "John Doe", "academic": "Dr. John Doe"},
            "2": {"default": "Engineer", "data_scientist": "Data Scientist"},
        }

    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(config_data))
    return config_file


def create_test_template(tmp_path: Path, content: str | None = None) -> Path:
    """Create a test resume template file."""
    if content is None:
        content = "Hello <1>, you are a <2>."

    template_file = tmp_path / "template.tex"
    template_file.write_text(content)
    return template_file


def create_test_profiles(tmp_path: Path, content: str | None = None) -> Path:
    """Create a test profiles file."""
    if content is None:
        content = "USA,UK\ndata_scientist,finance\nresearcher,academic"

    profiles_file = tmp_path / "profiles.txt"
    profiles_file.write_text(content)
    return profiles_file


def change_to_tmp_dir(tmp_path: Path) -> str:
    """Change to temporary directory and return original directory."""
    original_cwd = os.getcwd()
    os.chdir(tmp_path)
    return original_cwd


def restore_directory(original_cwd: str) -> None:
    """Restore to original directory."""
    os.chdir(original_cwd)
