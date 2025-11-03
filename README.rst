===============
resume-composer
===============

.. image:: https://img.shields.io/badge/python-3.13+-blue.svg
    :target: https://www.python.org/downloads/
    :alt: Python Version

.. image:: https://img.shields.io/badge/license-MIT-green.svg
    :alt: License

A configurable resume generator that assembles tailored versions of a base resume using predefined customization sets for different roles, companies, or focuses.

Project Description
-------------------

Resume Composer is a powerful tool designed to help job seekers and professionals maintain multiple versions of their resume without the hassle of manual editing. Instead of maintaining separate resume files for different positions, you create one master template with placeholders and let Resume Composer generate tailored versions automatically.

**Key Benefits:**

- **Efficient Management**: Update all resume variants by modifying a single template
- **Time Saving**: No more manual editing of multiple resume files
- **Professional Quality**: Leverage LaTeX's superior typesetting capabilities

Key Features
------------

Resume Customization
~~~~~~~~~~~~~~~~~~~~

- **Template-Based System**: Use LaTeX templates with numbered placeholders (``<1>``, ``<place_holder>``, etc.) that get replaced with tag-specific values
- **Priority System**: Configure tag precedence when multiple tags apply
- **Batch Processing**: Generate multiple resume variants in one command

Flexible Configuration
~~~~~~~~~~~~~~~~~~~~~~

- **JSON Configuration**: Clean, readable configuration format
- **Multi-Dimensional Targeting**: Customize by role (data scientist, researcher), geography (USA, UK), and career stage (academic, industry)

Professional Output
~~~~~~~~~~~~~~~~~~~

- **PDF Generation**: Automatic compilation to publication-ready PDFs
- **Consistent Styling**: Maintain visual consistency across all variants
- **Quality Control**: Built-in validation and error checking

Resume Repository Automation
~~~~~~~~~~~~~~~~~~~~~~~~~~~~

- **GitHub Actions Templates**: Ready-to-use workflow files for your resume repositories
- **Automatic PDF Generation**: Set up CI/CD to build resumes on every template or config update
- **Multi-Profile Publishing**: Generate and publish all resume variants as downloadable artifacts

Quick Start
-----------

1. **Installation**: Clone the repository and install the package:

    .. code-block:: bash

        # OR clone from GitHub
        git clone https://github.com/j-moralejo-pinas/resume-composer.git
        cd resume-composer
        pip install -e .

2. **Create Template**: Modify the template and configuration files in the ``data/`` folder to suit your needs.

3. **Basic Usage**: Create your resume or multiple resumes on batch:

    .. code-block:: bash

        # Generate a single customized resume
        python -m resume_composer.substitute_resume --input "data/sample_resume_template.tex" --config "data/sample_config.json" --output output_folder --tags data_scientist

        # Generate multiple resumes for different profiles
        python -m resume_composer.generate_profiles --input "data/sample_resume_template.tex" --profiles "data/sample_profiles.txt" --config "data/sample_config.json"

4. If multiple tags match a placeholder, the first tag in the command line takes precedence.

Resume Repository Automation
----------------------------

1. **Create a repository**: This repository will contain the template, configuration, and profiles files, and the generated resumes will be built automatically using GitHub Actions.

2. Upload the provided folder ``.github/workflows/`` found inside ``src/repo_automation_workflows/`` to your resume repository to enable automatic resume generation on GitHub Actions.

3. Set a Personal Access Token as a secret in your GitHub repository settings with the name ``PAT_TOKEN``, and read and write content permissions.

4. Upload a LaTeX template (``resume_template.tex``), a configuration file (``config.json``), and a profiles file (``profiles.txt``).

5. On each push to the repository that modifies either the template or the profiles, GitHub Actions will automatically generate the resumes based on your template and configuration, producing tex and PDF files as artifacts, and pushing them to the repo.

📚 Documentation
---------------

- 📦 `Installation Guide <docs/installation.rst>`_ - Setup instructions and requirements
- 🤝 `Contributing Guidelines <CONTRIBUTING.rst>`_ - Development standards and contribution process
- 📄 `License <LICENSE.txt>`_ - License terms and usage rights
- 👥 `Authors <AUTHORS.rst>`_ - Project contributors and maintainers
- 📜 `Changelog <CHANGELOG.rst>`_ - Project history and version changes
- 📜 `Code of Conduct <CODE_OF_CONDUCT.rst>`_ - Guidelines for participation and conduct
