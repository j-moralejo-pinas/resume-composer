#!/usr/bin/env python3
"""
Resume Profile Generator Script.

This script reads a profiles file and generates resumes for all combinations of countries and tag
profiles.

Profile file format:
- First line: comma-separated list of countries
- Following lines: each line contains comma-separated tags for one profile

Example profiles.txt:
USA,UK,Germany,France
data_scientist,finance
researcher,academic
engineer,transportation

This will generate 12 resumes (4 countries x 3 profiles).

Usage
-----
    python generate_profiles.py [--profiles PROFILES_FILE] [--config CONFIG_FILE]
    [--input INPUT_FILE] [--compile]

Examples
--------
    python generate_profiles.py --profiles profiles.txt
    python generate_profiles.py --profiles profiles.txt --compile
    python generate_profiles.py --profiles profiles.txt --config config.json --input resume.tex
"""

import argparse
import logging
import sys
from argparse import Namespace
from pathlib import Path

from resume_composer.substitute_resume import process_resume_substitution

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def read_profiles_file(profiles_file: str) -> tuple[list[str], list[list[str]]]:  # noqa: C901, PLR0912
    """
    Read the profiles file and extract countries and tag profiles.

    Parameters
    ----------
    profiles_file : str
        Path to the profiles file

    Returns
    -------
    tuple[list[str], list[list[str]]]
        Tuple of (countries list, list of tag profiles)
    """
    try:
        with Path(profiles_file).open("r", encoding="utf-8") as f:
            lines = [line.strip() for line in f]
    except FileNotFoundError:
        logger.exception("Profiles file '%s' not found.", profiles_file)
        sys.exit(1)
    except UnicodeDecodeError:
        logger.exception("Could not read profiles file '%s' as UTF-8.", profiles_file)
        sys.exit(1)

    if not lines:
        logger.error("Profiles file is empty.")
        sys.exit(1)

    # Filter out empty lines but keep track of original line numbers
    non_empty_lines = []
    line_mapping = {}  # Maps non-empty line index to original line number
    original_line_num = 1

    for line in lines:
        if line.strip():
            non_empty_lines.append(line)
            line_mapping[len(non_empty_lines) - 1] = original_line_num
        original_line_num += 1

    if not non_empty_lines:
        logger.error("Profiles file contains no non-empty lines.")
        sys.exit(1)

    # First non-empty line contains countries
    countries = [country.strip() for country in non_empty_lines[0].split(",") if country.strip()]

    if not countries:
        logger.error("No countries found in the first line.")
        sys.exit(1)

    # Process remaining lines (both empty and non-empty) for profiles, maintaining warnings
    profiles = []
    first_country_line_num = line_mapping[0]

    for i, line in enumerate(lines[first_country_line_num:], first_country_line_num + 1):
        if not line.strip():  # Empty line
            logger.warning("Empty profile on line %d, skipping.", i)
        else:
            tags = [tag.strip() for tag in line.split(",") if tag.strip()]
            if tags:
                profiles.append(tags)
            else:  # Line has content but no valid tags (e.g., just commas)
                logger.warning("No valid tags on line %d, skipping.", i)

    if not profiles:
        logger.error("No tag profiles found.")
        sys.exit(1)

    return countries, profiles


def generate_resume(
    country: str, tags: list[str], config: str, input_file: str, *, compile_pdf: bool
) -> None:
    """
    Generate a single resume for a country and tag combination.

    Parameters
    ----------
    country : str
        Country name
    tags : list[str]
        List of tags for this profile
    config : str
        Path to configuration file
    input_file : str
        Path to input LaTeX file
    compile_pdf : bool
        Whether to compile to PDF
    """
    # Create arguments object similar to argparse output
    args = Namespace(
        tags=",".join(tags),
        country=country,
        config=config,
        input=input_file,
        compile=compile_pdf,
        output=None,  # Let the function determine the output file
        list_tags=False,
        use_folders=True,
        no_folders=False,
    )

    # Call the substitution function directly
    try:
        logger.info("Generating resume for %s with tags: %s", country, ", ".join(tags))
        process_resume_substitution(args)
        logger.info("  ✓ Success")
    except Exception:
        logger.exception("  ✗ Error")


def main() -> None:
    """Handle command line arguments and execute profile generation."""
    parser = argparse.ArgumentParser(
        description="Generate resumes for all combinations of countries and tag profiles",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Profile file format:
    First line: comma-separated countries (e.g., "USA,UK,Germany,France")
    Following lines: comma-separated tags for each profile

Example profiles.txt:
    USA,UK,Germany,France
    data_scientist,finance
    researcher,academic
    engineer,transportation

Examples:
    %(prog)s --profiles profiles.txt
    %(prog)s --profiles profiles.txt --compile
    %(prog)s --profiles profiles.txt --config config.json
        """,
    )

    parser.add_argument(
        "--profiles",
        "-p",
        type=str,
        default="profiles.txt",
        help="Profiles file containing countries and tag combinations (default: profiles.txt)",
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config.json",
        help="Configuration file (default: config.json)",
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="resume.tex",
        help="Input LaTeX file (default: resume.tex)",
    )

    parser.add_argument(
        "--compile", action="store_true", help="Compile generated LaTeX files to PDF"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be generated without actually generating files",
    )

    args = parser.parse_args()

    # Read the profiles file
    countries, profiles = read_profiles_file(args.profiles)

    logger.info("Found %d countries: %s", len(countries), ", ".join(countries))
    logger.info("Found %d profiles:", len(profiles))
    for i, profile in enumerate(profiles, 1):
        logger.info("  %d. %s", i, ", ".join(profile))

    total_combinations = len(countries) * len(profiles)
    logger.info("Will generate %d resumes", total_combinations)

    if args.dry_run:
        logger.info("Dry run - showing combinations that would be generated:")
        for country in countries:
            for profile in profiles:
                logger.info("  %s: %s", country, ", ".join(profile))
        return

    # Check if required files exist
    if not Path(args.config).exists():
        logger.error("Configuration file '%s' not found.", args.config)
        sys.exit(1)

    if not Path(args.input).exists():
        logger.error("Input file '%s' not found.", args.input)
        sys.exit(1)

    # Generate all combinations
    logger.info("Generating resumes...")
    success_count = 0

    for country in countries:
        for profile in profiles:
            generate_resume(country, profile, args.config, args.input, compile_pdf=args.compile)
            success_count += 1

    logger.info("Completed processing %d/%d combinations", success_count, total_combinations)


if __name__ == "__main__":
    main()
