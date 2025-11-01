#!/usr/bin/env python3
"""
Resume Template Substitution Script.

This script takes a LaTeX resume template with placeholders (<1>, <2>, etc.) and substitutes
them with predefined values based on tags. Each placeholder has a default value and can have
tag-specific values. When multiple tags are provided, the first matching tag takes precedence.

Usage
-----
    python substitute_resume.py [--tags TAG1,TAG2,...] [--input INPUT_FILE]
    [--output OUTPUT_FILE] [--config CONFIG_FILE]

Examples
--------
    python substitute_resume.py --tags data_scientist
    python substitute_resume.py --tags ai_engineer,research --input resume.tex
    --output resume_customized.tex
    python substitute_resume.py --tags academic,industry --config my_config.json
"""

import argparse
import json
import logging
import re
import subprocess
import sys
from pathlib import Path

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ResumeSubstituter:
    """Handles the substitution of placeholders in resume templates."""

    def __init__(self, config_file: str = "config.json") -> None:
        """
        Initialize the substituter with a configuration file.

        Parameters
        ----------
        config_file : str, default="config.json"
            Path to the JSON configuration file
        """
        self.config_file = config_file
        self.config = self._load_config()

    def _load_config(self) -> dict[str, dict[str, str]]:
        """Load the configuration from the JSON file."""
        try:
            with Path(self.config_file).open("r", encoding="utf-8") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.exception("Configuration file '%s' not found.", self.config_file)
            sys.exit(1)
        except json.JSONDecodeError:
            logger.exception("Invalid JSON in configuration file")
            sys.exit(1)

    def _get_value_for_placeholder(self, placeholder_id: str, tags: list[str]) -> str:  # noqa: PLR0911
        """
        Get the appropriate value for a placeholder based on tags.

        Parameters
        ----------
        placeholder_id : str
            The ID of the placeholder (e.g., "1", "2")
        tags : list[str]
            List of tags in order of priority

        Returns
        -------
        str
            The value to substitute for the placeholder
        """
        if placeholder_id not in self.config:
            logger.warning("No configuration found for placeholder <%s>", placeholder_id)
            return f"<{placeholder_id}>"

        placeholder_config = self.config[placeholder_id]

        # Handle case where config value is None
        if placeholder_config is None:
            logger.warning("Configuration for placeholder <%s> is null", placeholder_id)
            return f"<{placeholder_id}>"

        # Check tags in order of priority
        for tag in tags:
            if tag in placeholder_config:
                value = placeholder_config[tag]
                # Handle nested objects - convert to string if not already
                if not isinstance(value, str):
                    logger.warning(
                        "Non-string value for placeholder <%s> tag '%s', converting to string",
                        placeholder_id,
                        tag,
                    )
                    return str(value)
                return value

        # Fall back to default value
        if "default" in placeholder_config:
            value = placeholder_config["default"]
            # Handle nested objects - convert to string if not already
            if not isinstance(value, str):
                logger.warning(
                    "Non-string default value for placeholder <%s>, converting to string",
                    placeholder_id,
                )
                return str(value)
            return value

        logger.warning("No default value found for placeholder <%s>", placeholder_id)
        return f"<{placeholder_id}>"

    def map_country_to_tag(self, country: str) -> str:
        """
        Map a country name to an appropriate tag.

        Parameters
        ----------
        country : str
            Country name (case-insensitive)

        Returns
        -------
        str
            Mapped tag name for configuration lookup
        """
        country_lower = country.lower()

        # Direct mappings to existing country tags
        direct_mappings = {
            "uk": "uk",
            "united kingdom": "uk",
            "britain": "uk",
            "great britain": "uk",
            "england": "uk",
            "scotland": "uk",
            "wales": "uk",
            "northern ireland": "uk",
            "usa": "usa",
            "united states": "usa",
            "us": "usa",
            "america": "usa",
            "switzerland": "switzerland",
            "spain": "spain",
        }

        # European countries that should map to 'europe' tag
        european_countries = {
            "germany",
            "france",
            "italy",
            "netherlands",
            "belgium",
            "austria",
            "denmark",
            "sweden",
            "norway",
            "finland",
            "portugal",
            "greece",
            "poland",
            "czech republic",
            "hungary",
            "slovenia",
            "slovakia",
            "estonia",
            "latvia",
            "lithuania",
            "luxembourg",
            "malta",
            "cyprus",
            "ireland",
            "romania",
            "bulgaria",
            "croatia",
        }

        # Check direct mappings first
        if country_lower in direct_mappings:
            return direct_mappings[country_lower]

        # Check if it's a European country
        if country_lower in european_countries:
            return "europe"

        # Default fallback
        return "default"

    def create_folder_structure(
        self, tags: list[str], base_output_file: str, country_original: str = ""
    ) -> str:
        """
        Create folder structure based on tags and return the full output path.

        Pattern: {country}/base_{tags_concatenated_except_country}/{position}

        Parameters
        ----------
        tags : list[str]
            List of tags
        base_output_file : str
            Base output filename
        country_original : str, default=""
            Original country name for folder structure

        Returns
        -------
        str
            Full path including folder structure
        """
        # Define country and position tags
        country_tags = {"uk", "usa", "switzerland", "europe", "spain"}
        position_tags = {
            "engineer",
            "researcher",
            "data_scientist",
            "developer",
            "software_engineer",
            "software_developer",
        }

        # Extract country and position from tags
        country = None
        position = None
        other_tags = []

        for tag in tags:
            if tag in country_tags:
                country = tag
            elif tag in position_tags:
                position = tag
            else:
                other_tags.append(tag)

        # Use defaults if not found
        if not country:
            country = "default"
        if not position:
            position = "general"

        # Create folder structure
        base_name = Path(base_output_file).stem
        extension = Path(base_output_file).suffix

        # Build the path components
        folder_name = f"_base_{'_'.join(other_tags)}" if other_tags else "_base"

        # Use original country name for folder, or fall back to tag-based country
        folder_country = country_original if country_original else country
        folder_path = Path(folder_country) / folder_name / "Position"

        # Create directories if they don't exist
        folder_path.mkdir(parents=True, exist_ok=True)

        # Create the full output path
        output_path = folder_path / f"{base_name}{extension}"

        return str(output_path)

    def substitute_file(self, input_file: str, output_file: str, tags: list[str]) -> None:
        """
        Substitute placeholders in a file and write the result to another file.

        Parameters
        ----------
        input_file : str
            Path to the input file
        output_file : str
            Path to the output file
        tags : list[str]
            List of tags in order of priority
        """
        try:
            with Path(input_file).open("r", encoding="utf-8") as f:
                content = f.read()
        except FileNotFoundError:
            logger.exception("Input file '%s' not found.", input_file)
            sys.exit(1)
        except UnicodeDecodeError:
            logger.exception("Could not read input file '%s' as UTF-8.", input_file)
            sys.exit(1)

        # Find all placeholders in the format <identifier> (alphanumeric)
        placeholders = re.findall(r"<([a-zA-Z0-9_][a-zA-Z0-9_]*)>", content)

        if not placeholders:
            logger.warning("No placeholders found in the input file.")
            # Still write the original content to output file
            Path(output_file).write_text(content, encoding="utf-8")
            logger.info("Output file created: %s", output_file)
            return

        logger.info("Found placeholders: %s", sorted(set(placeholders)))
        if tags:
            logger.info("Using tags (in priority order): %s", ", ".join(tags))
        else:
            logger.info("No tags provided, using default values")

        # Perform substitutions
        substitution_count = 0
        for placeholder_id in set(placeholders):
            value = self._get_value_for_placeholder(placeholder_id, tags)
            pattern = f"<{placeholder_id}>"

            # Count occurrences before substitution
            occurrences = len(re.findall(re.escape(pattern), content))
            content = content.replace(pattern, value)
            substitution_count += occurrences

            if occurrences > 0:
                logger.info("  <%s> -> '%s' (%d occurrences)", placeholder_id, value, occurrences)

        # Write the result
        try:
            with Path(output_file).open("w", encoding="utf-8") as f:
                f.write(content)
            logger.info(
                "Successfully wrote %d substitutions to '%s'", substitution_count, output_file
            )
        except OSError:
            logger.exception("Could not write to output file '%s'", output_file)
            sys.exit(1)

    def list_available_tags(self) -> None:
        """List all available tags from the configuration."""
        all_tags = set()
        for placeholder_config in self.config.values():
            all_tags.update(key for key in placeholder_config if key != "default")

        if all_tags:
            message = "Available tags:"
            logger.info(message)
            for tag in sorted(all_tags):
                tag_message = f"  - {tag}"
                logger.info(tag_message)
        else:
            message = "No tags found in configuration."
            logger.info(message)


def process_resume_substitution(args: argparse.Namespace) -> None:
    """
    Process resume substitution with the given arguments.

    Parameters
    ----------
    args : argparse.Namespace
        Parsed command line arguments from argparse
    """
    # Initialize the substituter
    substituter = ResumeSubstituter(args.config)

    # Handle list-tags option
    if args.list_tags:
        substituter.list_available_tags()
        return

    # Parse tags
    tags = [tag.strip() for tag in args.tags.split(",") if tag.strip()] if args.tags else []

    # Handle country argument
    country_original = ""
    if args.country:
        country_original = args.country
        country_tag = substituter.map_country_to_tag(args.country)
        # Add country tag to the beginning of tags list for priority
        if country_tag != "default":
            tags.insert(0, country_tag)

    # Determine whether to use folder structure
    use_folders = args.use_folders and not args.no_folders

    # Determine output file name
    if args.output:
        output_file = args.output
    else:
        input_path = Path(args.input)
        if tags and use_folders:
            # Use folder structure pattern
            base_output = str(input_path.with_stem(input_path.stem + "_" + "_".join(tags)))
            output_file = substituter.create_folder_structure(tags, base_output, country_original)
        else:
            # Use flat file naming
            tag_suffix = "_" + "_".join(tags) if tags else "_default"
            output_file = str(input_path.with_stem(input_path.stem + tag_suffix))

    # Perform substitution
    substituter.substitute_file(args.input, output_file, tags)

    # Compile to PDF if requested
    if args.compile:
        compile_latex_to_pdf(output_file)


def main() -> None:
    """Handle command line arguments and execute the script."""
    parser = argparse.ArgumentParser(
        description="Substitute placeholders in a resume template based on tags",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    %(prog)s --tags data_scientist
    %(prog)s --tags ai_engineer,research --input resume.tex --output resume_ai.tex
    %(prog)s --list-tags
        """,
    )

    parser.add_argument(
        "--tags",
        "-t",
        type=str,
        help='Comma-separated list of tags in priority order (e.g., "data_scientist,research")',
    )

    parser.add_argument(
        "--input",
        "-i",
        type=str,
        default="resume.tex",
        help="Input LaTeX file (default: resume.tex)",
    )

    parser.add_argument(
        "--output",
        "-o",
        type=str,
        help="Output LaTeX file (default: input file with _[tags] suffix)",
    )

    parser.add_argument(
        "--config",
        "-c",
        type=str,
        default="config.json",
        help="Configuration file (default: config.json)",
    )

    parser.add_argument("--list-tags", action="store_true", help="list available tags and exit")

    parser.add_argument(
        "--use-folders",
        action="store_true",
        default=True,
        help="Use folder structure pattern {country}/_base_{other_tags}/{position} (default: True)",
    )

    parser.add_argument(
        "--no-folders",
        action="store_true",
        help="Disable folder structure, use flat file naming instead",
    )

    parser.add_argument(
        "--country", type=str, help="Country name to use for folder structure and tag mapping"
    )

    parser.add_argument(
        "--compile",
        action="store_true",
        help="Compile the generated LaTeX file to PDF using pdflatex",
    )

    args = parser.parse_args()

    # Call the main processing function with parsed arguments
    process_resume_substitution(args)


def compile_latex_to_pdf(tex_file: str) -> None:
    """
    Compile a LaTeX file to PDF using pdflatex.

    Parameters
    ----------
    tex_file : str
        Path to the LaTeX file to compile
    """
    tex_path = Path(tex_file)

    if not tex_path.exists():
        logger.error("LaTeX file '%s' not found.", tex_file)
        return

    # Change to the directory containing the tex file
    work_dir = tex_path.parent
    tex_filename = tex_path.name

    try:
        logger.info("Compiling %s to PDF...", tex_file)
        result = subprocess.run(  # noqa: S603
            ["pdflatex", "-interaction=nonstopmode", tex_filename],  # noqa: S607
            check=False,
            cwd=work_dir,
            capture_output=True,
            text=True,
            timeout=60,
        )

        pdf_file = tex_path.with_suffix(".pdf")

        if result.returncode == 0 and pdf_file.exists():
            logger.info("Successfully compiled to '%s'", pdf_file)

            # Clean up auxiliary files
            aux_extensions = [".aux", ".log", ".out", ".toc", ".fdb_latexmk", ".fls"]
            for ext in aux_extensions:
                aux_file = tex_path.with_suffix(ext)
                if aux_file.exists():
                    aux_file.unlink()
        else:
            logger.error("Compilation failed with return code %d", result.returncode)
            logger.error("Error output:")
            logger.error(result.stderr)

    except subprocess.TimeoutExpired:
        logger.exception("Compilation timed out after 60 seconds.")
    except FileNotFoundError:
        logger.exception("pdflatex not found. Please install a LaTeX distribution.")
    except Exception:
        logger.exception("Error during compilation")


if __name__ == "__main__":
    main()
