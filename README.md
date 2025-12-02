# Format-Preserving Data Anonymization Framework

A powerful Python tool for anonymizing CSV files while preserving data formats, enabling realistic test data generation, GDPR-compliant pseudonymization, and optional deterministic reversibility.

## Features

- **Format-Preserving Anonymization**: Maintains structure, length, capitalization, and domain models
- **Multiple Anonymization Modes**: 
  - Format-Preserving Fake Data Generator (deterministic)
  - FPE Using AES-FFX (NIST-800-38G style)
  - Seeded HMAC (deterministic hash)
  - Hybrid mode (recommended)
- **Intelligent Data Type Detection**: Automatic detection of emails, phones, names, UUIDs, addresses, etc.
- **Reversible Anonymization**: Encrypted mapping vault for deterministic reversibility
- **Cross-Dataset Integrity**: Maintain referential integrity across multiple files
- **Performance Optimized**: Stream processing and multiprocessing for large datasets

## Installation

```bash
pip install -r requirements.txt
python -m spacy download en_core_web_sm
```

## Quick Start

```bash
python -m anonymizer.cli anonymize --input data.csv --output output/
```

## Usage

See `python -m anonymizer.cli --help` for full documentation.

## Project Structure

```
anonymizer/
├── __init__.py
├── cli.py              # CLI interface
├── core/
│   ├── __init__.py
│   ├── detector.py     # Data type detection
│   ├── transformers.py # Format-preserving transformers
│   └── vault.py        # Mapping vault management
├── utils/
│   ├── __init__.py
│   ├── csv_processor.py
│   └── validators.py
└── config/
    ├── __init__.py
    └── profiles.py     # Anonymization profiles
```

## License

MIT

