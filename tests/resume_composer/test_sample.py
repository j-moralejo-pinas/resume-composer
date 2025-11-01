"""Tests for the resume_composer package."""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from resume_composer.substitute_resume import ResumeSubstituter


def test_sample():
    """Sample test that always passes."""
    assert True