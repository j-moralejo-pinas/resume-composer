"""
Pytest configuration and fixtures for resume-composer tests.

Read more about conftest.py under:
- https://docs.pytest.org/en/stable/fixture.html
- https://docs.pytest.org/en/stable/writing_plugins.html
"""

import json
import shutil
from pathlib import Path

import pytest


@pytest.fixture
def sample_config_data() -> dict[str, dict[str, str]]:
    """Sample configuration data for testing."""
    return {
        "1": {
            "default": "John Doe",
            "academic": "Dr. John Doe",
            "professional": "John Doe, Ph.D.",
            "usa": "John Doe USA",
            "uk": "John Doe UK"
        },
        "2": {
            "default": "Software Engineer",
            "data_scientist": "Data Scientist",
            "researcher": "Research Scientist",
            "academic": "Professor of Computer Science"
        },
        "name": {
            "default": "Jane Smith",
            "academic": "Dr. Jane Smith"
        },
        "title": {
            "default": "Engineer",
            "academic": "Professor",
            "data_scientist": "Data Scientist"
        }
    }


@pytest.fixture
def sample_config_file(tmp_path: Path, sample_config_data: dict[str, dict[str, str]]) -> Path:
    """Create a sample config file for testing."""
    config_file = tmp_path / "config.json"
    config_file.write_text(json.dumps(sample_config_data))
    return config_file


@pytest.fixture
def sample_resume_template(tmp_path: Path) -> Path:
    """Create a sample resume template for testing."""
    template_content = """\\documentclass[11pt]{article}
\\usepackage[margin=1in]{geometry}

\\begin{document}

\\begin{center}
    \\textbf{\\Large <1>}\\\\
    \\vspace{0.1in}
    \\textbf{<2>}\\\\
\\end{center}

\\section*{Summary}
This is a sample resume for <name> with title <title>.

\\end{document}"""
    
    template_file = tmp_path / "resume_template.tex"
    template_file.write_text(template_content)
    return template_file


@pytest.fixture
def sample_profiles_file(tmp_path: Path) -> Path:
    """Create a sample profiles file for testing."""
    profiles_content = """USA,UK,Spain,Switzerland
data_scientist,finance
researcher,academic
engineer,general"""
    
    profiles_file = tmp_path / "profiles.txt"
    profiles_file.write_text(profiles_content)
    return profiles_file


@pytest.fixture
def sample_data_dir(tmp_path: Path) -> Path:
    """Create a complete sample data directory structure."""
    data_dir = tmp_path / "data"
    data_dir.mkdir()
    
    # Copy actual sample files if they exist
    project_root = Path(__file__).parent.parent
    source_data_dir = project_root / "data"
    
    if source_data_dir.exists():
        for file_path in source_data_dir.glob("*"):
            if file_path.is_file():
                shutil.copy(file_path, data_dir)
    
    return data_dir


@pytest.fixture(autouse=True)
def change_test_dir(request: pytest.FixtureRequest, monkeypatch: pytest.MonkeyPatch) -> None:
    """Change to the test directory for each test."""
    if request.node.get_closest_marker("no_chdir"):
        return
    
    # Use tmp_path if available, otherwise use current directory
    if hasattr(request, "getfixturevalue"):
        try:
            tmp_path = request.getfixturevalue("tmp_path")
            monkeypatch.chdir(tmp_path)
        except Exception:
            pass
