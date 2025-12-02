"""
Setup script for Format-Preserving Data Anonymization Framework
"""

from setuptools import setup, find_packages
from pathlib import Path

# Read README
readme_file = Path(__file__).parent / "README.md"
long_description = readme_file.read_text() if readme_file.exists() else ""

setup(
    name="format-preserving-anonymizer",
    version="1.0.0",
    description="Format-Preserving Data Anonymization Framework",
    long_description=long_description,
    long_description_content_type="text/markdown",
    author="Your Name",
    author_email="your.email@example.com",
    url="https://github.com/yourusername/anonymizer",
    packages=find_packages(),
    install_requires=[
        "pandas>=2.0.0",
        "polars>=0.19.0",
        "cryptography>=41.0.0",
        "faker>=19.0.0",
        "python-dateutil>=2.8.0",
        "regex>=2023.0.0",
        "presidio-analyzer>=2.2.0",
        "presidio-anonymizer>=2.2.0",
        "rich>=13.0.0",
        "click>=8.1.0",
        "python-dotenv>=1.0.0",
        "tqdm>=4.66.0",
    ],
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=23.0.0",
            "flake8>=6.0.0",
        ],
        "spacy": [
            "spacy>=3.7.0",
        ],
        "sqlcipher": [
            "pysqlcipher3>=1.1.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "anonymize=anonymizer.cli:cli",
        ],
    },
    python_requires=">=3.8",
    classifiers=[
        "Development Status :: 4 - Beta",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Topic :: Security",
        "Topic :: Software Development :: Libraries :: Python Modules",
    ],
)

