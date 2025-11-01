#!/usr/bin/env python3
"""
Resume Profile Generator Script

This script reads a profiles file and generates resumes for all combinations of countries and tag profiles.

Profile file format:
- First line: comma-separated list of countries
- Following lines: each line contains comma-separated tags for one profile

Example profiles.txt:
USA,UK,Germany,France
data_scientist,finance
researcher,academic
engineer,transportation

This will generate 12 resumes (4 countries × 3 profiles).

Usage:
    python generate_profiles.py [--profiles PROFILES_FILE] [--config CONFIG_FILE] [--input INPUT_FILE] [--compile]

Examples:
    python generate_profiles.py --profiles profiles.txt
    python generate_profiles.py --profiles profiles.txt --compile
    python generate_profiles.py --profiles profiles.txt --config config_named.json --input resume.tex
"""

import argparse
import sys
from pathlib import Path
from typing import List, Tuple
import subprocess


def read_profiles_file(profiles_file: str) -> Tuple[List[str], List[List[str]]]:
    """
    Read the profiles file and extract countries and tag profiles.

    Args:
        profiles_file: Path to the profiles file

    Returns:
        Tuple of (countries list, list of tag profiles)
    """
    try:
        with open(profiles_file, "r", encoding="utf-8") as f:
            lines = [line.strip() for line in f.readlines() if line.strip()]
    except FileNotFoundError:
        print(f"Error: Profiles file '{profiles_file}' not found.")
        sys.exit(1)
    except UnicodeDecodeError:
        print(f"Error: Could not read profiles file '{profiles_file}' as UTF-8.")
        sys.exit(1)

    if not lines:
        print("Error: Profiles file is empty.")
        sys.exit(1)

    # First line contains countries
    countries = [country.strip() for country in lines[0].split(",") if country.strip()]

    if not countries:
        print("Error: No countries found in the first line.")
        sys.exit(1)

    # Remaining lines contain tag profiles
    profiles = []
    for i, line in enumerate(lines[1:], 2):
        tags = [tag.strip() for tag in line.split(",") if tag.strip()]
        if tags:
            profiles.append(tags)
        else:
            print(f"Warning: Empty profile on line {i}, skipping.")

    if not profiles:
        print("Error: No tag profiles found.")
        sys.exit(1)

    return countries, profiles


def generate_resume(
    country: str, tags: List[str], config: str, input_file: str, compile_pdf: bool
) -> None:
    """
    Generate a single resume for a country and tag combination.

    Args:
        country: Country name
        tags: List of tags for this profile
        config: Path to configuration file
        input_file: Path to input LaTeX file
        compile_pdf: Whether to compile to PDF
    """
    # Build the command
    cmd = [
        "python3",
        "substitute_resume.py",
        "--config",
        config,
        "--country",
        country,
        "--tags",
        ",".join(tags),
    ]

    if input_file != "resume.tex":
        cmd.extend(["--input", input_file])

    if compile_pdf:
        cmd.append("--compile")

    # Execute the command
    try:
        print(f"Generating resume for {country} with tags: {', '.join(tags)}")
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)

        if result.returncode == 0:
            print(f"  ✓ Success")
        else:
            print(f"  ✗ Failed with return code {result.returncode}")
            if result.stderr:
                print(f"  Error: {result.stderr.strip()}")

    except subprocess.TimeoutExpired:
        print(f"  ✗ Timeout after 120 seconds")
    except Exception as e:
        print(f"  ✗ Error: {e}")


def main():
    """Main function to handle command line arguments and execute profile generation."""
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
  %(prog)s --profiles profiles.txt --config config_named.json
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
        default="config_named.json",
        help="Configuration file (default: config_named.json)",
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

    print(f"Found {len(countries)} countries: {', '.join(countries)}")
    print(f"Found {len(profiles)} profiles:")
    for i, profile in enumerate(profiles, 1):
        print(f"  {i}. {', '.join(profile)}")

    total_combinations = len(countries) * len(profiles)
    print(f"\nWill generate {total_combinations} resumes")

    if args.dry_run:
        print("\nDry run - showing combinations that would be generated:")
        for country in countries:
            for profile in profiles:
                print(f"  {country}: {', '.join(profile)}")
        return

    # Check if required files exist
    if not Path(args.config).exists():
        print(f"Error: Configuration file '{args.config}' not found.")
        sys.exit(1)

    if not Path(args.input).exists():
        print(f"Error: Input file '{args.input}' not found.")
        sys.exit(1)

    if not Path("substitute_resume.py").exists():
        print("Error: substitute_resume.py not found in current directory.")
        sys.exit(1)

    # Generate all combinations
    print(f"\nGenerating resumes...")
    success_count = 0

    for country in countries:
        for profile in profiles:
            generate_resume(country, profile, args.config, args.input, args.compile)
            success_count += 1

    print(f"\nCompleted processing {success_count}/{total_combinations} combinations")


if __name__ == "__main__":
    main()
